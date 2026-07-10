"""Player action models and helpers for betting decisions."""

from dataclasses import dataclass
from enum import Enum, auto

from poker.player import Player
from poker.table import Table


class PlayerAction(Enum):
    """Actions a player can choose during a betting street."""

    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    BET = auto()
    RAISE = auto()
    ALL_IN = auto()


class ActionError(ValueError):
    """Base class for invalid player action requests."""


class PlayerNotFoundError(ActionError):
    """Raised when an action references a player outside the table."""


class ActionNotAvailableError(ActionError):
    """Raised when an action is not currently available to the player."""


class MissingAmountError(ActionError):
    """Raised when an action requires an amount but none was supplied."""


class NonPositiveAmountError(ActionError):
    """Raised when a supplied action amount is zero or negative."""


class StackExceededError(ActionError):
    """Raised when a bet or raise requires more chips than the player has."""


class InvalidRaiseError(ActionError):
    """Raised when a raise does not produce a valid larger full bet."""


@dataclass(frozen=True, slots=True)
class ActionRequest:
    """A requested action from a player."""

    player_id: str
    action: PlayerAction
    amount: int | None = None


@dataclass(frozen=True, slots=True)
class ActionResult:
    """Resulting table and player state after applying an action."""

    player_id: str
    action: PlayerAction
    amount_paid: int
    player_stack: int
    player_current_bet: int
    table_current_bet: int
    pot: int


def available_actions(player: Player, table: Table) -> set[PlayerAction]:
    """Return actions available to a player in the current table state.

    This helper intentionally models only basic action availability. It does not
    enforce minimum raise sizing, action order, street completion, or side pots.
    """

    if player.folded or player.all_in:
        return set()

    if player.current_bet < table.current_bet:
        return {
            PlayerAction.FOLD,
            PlayerAction.CALL,
            PlayerAction.RAISE,
            PlayerAction.ALL_IN,
        }

    if table.current_bet > 0:
        return {
            PlayerAction.CHECK,
            PlayerAction.RAISE,
            PlayerAction.ALL_IN,
        }

    return {
        PlayerAction.FOLD,
        PlayerAction.CHECK,
        PlayerAction.BET,
        PlayerAction.ALL_IN,
    }
