"""Deck implementation for Texas Hold'em."""

import random
from collections.abc import Sequence

from poker.cards import Card, Rank, Suit


class Deck:
    """A standard 52-card deck."""

    def __init__(self, cards: Sequence[Card] | None = None) -> None:
        self.cards: list[Card] = list(cards) if cards is not None else self._build_standard_deck()

    @staticmethod
    def _build_standard_deck() -> list[Card]:
        return [Card(rank=rank, suit=suit) for suit in Suit for rank in Rank]

    def shuffle(self) -> None:
        """Shuffle cards in place."""

        random.shuffle(self.cards)

    def deal_one(self) -> Card:
        """Deal one card from the top of the deck."""

        if not self.cards:
            raise ValueError("Cannot deal from an empty deck")
        return self.cards.pop()

    def deal_many(self, count: int) -> list[Card]:
        """Deal several cards from the top of the deck."""

        if count < 0:
            raise ValueError("Cannot deal a negative number of cards")
        if count > len(self.cards):
            raise ValueError("Not enough cards left in the deck")
        return [self.deal_one() for _ in range(count)]

    def __len__(self) -> int:
        return len(self.cards)
