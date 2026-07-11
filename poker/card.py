from dataclasses import dataclass

RANKS = "23456789TJQKA"
SUITS = "CDHS"
RANK_VALUES = {rank: index + 2 for index, rank in enumerate(RANKS)}


@dataclass(frozen=True, order=True)
class Card:
    rank: str
    suit: str

    def __post_init__(self):
        rank = self.rank.upper()
        suit = self.suit.upper()
        if rank not in RANKS:
            raise ValueError(f"Unknown card rank: {self.rank}")
        if suit not in SUITS:
            raise ValueError(f"Unknown card suit: {self.suit}")
        object.__setattr__(self, "rank", rank)
        object.__setattr__(self, "suit", suit)

    @property
    def value(self) -> int:
        return RANK_VALUES[self.rank]

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        return str(self)
