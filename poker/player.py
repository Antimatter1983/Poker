"""Player model for the poker engine."""

from dataclasses import dataclass, field

from poker.cards import Card


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

    def reset_for_new_hand(self) -> None:
        """Clear per-hand state before a new hand starts."""

        self.hand.clear()
        self.current_bet = 0
        self.folded = False
        self.all_in = False

    def bet(self, amount: int) -> int:
        """Move chips from the stack into the current bet and return paid amount."""

        if amount < 0:
            raise ValueError("Bet amount cannot be negative")
        paid = min(amount, self.stack)
        self.stack -= paid
        self.current_bet += paid
        self.all_in = self.stack == 0
        return paid
