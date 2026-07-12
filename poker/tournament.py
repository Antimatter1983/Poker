"""Synchronous Texas Hold'em Heads-Up training tournaments."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic

from .bot import CallBot
from .deck import Deck
from .hand_engine import HandEngine
from .player import Player

STARTING_STACK = 1000
HAND_COUNT = 100
ACTION_TIMEOUT_SECONDS = 10
BOT_STACK = 10**12


@dataclass
class TournamentTable:
    player: Player
    bot: Player
    engine: HandEngine


@dataclass
class Tournament:
    """Tournament with identical deals and synchronized streets across tables."""

    tournament_id: str
    player_ids: list[str]
    small_blind: int = 5
    big_blind: int = 10
    hand_count: int = HAND_COUNT
    action_timeout_seconds: int = ACTION_TIMEOUT_SECONDS
    bot_policy: CallBot = field(default_factory=CallBot)
    hand_number: int = 0
    tables: list[TournamentTable] = field(default_factory=list)
    action_deadline: float | None = None

    def __post_init__(self) -> None:
        if not self.player_ids:
            raise ValueError("Tournament requires at least one player")
        if len(set(self.player_ids)) != len(self.player_ids):
            raise ValueError("Tournament player ids must be unique")
        self.tables = [self._new_table(player_id) for player_id in self.player_ids]

    @classmethod
    def create_by_admin(cls, admin_id: str, tournament_id: str, player_ids: list[str], **kwargs) -> "Tournament":
        if not admin_id:
            raise ValueError("Only an authenticated administrator can create tournaments")
        return cls(tournament_id=tournament_id, player_ids=player_ids, **kwargs)

    def start_next_hand(self) -> None:
        if self.hand_number >= self.hand_count:
            raise ValueError("Tournament is already complete")
        deck = Deck(); deck.shuffle(); shared_cards = list(deck.cards)
        self.hand_number += 1
        for table in self.tables:
            button_id = table.player.player_id
            table.engine = HandEngine(table.player, table.bot, button_id, self.small_blind, self.big_blind)
            table.engine.start_hand(deck_cards=shared_cards)
        self._run_ready_bots()
        self.action_deadline = monotonic() + self.action_timeout_seconds

    def submit_player_action(self, player_id: str, action: str, amount: int | None = None) -> None:
        table = self._table_for(player_id)
        if table.engine.finished:
            raise ValueError("This table hand is already finished")
        if table.engine.current_player is not table.player:
            raise ValueError("It is not this player's turn")
        table.engine.act(action, amount)
        self._run_ready_bots()
        if self.all_tables_waiting_at_barrier():
            self.action_deadline = monotonic() + self.action_timeout_seconds

    def all_tables_waiting_at_barrier(self) -> bool:
        streets = {table.engine.street for table in self.tables}
        return len(streets) == 1 and all(
            table.engine.finished or table.engine.current_player is table.player for table in self.tables
        )

    def standings(self) -> list[tuple[str, int]]:
        return sorted(((table.player.player_id, table.player.stack) for table in self.tables), key=lambda item: item[1], reverse=True)

    def winner_ids(self) -> list[str]:
        if self.hand_number < self.hand_count:
            raise ValueError("Tournament is not complete")
        standings = self.standings()
        best_stack = standings[0][1]
        return [player_id for player_id, stack in standings if stack == best_stack]

    def _run_ready_bots(self) -> None:
        for table in self.tables:
            while not table.engine.finished and table.engine.current_player is table.bot:
                action, amount = self.bot_policy.choose_action(table.engine, table.bot)
                table.engine.act(action, amount)

    def _new_table(self, player_id: str) -> TournamentTable:
        player = Player(player_id, STARTING_STACK)
        bot = Player(f"bot:{player_id}", BOT_STACK)
        engine = HandEngine(player, bot, player.player_id, self.small_blind, self.big_blind)
        return TournamentTable(player=player, bot=bot, engine=engine)

    def _table_for(self, player_id: str) -> TournamentTable:
        for table in self.tables:
            if table.player.player_id == player_id:
                return table
        raise ValueError(f"Unknown tournament player: {player_id}")
