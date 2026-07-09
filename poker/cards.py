"""Card primitives used by the poker engine."""

from dataclasses import dataclass
from enum import Enum


class Suit(str, Enum):
    """A standard playing-card suit."""

    CLUBS = "clubs"
    DIAMONDS = "diamonds"
    HEARTS = "hearts"
    SPADES = "spades"


class Rank(str, Enum):
    """A standard playing-card rank."""

    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


@dataclass(frozen=True, slots=True)
class Card:
    """A single immutable playing card."""

    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value[0].upper()}"
