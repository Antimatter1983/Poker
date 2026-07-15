"""Player equity calculation against one unknown random opponent hand."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import random
from typing import Iterable

from .card import Card, RANK_VALUES, RANKS, SUITS
from .hand_evaluator import HandEvaluator
from .preflop_equity import PREFLOP_EQUITY

PREFLOP = "table"
EXACT = "exact"
MONTE_CARLO = "monte_carlo"
DEFAULT_FLOP_SIMULATIONS = 7000
DEFAULT_TURN_SIMULATIONS = 15000

_EQUITY_CACHE: dict[tuple, "EquityResult"] = {}


@dataclass(frozen=True)
class EquityResult:
    win: float
    tie: float
    loss: float
    method: str
    simulations: int | None = None

    @property
    def win_percent(self) -> float:
        return self.win * 100

    @property
    def tie_percent(self) -> float:
        return self.tie * 100

    @property
    def loss_percent(self) -> float:
        return self.loss * 100


def card_code(card: Card | str) -> str:
    if isinstance(card, Card):
        return str(card)
    text = str(card).strip().upper()
    if len(text) != 2:
        raise ValueError(f"Invalid card code: {card}")
    return str(Card(text[0], text[1]))


def _coerce_cards(cards: Iterable[Card | str], *, expected: int | None = None, label: str = "cards") -> list[Card]:
    result = [Card(card_code(card)[0], card_code(card)[1]) for card in cards]
    if expected is not None and len(result) != expected:
        raise ValueError(f"Expected {expected} {label}, got {len(result)}")
    if len({str(card) for card in result}) != len(result):
        raise ValueError("Duplicate cards are not allowed")
    return result


def normalize_starting_hand(hole_cards: Iterable[Card | str]) -> str:
    cards = sorted(_coerce_cards(hole_cards, expected=2, label="hole cards"), key=lambda c: c.value, reverse=True)
    first, second = cards
    if first.rank == second.rank:
        return f"{first.rank}{second.rank}"
    suffix = "s" if first.suit == second.suit else "o"
    return f"{first.rank}{second.rank}{suffix}"


def _deck_without(known: list[Card]) -> list[Card]:
    known_codes = {str(card) for card in known}
    return [Card(rank, suit) for suit in SUITS for rank in RANKS if f"{rank}{suit}" not in known_codes]


def _cache_key(hole: list[Card], board: list[Card], method: str, simulations: int | None) -> tuple:
    return (
        tuple(sorted(str(card) for card in hole)),
        tuple(sorted(str(card) for card in board)),
        method,
        simulations if method == MONTE_CARLO else None,
    )


def _validate_state(hole_cards: Iterable[Card | str], board_cards: Iterable[Card | str]) -> tuple[list[Card], list[Card]]:
    hole = _coerce_cards(hole_cards, expected=2, label="hole cards")
    board = _coerce_cards(board_cards, label="board cards")
    if len(board) not in {0, 3, 4, 5}:
        raise ValueError("Board must contain 0, 3, 4, or 5 cards")
    if len({str(card) for card in hole + board}) != len(hole) + len(board):
        raise ValueError("Duplicate cards are not allowed")
    return hole, board


def _result(wins: int, ties: int, losses: int, method: str, simulations: int | None = None) -> EquityResult:
    total = wins + ties + losses
    if total <= 0:
        raise ValueError("No equity trials were evaluated")
    return EquityResult(wins / total, ties / total, losses / total, method, simulations)


def _compare(hero: list[Card], villain: list[Card], board: list[Card]) -> int:
    hero_value = HandEvaluator.evaluate(hero + board)
    villain_value = HandEvaluator.evaluate(villain + board)
    if hero_value > villain_value:
        return 1
    if hero_value == villain_value:
        return 0
    return -1


def _record(outcome: int, counts: list[int]) -> None:
    if outcome > 0:
        counts[0] += 1
    elif outcome == 0:
        counts[1] += 1
    else:
        counts[2] += 1


def _monte_carlo(hole: list[Card], board: list[Card], simulations: int, seed: int | None) -> EquityResult:
    rng = random.Random(seed)
    counts = [0, 0, 0]
    known = hole + board
    need_board = 5 - len(board)
    for _ in range(simulations):
        deck = _deck_without(known)
        rng.shuffle(deck)
        opponent = [deck.pop(), deck.pop()]
        runout = [deck.pop() for _ in range(need_board)]
        _record(_compare(hole, opponent, board + runout), counts)
    return _result(*counts, method=MONTE_CARLO, simulations=simulations)


def _exact(hole: list[Card], board: list[Card]) -> EquityResult:
    counts = [0, 0, 0]
    deck = _deck_without(hole + board)
    if len(board) == 5:
        for opponent in combinations(deck, 2):
            _record(_compare(hole, list(opponent), board), counts)
    elif len(board) == 4:
        for opponent in combinations(deck, 2):
            remaining = [card for card in deck if card not in opponent]
            for river in remaining:
                _record(_compare(hole, list(opponent), board + [river]), counts)
    else:
        raise ValueError("Exact equity is supported only on turn and river")
    return _result(*counts, method=EXACT)


def calculate_equity(hole_cards: Iterable[Card | str], board_cards: Iterable[Card | str] = (), *, simulations: int | None = None, seed: int | None = None, use_cache: bool = True) -> EquityResult:
    """Return equity using only hero cards and the public board.

    Opponent cards are always generated from legal unknown cards; actual bot cards
    must not be supplied here before showdown.
    """
    hole, board = _validate_state(hole_cards, board_cards)
    if len(board) == 0:
        method, sims = PREFLOP, None
        key = _cache_key(hole, board, method, sims)
        if use_cache and key in _EQUITY_CACHE:
            return _EQUITY_CACHE[key]
        result = EquityResult(*PREFLOP_EQUITY[normalize_starting_hand(hole)], method=method)
    elif len(board) == 3:
        method, sims = MONTE_CARLO, simulations or DEFAULT_FLOP_SIMULATIONS
        key = _cache_key(hole, board, method, sims)
        if use_cache and seed is None and key in _EQUITY_CACHE:
            return _EQUITY_CACHE[key]
        result = _monte_carlo(hole, board, sims, seed)
    elif len(board) in {4, 5}:
        method, sims = EXACT, None
        key = _cache_key(hole, board, method, sims)
        if use_cache and key in _EQUITY_CACHE:
            return _EQUITY_CACHE[key]
        result = _exact(hole, board)
    else:  # already validated, defensive only
        raise ValueError("Unsupported board size")
    if use_cache and not (method == MONTE_CARLO and seed is not None):
        _EQUITY_CACHE[key] = result
    return result


def clear_equity_cache() -> None:
    _EQUITY_CACHE.clear()
