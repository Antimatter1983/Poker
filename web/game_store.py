"""In-memory tournament registry used by the Django views.

The poker engine is stateful Python code, so this store keeps live Tournament
objects for a lightweight local server. Restarting the Django process resets
open tournaments.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from contextlib import nullcontext
from threading import RLock
from time import monotonic

from django.conf import settings
from django.db import transaction
from secrets import token_hex

from poker.hand_engine import BET, CALL, CHECK, FOLD, RAISE, ALL_IN, HandEngine
from poker.tournament import HAND_COUNT, Tournament

WAITING = "waiting"
RUNNING = "running"
FINISHED = "finished"

HAND_PLAYING = "PLAYING"
HAND_WAITING = "WAITING"
HAND_REVEAL = "REVEAL"
REVEAL_SECONDS = 10
HAND_RESULT_PAUSE_SECONDS = REVEAL_SECONDS


def _safe_atomic():
    if settings.configured:
        return transaction.atomic()
    return nullcontext()


@dataclass
class LobbyTournament:
    code: str
    title: str
    admin_name: str
    hand_count: int = HAND_COUNT
    player_names: list[str] = field(default_factory=list)
    status: str = WAITING
    game: Tournament | None = None
    finished_hand_at: float | None = None
    next_hand_actor_name: str | None = None
    hand_state: str = HAND_PLAYING
    reveal_started_at: float | None = None
    reveal_until: float | None = None
    next_hand_by_completed_hand: dict[int, int] = field(default_factory=dict)
    _advance_lock: RLock = field(default_factory=RLock, init=False, repr=False)

    def add_player(self, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValueError("Введите имя игрока")
        if self.status != WAITING:
            raise ValueError("Регистрация закрыта: турнир уже начался")
        if name in self.player_names:
            raise ValueError("Игрок с таким именем уже зарегистрирован")
        self.player_names.append(name)

    def start(self) -> None:
        if self.status != WAITING:
            return
        if not self.player_names:
            raise ValueError("Добавьте хотя бы одного игрока")
        self.game = Tournament.create_by_admin(
            self.admin_name,
            self.code,
            self.player_names,
            hand_count=self.hand_count,
        )
        self.status = RUNNING
        self.finished_hand_at = None
        self.next_hand_actor_name = None
        self.game.start_next_hand()
        self.hand_state = HAND_PLAYING

    def finish(self) -> None:
        if self.status == WAITING:
            raise ValueError("Турнир ещё не начался")
        self.status = FINISHED

    def table_for(self, player_name: str):
        if self.game is None:
            return None
        return next((table for table in self.game.tables if table.player.player_id == player_name), None)

    def advance_finished_hands(self, force: bool = False) -> None:
        if self.game is None or self.status != RUNNING:
            return
        self.game.process_timeouts()
        if not self.all_hands_finished():
            self.finished_hand_at = None
            self.next_hand_actor_name = None
            return
        if self.finished_hand_at is None:
            self.finished_hand_at = monotonic()
            self.next_hand_actor_name = self._latest_finished_player_name()
        if force:
            self.complete_current_hand_and_maybe_start_next()

    def complete_current_hand_and_maybe_start_next(self) -> None:
        """Start the next shared hand once, after every current table is finished."""
        if self.game is None or self.status != RUNNING or not self.all_hands_finished():
            return
        completed_hand_number = self.game.hand_number
        with _safe_atomic():
            with self._advance_lock:
                if self.game is None or self.status != RUNNING:
                    return
                if self.game.hand_number != completed_hand_number or not self.all_hands_finished():
                    return
                if self.finished_hand_at is None:
                    self.finished_hand_at = monotonic()
                    self.next_hand_actor_name = self._latest_finished_player_name()
                if self.game.hand_number >= self.game.hand_count:
                    self.status = FINISHED
                    return
                self._start_next_hand_locked(completed_hand_number)

    def mark_waiting_or_reveal(self) -> None:
        if self.game is None or self.status != RUNNING:
            return
        if self.all_hands_finished():
            self.start_reveal()
        elif any(table.engine.finished for table in self.game.tables):
            self.hand_state = HAND_WAITING

    def start_reveal(self) -> None:
        if self.game is None or self.status != RUNNING or not self.all_hands_finished():
            return
        with _safe_atomic():
            with self._advance_lock:
                if self.game is None or self.status != RUNNING or not self.all_hands_finished():
                    return
                if self.hand_state != HAND_REVEAL:
                    self.hand_state = HAND_REVEAL
                    self.reveal_started_at = monotonic()
                    self.reveal_until = self.reveal_started_at + REVEAL_SECONDS
                    self.finished_hand_at = self.reveal_started_at
                    self.next_hand_actor_name = self._latest_finished_player_name()

    def reveal_seconds_left(self) -> int:
        if self.reveal_until is None:
            return REVEAL_SECONDS
        return max(0, int(self.reveal_until - monotonic() + 0.999))

    def get_or_create_next_hand_after_reveal(self, completed_hand_number: int) -> int | None:
        if self.game is None:
            return None
        with _safe_atomic():
            with self._advance_lock:
                if self.game is None:
                    return None
                existing = self.next_hand_by_completed_hand.get(completed_hand_number)
                if existing:
                    return existing
                if self.game.hand_number > completed_hand_number:
                    self.next_hand_by_completed_hand[completed_hand_number] = self.game.hand_number
                    return self.game.hand_number
                if self.status != RUNNING or self.hand_state != HAND_REVEAL or self.reveal_seconds_left() > 0:
                    return None
                if self.game.hand_number >= self.game.hand_count:
                    self.status = FINISHED
                    return None
                return self._start_next_hand_locked(completed_hand_number)

    def _start_next_hand_locked(self, completed_hand_number: int) -> int:
        existing = self.next_hand_by_completed_hand.get(completed_hand_number)
        if existing:
            return existing
        self.finished_hand_at = None
        self.next_hand_actor_name = None
        self.reveal_started_at = None
        self.reveal_until = None
        self.hand_state = HAND_PLAYING
        self.game.start_next_hand()
        self.next_hand_by_completed_hand[completed_hand_number] = self.game.hand_number
        return self.game.hand_number

    def all_hands_finished(self) -> bool:
        return bool(self.game and self.game.tables and all(table.engine.finished for table in self.game.tables))

    def player_can_advance_hand(self, player_name: str | None) -> bool:
        return bool(player_name and self.can_advance_hand() and player_name == self.next_hand_actor_name)

    def _latest_finished_player_name(self) -> str | None:
        if self.game is None:
            return None
        latest_table = max(
            self.game.tables,
            key=lambda table: table.engine.finished_at or 0,
            default=None,
        )
        return latest_table.player.player_id if latest_table else None

    def seconds_until_next_hand_ready(self) -> int:
        if not self.all_hands_finished():
            return HAND_RESULT_PAUSE_SECONDS
        if self.finished_hand_at is None:
            self.finished_hand_at = monotonic()
            return HAND_RESULT_PAUSE_SECONDS
        elapsed = monotonic() - self.finished_hand_at
        return max(0, int(HAND_RESULT_PAUSE_SECONDS - elapsed + 0.999))

    def can_advance_hand(self) -> bool:
        return self.status == RUNNING and self.game is not None and self.all_hands_finished()

    def finished_player_count(self, hand_number: int | None = None) -> int:
        if self.game is None or hand_number is None:
            return len(self.player_names)
        if hand_number != self.game.hand_number:
            return len(self.player_names)
        return sum(1 for table in self.game.tables if table.engine.finished)

    def next_hand_ready(self, completed_hand_number: int) -> bool:
        return bool(self.game and self.game.hand_number > completed_hand_number) or self.status == FINISHED

    def unfinished_player_names(self) -> list[str]:
        if self.game is None:
            return []
        return [table.player.player_id for table in self.game.tables if not table.engine.finished]

    def standings(self) -> list[tuple[str, int]]:
        if self.game is None:
            return [(name, 1000) for name in self.player_names]
        return self.game.standings()

    def race_standings(self) -> list[dict[str, int | str]]:
        standings = self.standings()
        if not standings:
            return []
        stacks = [stack for _, stack in standings]
        min_stack = min(stacks)
        max_stack = max(stacks)
        spread = max(max_stack - min_stack, 1)
        return [
            {
                "name": name,
                "stack": stack,
                "position": 8 + round(((stack - min_stack) / spread) * 84),
            }
            for name, stack in standings
        ]


TOURNAMENTS: dict[str, LobbyTournament] = {}


def create(title: str, admin_name: str, hand_count: int = HAND_COUNT) -> LobbyTournament:
    code = token_hex(3)
    while code in TOURNAMENTS:
        code = token_hex(3)
    lobby = LobbyTournament(code=code, title=title.strip() or "Poker Tournament", admin_name=admin_name.strip() or "admin", hand_count=hand_count)
    TOURNAMENTS[code] = lobby
    return lobby


def get(code: str) -> LobbyTournament:
    try:
        return TOURNAMENTS[code]
    except KeyError as exc:
        raise ValueError("Турнир не найден") from exc


def card_text(cards) -> str:
    return " ".join(str(card) for card in cards) or "—"


def card_view(cards) -> list[dict[str, str | bool]]:
    suit_symbols = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
    red_suits = {"H", "D"}
    rank_labels = {"T": "10"}
    return [
        {"rank": rank_labels.get(card.rank, card.rank), "suit": suit_symbols[card.suit], "red": card.suit in red_suits}
        for card in cards
    ]


def hand_result(engine: HandEngine | None, player_id: str | None = None) -> dict[str, str | bool | int] | None:
    if engine is None or player_id is None or not engine.finished or not engine.winners:
        return None
    player = next((candidate for candidate in engine.players if candidate.player_id == player_id), None)
    bot = next((candidate for candidate in engine.players if candidate.player_id != player_id), None)
    if player is None or bot is None:
        return None

    player_won = any(winner.player_id == player_id for winner in engine.winners)
    split = len(engine.winners) > 1
    start_stack = engine.starting_stacks.get(player_id, player.stack)
    net = player.stack - start_stack
    amount = abs(net)
    player_value = engine.hand_values.get(player.player_id)
    bot_value = engine.hand_values.get(bot.player_id)
    player_hand = player_value.name if player_value else "fold"
    bot_hand = bot_value.name if bot_value else "fold"

    player_label = player.player_id
    if split:
        verdict = "Ничья"
        summary = f"{player_label} вернул(а) {amount} с {player_hand} против {bot_hand}"
    elif player_won:
        verdict = f"{player_label} выиграл(а)"
        summary = f"{player_label} выиграл(а) {amount} с {player_hand} против {bot_hand}"
    else:
        verdict = f"{player_label} проиграл(а)"
        summary = f"{player_label} проиграл(а) {amount} с {player_hand} против {bot_hand}"

    return {
        "player_won": player_won,
        "split": split,
        "verdict": verdict,
        "amount": amount,
        "player_hand": player_hand,
        "bot_hand": bot_hand,
        "summary": summary,
    }


def betting_buttons(engine: HandEngine | None, player) -> list[dict[str, int | str]]:
    if engine is None or player is None:
        return []
    legal = engine.legal_actions(player)
    action = BET if BET in legal else RAISE if RAISE in legal else None
    maximum = engine.max_bet_or_raise_to(player) if action else None
    if action is None or maximum is None:
        return []
    minimum = engine.big_blind if action == BET else engine.current_bet + engine.min_raise
    half_pot = player.street_bet + engine.to_call(player) + engine.pot // 2
    medium = min(maximum, max(minimum, half_pot))
    labels = [("Мин 2ББ", minimum), ("1/2 пота", medium), ("Пот", maximum)]
    return [{"label": label, "action": action, "amount": amount} for label, amount in labels]


def legal_action_options(engine: HandEngine) -> list[tuple[str, str]]:
    labels = {FOLD: "Fold", CHECK: "Check", CALL: "Call", BET: "Bet", RAISE: "Raise", ALL_IN: "All-in"}
    return [(action, labels[action]) for action in engine.legal_actions()]


def current_hand_summary(cards) -> str:
    cards = list(cards)
    if len(cards) < 2:
        return "—"
    from itertools import combinations
    from poker.hand_evaluator import HAND_NAMES, _evaluate_five
    if len(cards) >= 5:
        value = max((_evaluate_five(tuple(combo)) for combo in combinations(cards, 5)), key=lambda h: h._key())
        return value.name
    counts = {}
    for card in cards:
        counts[card.value] = counts.get(card.value, 0) + 1
    if 4 in counts.values():
        return HAND_NAMES[8]
    if 3 in counts.values():
        return HAND_NAMES[4]
    pairs = sum(1 for count in counts.values() if count == 2)
    if pairs >= 2:
        return HAND_NAMES[3]
    if pairs == 1:
        return HAND_NAMES[2]
    return HAND_NAMES[1]


def _signed_amount(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)


def hand_results(lobby: LobbyTournament) -> list[dict]:
    if lobby.game is None:
        return []
    rows = []
    for table in lobby.game.tables:
        engine = table.engine
        player = table.player
        bot = table.bot
        result = hand_result(engine, player.player_id)
        player_value = engine.hand_values.get(player.player_id)
        bot_value = engine.hand_values.get(bot.player_id)
        player_net = player.stack - engine.starting_stacks.get(player.player_id, player.stack)
        bot_net = -player_net
        bot_won = bool(result and not result["split"] and not result["player_won"])
        rows.append({
            "player_name": player.player_id,
            "player_cards": card_view(player.cards),
            "bot_cards": card_view(bot.cards),
            "board": card_view(engine.community_cards),
            "player_best_cards": card_view(player_value.best_five) if player_value else [],
            "bot_best_cards": card_view(bot_value.best_five) if bot_value else [],
            "player_hand": player_value.name if player_value else (result or {}).get("player_hand", "fold"),
            "bot_hand": bot_value.name if bot_value else (result or {}).get("bot_hand", "fold"),
            "winner": "Ничья" if result and result["split"] else player.player_id if result and result["player_won"] else "Бот",
            "bot_verdict": "Ничья" if result and result["split"] else "Бот победил" if bot_won else "Бот проиграл",
            "net": player_net,
            "player_net_label": _signed_amount(player_net),
            "bot_net_label": _signed_amount(bot_net),
            "result": result,
        })
    return sorted(rows, key=lambda row: row["net"], reverse=True)
