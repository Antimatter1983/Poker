"""In-memory tournament registry used by the Django views.

The poker engine is stateful Python code, so this store keeps live Tournament
objects for a lightweight local server. Restarting the Django process resets
open tournaments.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from secrets import token_hex

from poker.hand_engine import BET, CALL, CHECK, FOLD, RAISE, ALL_IN, HandEngine
from poker.tournament import HAND_COUNT, Tournament

WAITING = "waiting"
RUNNING = "running"
FINISHED = "finished"


@dataclass
class LobbyTournament:
    code: str
    title: str
    admin_name: str
    hand_count: int = HAND_COUNT
    player_names: list[str] = field(default_factory=list)
    status: str = WAITING
    game: Tournament | None = None

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
        self.game.start_next_hand()

    def table_for(self, player_name: str):
        if self.game is None:
            return None
        return next((table for table in self.game.tables if table.player.player_id == player_name), None)

    def advance_finished_hands(self) -> None:
        if self.game is None or self.status != RUNNING:
            return
        while all(table.engine.finished for table in self.game.tables):
            if self.game.hand_number >= self.game.hand_count:
                self.status = FINISHED
                return
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


def legal_action_options(engine: HandEngine) -> list[tuple[str, str]]:
    labels = {FOLD: "Fold", CHECK: "Check", CALL: "Call", BET: "Bet", RAISE: "Raise", ALL_IN: "All-in"}
    return [(action, labels[action]) for action in engine.legal_actions()]
