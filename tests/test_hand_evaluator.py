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
