from poker.card import Card
from poker.hand_evaluator import HandEvaluator


def C(text): return Card(text[0], text[1])
def E(cards): return HandEvaluator.evaluate([C(c) for c in cards.split()])


def test_all_hand_types():
    assert E("AS KD 9H 7C 5S 3D 2C").name == "High Card"
    assert E("AS AD 9H 7C 5S 3D 2C").name == "One Pair"
    assert E("AS AD 9H 9C 5S 3D 2C").name == "Two Pair"
    assert E("AS AD AH 9C 5S 3D 2C").name == "Three of a Kind"
    assert E("AS KD QH JC TS 3D 2C").name == "Straight"
    assert E("AS 2D 3H 4C 5S 9D TC").tiebreakers == (5,)
    assert E("AS QS 9S 6S 3S 2D TC").name == "Flush"
    assert E("AS AD AH 9C 9S 3D 2C").name == "Full House"
    assert E("AS AD AH AC 9S 3D 2C").name == "Four of a Kind"
    assert E("AS KS QS JS TS 3D 2C").name == "Straight Flush"


def test_kicker_comparison_and_tie():
    ace_pair_king = E("AS AD KH 9C 7S 3D 2C")
    ace_pair_queen = E("AS AD QH 9C 7S 3D 2C")
    assert ace_pair_king > ace_pair_queen
    assert E("AS KD QH JC 9S 3D 2C") == E("AH KC QS JD 9D 3C 2H")


def S(value): return tuple(str(card) for card in value.best_five)


def assert_best_five(cards, name, expected):
    value = E(cards)
    assert value.name == name
    assert len(value.best_five) == 5
    assert S(value) == tuple(expected.split())


def test_best_five_three_of_a_kind_uses_two_real_kickers():
    assert_best_five(
        "7S 7D 7C AS KD 4H 2C",
        "Three of a Kind",
        "7S 7D 7C AS KD",
    )


def test_best_five_full_house_uses_trips_and_pair():
    assert_best_five(
        "QH QS QC 7S 7D AS KD",
        "Full House",
        "QH QS QC 7S 7D",
    )


def test_best_five_two_pair_uses_two_highest_pairs_and_kicker():
    assert_best_five(
        "AS AD KH KC QS QD 2C",
        "Two Pair",
        "AS AD KH KC QS",
    )


def test_best_five_flush_uses_five_highest_suited_cards():
    assert_best_five(
        "AS QS 9S 6S 3S 2S TC",
        "Flush",
        "AS QS 9S 6S 3S",
    )


def test_best_five_straight_uses_exact_sequence():
    assert_best_five(
        "AS KD QH JC TS 9D 2C",
        "Straight",
        "AS KD QH JC TS",
    )


def test_best_five_four_of_a_kind_uses_best_kicker():
    assert_best_five(
        "AS AD AH AC KS QD 2C",
        "Four of a Kind",
        "AS AD AH AC KS",
    )


def test_best_five_can_be_entirely_on_board():
    assert_best_five(
        "2C 3D AS KS QS JS TS",
        "Straight Flush",
        "AS KS QS JS TS",
    )
