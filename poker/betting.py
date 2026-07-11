"""Betting action application for poker tables."""

from poker.actions import (
    ActionNotAvailableError,
    ActionRequest,
    ActionResult,
    InvalidRaiseError,
    MissingAmountError,
    NonPositiveAmountError,
    PlayerAction,
    StackExceededError,
)
from poker.player import Player
from poker.table import Table


class BettingActionProcessor:
    """Apply validated betting actions to a player and table state."""

    def apply(self, table: Table, player: Player, request: ActionRequest) -> ActionResult:
        """Apply a betting action and return the resulting state."""

        amount_paid = 0
        if request.action is PlayerAction.FOLD:
            player.folded = True
        elif request.action is PlayerAction.CHECK:
            self._ensure_check_allowed(table, player)
        elif request.action is PlayerAction.CALL:
            amount_paid = player.bet(player.call_amount(table.current_bet))
            table.pot += amount_paid
        elif request.action is PlayerAction.BET:
            amount_paid = self._apply_bet(table, player, request.amount)
        elif request.action is PlayerAction.RAISE:
            amount_paid = self._apply_raise(table, player, request.amount)
        elif request.action is PlayerAction.ALL_IN:
            amount_paid = player.bet(player.stack)
            table.pot += amount_paid
            if player.current_bet > table.current_bet:
                table.current_bet = player.current_bet

        player.last_action = request.action
        return ActionResult(
            player_id=player.id,
            action=request.action,
            amount_paid=amount_paid,
            player_stack=player.stack,
            player_current_bet=player.current_bet,
            table_current_bet=table.current_bet,
            pot=table.pot,
        )

    def _ensure_check_allowed(self, table: Table, player: Player) -> None:
        if player.call_amount(table.current_bet) != 0:
            raise ActionNotAvailableError(f"Player {player.id} cannot check while facing a bet")

    def _require_positive_amount(self, amount: int | None) -> int:
        if amount is None:
            raise MissingAmountError("Action amount is required")
        if amount <= 0:
            raise NonPositiveAmountError("Action amount must be positive")
        return amount

    def _apply_bet(self, table: Table, player: Player, requested_amount: int | None) -> int:
        if table.current_bet != 0:
            raise ActionNotAvailableError("Bet is not available after a bet already exists")
        amount = self._require_positive_amount(requested_amount)
        if amount > player.stack:
            raise StackExceededError("Bet amount cannot exceed player stack")

        amount_paid = player.bet(amount)
        table.pot += amount_paid
        table.current_bet = player.current_bet
        return amount_paid

    def _apply_raise(self, table: Table, player: Player, requested_amount: int | None) -> int:
        if table.current_bet == 0:
            raise ActionNotAvailableError("Raise is not available before a bet exists")
        amount = self._require_positive_amount(requested_amount)
        if amount <= table.current_bet:
            raise InvalidRaiseError("Raise amount must be greater than the current table bet")

        additional_amount = amount - player.current_bet
        if additional_amount <= 0:
            raise InvalidRaiseError("Raise amount must exceed the player's current bet")
        if additional_amount > player.stack:
            raise StackExceededError("Raise amount cannot exceed player stack")

        amount_paid = player.bet(additional_amount)
        table.pot += amount_paid
        table.current_bet = player.current_bet
        return amount_paid
