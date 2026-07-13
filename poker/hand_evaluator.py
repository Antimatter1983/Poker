from dataclasses import dataclass
from itertools import combinations
from .card import Card

HAND_NAMES = {
    1: "High Card", 2: "One Pair", 3: "Two Pair", 4: "Three of a Kind",
    5: "Straight", 6: "Flush", 7: "Full House", 8: "Four of a Kind", 9: "Straight Flush",
}


@dataclass(frozen=True)
class HandValue:
    rank: int
    name: str
    tiebreakers: tuple[int, ...]
    best_five: tuple[Card, ...]

    def _key(self):
        return (self.rank, self.tiebreakers)

    def __lt__(self, other):
        return self._key() < other._key()

    def __le__(self, other):
        return self._key() <= other._key()

    def __gt__(self, other):
        return self._key() > other._key()

    def __ge__(self, other):
        return self._key() >= other._key()

    def __eq__(self, other):
        if not isinstance(other, HandValue):
            return False
        return self._key() == other._key()


def evaluate_hand(cards: list[Card]) -> HandValue:
    if len(cards) != 7:
        raise ValueError("Texas Hold'em evaluation requires exactly 7 cards")
    return max((_evaluate_five(tuple(combo)) for combo in combinations(cards, 5)), key=lambda h: h._key())


class HandEvaluator:
    @staticmethod
    def evaluate(cards: list[Card]) -> HandValue:
        return evaluate_hand(cards)


def _straight_high(values: list[int]) -> int | None:
    unique = sorted(set(values), reverse=True)
    if 14 in unique:
        unique.append(1)
    for i in range(len(unique) - 4):
        window = unique[i:i + 5]
        if window[0] - window[4] == 4 and len(window) == 5:
            return 5 if window[0] == 5 else window[0]
    return None


def _cards_matching_value(cards: tuple[Card, ...], value: int) -> list[Card]:
    wanted = 14 if value == 1 else value
    return [card for card in cards if card.value == wanted]


def _cards_excluding_values(cards: tuple[Card, ...], excluded: set[int]) -> list[Card]:
    return sorted((card for card in cards if card.value not in excluded), key=lambda c: c.value, reverse=True)


def _straight_values(high: int) -> tuple[int, ...]:
    if high == 5:
        return (5, 4, 3, 2, 14)
    return tuple(range(high, high - 5, -1))


def _straight_cards(cards: tuple[Card, ...], high: int) -> tuple[Card, ...]:
    ordered = []
    for value in _straight_values(high):
        ordered.append(_cards_matching_value(cards, value)[0])
    return tuple(ordered)


def _evaluate_five(cards: tuple[Card, ...]) -> HandValue:
    values = sorted((c.value for c in cards), reverse=True)
    counts = {v: values.count(v) for v in set(values)}
    groups = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
    flush = len({c.suit for c in cards}) == 1
    straight = _straight_high(values)

    if flush and straight:
        rank, tb = 9, (straight,)
        best_five = _straight_cards(cards, straight)
    elif groups[0][1] == 4:
        quad = groups[0][0]
        kicker = max(v for v in values if v != quad)
        rank, tb = 8, (quad, kicker)
        best_five = tuple(_cards_matching_value(cards, quad) + _cards_matching_value(cards, kicker))
    elif groups[0][1] == 3 and groups[1][1] == 2:
        trips, pair = groups[0][0], groups[1][0]
        rank, tb = 7, (trips, pair)
        best_five = tuple(_cards_matching_value(cards, trips) + _cards_matching_value(cards, pair))
    elif flush:
        rank, tb = 6, tuple(values)
        best_five = tuple(sorted(cards, key=lambda c: c.value, reverse=True))
    elif straight:
        rank, tb = 5, (straight,)
        best_five = _straight_cards(cards, straight)
    elif groups[0][1] == 3:
        trips = groups[0][0]
        kickers = sorted((v for v in values if v != trips), reverse=True)
        rank, tb = 4, (trips, *kickers)
        best_five = tuple(_cards_matching_value(cards, trips) + _cards_excluding_values(cards, {trips})[:2])
    elif groups[0][1] == 2 and groups[1][1] == 2:
        pairs = sorted([v for v, c in counts.items() if c == 2], reverse=True)
        kicker = max(v for v in values if v not in pairs)
        rank, tb = 3, (pairs[0], pairs[1], kicker)
        best_five = tuple(_cards_matching_value(cards, pairs[0]) + _cards_matching_value(cards, pairs[1]) + _cards_matching_value(cards, kicker))
    elif groups[0][1] == 2:
        pair = groups[0][0]
        kickers = sorted((v for v in values if v != pair), reverse=True)
        rank, tb = 2, (pair, *kickers)
        best_five = tuple(_cards_matching_value(cards, pair) + _cards_excluding_values(cards, {pair})[:3])
    else:
        rank, tb = 1, tuple(values)
        best_five = tuple(sorted(cards, key=lambda c: c.value, reverse=True))
    return HandValue(rank, HAND_NAMES[rank], tb, best_five)
