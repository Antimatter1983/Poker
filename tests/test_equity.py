import pytest

from poker.card import Card
from poker import equity
from poker.equity import calculate_equity, normalize_starting_hand


def test_normalizes_suited_hand():
    assert normalize_starting_hand(["AS", "KS"]) == "AKs"


def test_normalizes_offsuit_hand():
    assert normalize_starting_hand(["AS", "KH"]) == "AKo"


def test_normalizes_pair():
    assert normalize_starting_hand(["TS", "TH"]) == "TT"


def test_preflop_uses_table_without_monte_carlo(monkeypatch):
    monkeypatch.setattr(equity, "_monte_carlo", lambda *a, **k: pytest.fail("Monte Carlo must not run preflop"))
    result = calculate_equity(["AS", "KS"], [], use_cache=False)
    assert result.method == equity.PREFLOP


def test_known_cards_are_excluded_from_simulated_opponent_and_board(monkeypatch):
    seen = []

    def fake_compare(hero, villain, board):
        known = {"AS", "KS", "QS", "7S", "2D"}
        generated = [str(card) for card in villain + board[3:]]
        seen.extend(generated)
        assert not known.intersection(generated)
        return 1

    monkeypatch.setattr(equity, "_compare", fake_compare)
    calculate_equity(["AS", "KS"], ["QS", "7S", "2D"], simulations=25, seed=1, use_cache=False)
    assert seen


def test_monte_carlo_is_deterministic_with_same_seed():
    first = calculate_equity(["AS", "KS"], ["QS", "7S", "2D"], simulations=200, seed=42, use_cache=False)
    second = calculate_equity(["AS", "KS"], ["QS", "7S", "2D"], simulations=200, seed=42, use_cache=False)
    assert first == second


@pytest.mark.parametrize("board", [[], ["QS", "7S", "2D"], ["QS", "7S", "2D", "3C"], ["QS", "7S", "2D", "3C", "4H"]])
def test_equity_percentages_sum_to_about_100(board):
    result = calculate_equity(["AS", "KS"], board, simulations=200, seed=7, use_cache=False)
    assert result.win_percent + result.tie_percent + result.loss_percent == pytest.approx(100.0)


def test_river_uses_exact_enumeration(monkeypatch):
    monkeypatch.setattr(equity, "_monte_carlo", lambda *a, **k: pytest.fail("Monte Carlo must not run on river"))
    result = calculate_equity(["AS", "KS"], ["QS", "7S", "2D", "3C", "4H"], use_cache=False)
    assert result.method == equity.EXACT


def test_same_cards_on_different_tables_reuse_one_cached_result(monkeypatch):
    equity.clear_equity_cache()
    calls = {"count": 0}
    original = equity._monte_carlo

    def counted(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(equity, "_monte_carlo", counted)
    a = calculate_equity([Card("A", "S"), Card("K", "S")], ["QS", "7S", "2D"], simulations=50)
    b = calculate_equity(["KS", "AS"], ["2D", "QS", "7S"], simulations=50)
    assert a == b
    assert calls["count"] == 1


def test_board_change_creates_new_result(monkeypatch):
    equity.clear_equity_cache()
    calls = {"count": 0}
    original = equity._monte_carlo

    def counted(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(equity, "_monte_carlo", counted)
    calculate_equity(["AS", "KS"], ["QS", "7S", "2D"], simulations=50)
    calculate_equity(["AS", "KS"], ["QS", "7S", "3D"], simulations=50)
    assert calls["count"] == 2


def test_hidden_bot_cards_do_not_influence_equity_before_showdown():
    result_a = calculate_equity(["AS", "KS"], ["QS", "7S", "2D"], simulations=200, seed=9, use_cache=False)
    hidden_bot_cards = ["AH", "AD"]
    result_b = calculate_equity(["AS", "KS"], ["QS", "7S", "2D"], simulations=200, seed=9, use_cache=False)
    assert hidden_bot_cards
    assert result_a == result_b


@pytest.mark.parametrize("hole,board", [(["AS", "AS"], []), (["AS", "KS"], ["AS", "2D", "3C"]), (["ZZ", "KS"], [])])
def test_invalid_or_duplicate_cards_raise_clear_error(hole, board):
    with pytest.raises(ValueError, match="Duplicate|Invalid|Unknown"):
        calculate_equity(hole, board, use_cache=False)
