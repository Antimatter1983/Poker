"""External contract for a single Texas Hold'em Heads-Up hand engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class PlayerAction(Enum):
    """Actions that a player can request."""

    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    BET = auto()
    RAISE = auto()
    ALL_IN = auto()


class EngineStatus(Enum):
    """Current high-level engine status."""

    WAITING_FOR_ACTION = auto()
    HAND_FINISHED = auto()


class Street(Enum):
    """Current street of a hand."""

    PREFLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()
    SHOWDOWN = auto()
    FINISHED = auto()


class FinishReason(Enum):
    """Reason why a hand finished."""

    FOLD = auto()
    SHOWDOWN = auto()


@dataclass
class HandSetup:
    """Initial data for one concrete hand."""

    player1_id: str
    player2_id: str
    player1_stack: int
    player2_stack: int
    small_blind_player_id: str
    big_blind_player_id: str
    small_blind: int
    big_blind: int


@dataclass
class ActionRequest:
    """A requested player action."""

    player_id: str
    action: PlayerAction
    amount: int | None = None


@dataclass
class PlayerState:
    """Full public snapshot of a player's state."""

    player_id: str
    starting_stack: int
    stack: int
    cards: list[Any]
    street_bet: int
    total_bet: int
    folded: bool
    all_in: bool
    last_action: PlayerAction | None
    is_small_blind: bool
    is_big_blind: bool
    is_button: bool


@dataclass
class EngineResponse:
    """Unified public response from the hand engine."""

    status: EngineStatus
    street: Street
    acting_player_id: str | None
    available_actions: list[PlayerAction]
    call_amount: int
    minimum_bet: int | None
    minimum_raise_to: int | None
    pot: int
    current_bet: int
    board: list[Any]
    players: list[PlayerState]
    winner_ids: list[str]
    finish_reason: FinishReason | None
