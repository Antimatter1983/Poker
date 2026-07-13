from poker.card import Card
from poker.hand_evaluator import _evaluate_five
from web.game_store import combination_cards, decisive_kicker_cards


def C(text):
    return Card(text[0], text[1])


def V(cards):
    return _evaluate_five(tuple(C(card) for card in cards.split()))


def codes(cards):
    return {str(card) for card in cards}


def test_pair_highlights_only_two_pair_cards():
    value = V("TH TD AS KC 2D")
    assert codes(combination_cards(value)) == {"TH", "TD"}


def test_two_pair_highlights_four_pair_cards():
    value = V("TH TD 7S 7C AD")
    assert codes(combination_cards(value)) == {"TH", "TD", "7S", "7C"}


def test_three_of_a_kind_highlights_three_trip_cards():
    value = V("7H 7D 7S AC KD")
    assert codes(combination_cards(value)) == {"7H", "7D", "7S"}


def test_four_of_a_kind_highlights_four_quad_cards():
    value = V("9H 9D 9S 9C AD")
    assert codes(combination_cards(value)) == {"9H", "9D", "9S", "9C"}


def test_straight_highlights_all_five_cards():
    value = V("9H 8D 7S 6C 5D")
    assert len(combination_cards(value)) == 5


def test_flush_highlights_all_five_cards():
    value = V("AH JH 8H 4H 2H")
    assert len(combination_cards(value)) == 5


def test_full_house_highlights_all_five_cards():
    value = V("QH QD QS 4C 4D")
    assert len(combination_cards(value)) == 5


def test_equal_pairs_highlight_decisive_kicker_separately():
    player = V("TH TD AS KC 2D")
    bot = V("TS TC KS QD 2C")

    assert codes(combination_cards(player)) == {"TH", "TD"}
    assert codes(combination_cards(bot)) == {"TS", "TC"}
    assert codes(decisive_kicker_cards(player, bot)) == {"AS"}
    assert codes(decisive_kicker_cards(bot, player)) == {"KS"}
