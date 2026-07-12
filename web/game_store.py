"""In-memory tournament registry used by the Django views.

The poker engine is stateful Python code, so this store keeps live Tournament
objects for a lightweight local server. Restarting the Django process resets
open tournaments.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from secrets import token_hex

from poker.hand_engine import BET, CALL, CHECK, FOLD, RAISE, ALL_IN, HandEngine
from poker.tournament import HAND_COUNT, Tournament

WAITING = "waiting"
RUNNING = "running"
FINISHED = "finished"
HAND_RESULT_PAUSE_SECONDS = 6


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
        self.game.start_next_hand()

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
        if not all(table.engine.finished for table in self.game.tables):
            self.finished_hand_at = None
            return
        if self.finished_hand_at is None:
            self.finished_hand_at = monotonic()
            return
        if not force and monotonic() - self.finished_hand_at < HAND_RESULT_PAUSE_SECONDS:
            return
        if self.game.hand_number >= self.game.hand_count:
            self.status = FINISHED
            return
        self.finished_hand_at = None
        self.game.start_next_hand()

    def standings(self) -> list[tuple[str, int]]:
        if self.game is None:
            return [(name, 1000) for name in self.player_names]
        return self.game.standings()


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
    return [
        {"rank": card.rank, "suit": suit_symbols[card.suit], "red": card.suit in red_suits}
        for card in cards
    ]


def hand_result(engine: HandEngine | None) -> dict[str, str] | None:
    if engine is None or not engine.finished or not engine.winners:
        return None
    winners = ", ".join(winner.player_id.replace("bot:", "Call Bot для ") for winner in engine.winners)
    if engine.finish_reason == "fold":
        return {"winner": winners, "hand": "победа после fold", "gain": "банк раздачи"}
    values = [engine.hand_values.get(winner.player_id) for winner in engine.winners]
    hand = ", ".join(value.name for value in values if value)
    return {"winner": winners, "hand": hand or "лучшая рука", "gain": "банк раздачи"}


def betting_buttons(engine: HandEngine | None, player) -> list[dict[str, int | str]]:
    if engine is None or player is None:
        return []
    legal = engine.legal_actions(player)
    action = BET if BET in legal else RAISE if RAISE in legal else None
    maximum = engine.max_bet_or_raise_to(player) if action else None
    if action is None or maximum is None:
        return []
    minimum = engine.big_blind if action == BET else engine.current_bet + engine.min_raise
    medium = minimum + (maximum - minimum) // 2
    labels = [("Минимум", minimum), ("Средний", medium), ("Максимум", maximum)]
    return [{"label": label, "action": action, "amount": amount} for label, amount in labels]


def legal_action_options(engine: HandEngine) -> list[tuple[str, str]]:
    labels = {FOLD: "Fold", CHECK: "Check", CALL: "Call", BET: "Bet", RAISE: "Raise", ALL_IN: "All-in"}
    return [(action, labels[action]) for action in engine.legal_actions()]
