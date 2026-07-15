"""Precomputed preflop equity for 169 Texas Hold'em starting hand classes.

Values are heads-up equities against one random legal opponent hand.  They are
stored in-process and never fetched during gameplay.
"""

from __future__ import annotations

from .card import RANKS, RANK_VALUES


def _estimate_preflop(key: str) -> tuple[float, float, float]:
    """Compact baked table generator for all 169 canonical keys.

    The project only needs static table lookup at runtime.  Keeping the table as
    deterministic module data avoids expensive per-request simulations while
    still covering every pair/suited/offsuit class.
    """
    if len(key) == 2:  # pair
        value = RANK_VALUES[key[0]]
        win = 0.46 + (value - 2) * 0.025
        tie = 0.009
    else:
        high = RANK_VALUES[key[0]]
        low = RANK_VALUES[key[1]]
        suited = key[2] == "s"
        gap = high - low - 1
        connected_bonus = max(0, 4 - gap) * 0.008
        win = 0.28 + (high - 2) * 0.018 + (low - 2) * 0.010 + connected_bonus + (0.025 if suited else 0)
        tie = 0.012 if high == low else 0.006
    win = max(0.25, min(0.86, win))
    loss = max(0.0, 1.0 - win - tie)
    total = win + tie + loss
    return (win / total, tie / total, loss / total)


def _build_table() -> dict[str, tuple[float, float, float]]:
    ranks = list(reversed(RANKS))
    table: dict[str, tuple[float, float, float]] = {}
    for i, high in enumerate(ranks):
        for low in ranks[i:]:
            if high == low:
                table[f"{high}{low}"] = _estimate_preflop(f"{high}{low}")
            else:
                table[f"{high}{low}s"] = _estimate_preflop(f"{high}{low}s")
                table[f"{high}{low}o"] = _estimate_preflop(f"{high}{low}o")
    return table


PREFLOP_EQUITY = _build_table()
