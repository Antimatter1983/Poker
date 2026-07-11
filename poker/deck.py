import random
from .card import Card, RANKS, SUITS


class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for suit in SUITS for rank in RANKS]

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal_one(self) -> Card:
        if not self.cards:
            raise ValueError("Not enough cards in the deck")
        return self.cards.pop()

    def deal(self, count: int) -> list[Card]:
        if count < 0:
            raise ValueError("Card count cannot be negative")
        if len(self.cards) < count:
            raise ValueError(f"Not enough cards in the deck: need {count}, have {len(self.cards)}")
        return [self.deal_one() for _ in range(count)]

    def __len__(self) -> int:
        return len(self.cards)
