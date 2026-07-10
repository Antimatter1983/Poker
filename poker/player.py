"""Player model for the poker engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from poker.cards import Card

if TYPE_CHECKING:
    from poker.actions import PlayerAction


@dataclass(slots=True)
class Player:
    """A player seated at a poker table."""

    id: str
    name: str
    stack: int
    hand: list[Card] = field(default_factory=list)
    current_bet: int = 0
    folded: bool = False
    all_in: bool = False
    last_action: PlayerAction | None = None

    def reset_for_new_hand(self) -> None:
        """Clear per-hand state before a new hand starts."""

        self.hand.clear()
        self.current_bet = 0
        self.folded = False
        self.all_in = False
        self.last_action = None

    def call_amount(self, table_current_bet: int) -> int:
        """Return chips needed to match the table bet, never below zero."""

        return max(table_current_bet - self.current_bet, 0)

    def bet(self, amount: int) -> int:
        """Move chips from the stack into the current bet and return paid amount."""

        if amount < 0:
            raise ValueError("Bet amount cannot be negative")
        paid = min(amount, self.stack)
        self.stack -= paid
        self.current_bet += paid
        self.all_in = self.stack == 0
        return paid
