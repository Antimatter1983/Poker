import pytest

from poker import equity
from poker.equity import calculate_equity, normalize_starting_hand
from poker.preflop_equity import PREFLOP_EQUITY


def test_normalizes_suited_hand():
    assert normalize_starting_hand(["AS", "KS"]) == "AKs"


def test_normalizes_offsuit_hand():
    assert normalize_starting_hand(["AS", "KH"]) == "AKo"


def test_normalizes_pair():
    assert normalize_starting_hand(["TS", "TH"]) == "TT"


def test_preflop_value_comes_from_table(monkeypatch):
    monkeypatch.setattr(equity, "_monte_carlo", lambda *a, **k: pytest.fail("Monte Carlo must not run preflop"))
    monkeypatch.setattr(equity, "_exact", lambda *a, **k: pytest.fail("Exact enumeration must not run preflop"))

    result = calculate_equity(["AS", "KS"], [], use_cache=False)

    assert result.method == equity.PREFLOP
    assert (result.win, result.tie, result.loss) == PREFLOP_EQUITY["AKs"]


@pytest.mark.parametrize("board", [["QS", "7S", "2D"], ["QS", "7S", "2D", "3C"], ["QS", "7S", "2D", "3C", "4H"]])
def test_postflop_calculate_equity_returns_none_without_heavy_calculation(monkeypatch, board):
    monkeypatch.setattr(equity, "_monte_carlo", lambda *a, **k: pytest.fail("Monte Carlo must not run postflop"))
    monkeypatch.setattr(equity, "_exact", lambda *a, **k: pytest.fail("Exact enumeration must not run postflop"))

    assert calculate_equity(["AS", "KS"], board, use_cache=False) is None


@pytest.mark.parametrize("hole,board", [(["AS", "AS"], []), (["AS", "KS"], ["AS", "2D", "3C"]), (["ZZ", "KS"], [])])
def test_invalid_or_duplicate_cards_raise_clear_error(hole, board):
    with pytest.raises(ValueError, match="Duplicate|Invalid|Unknown"):
        calculate_equity(hole, board, use_cache=False)
