from poker.card import Card
from poker.hand_evaluator import HandEvaluator
from web.game_store import showdown_hand_explanation


def C(text):
    return Card(text[0], text[1])


def E(cards):
    return HandEvaluator.evaluate([C(c) for c in cards.split()])


def codes(cards):
    return {card["code"] for card in cards}


def assert_combo_count(cards, expected_name, expected_count, expected_kicker_count=0):
    value = E(cards)
    explanation = showdown_hand_explanation(value)
    assert value.name == expected_name
    assert len(explanation["combination_cards"]) == expected_count
    assert len(explanation["kicker_cards"]) == expected_kicker_count


def test_pair_highlights_two_combination_cards():
    assert_combo_count("TS TD AH KC 8S 4D 2C", "One Pair", 2, 0)


def test_pair_split_between_hole_card_and_board_highlights_only_pair_cards():
    value = E("TS AH TD KC 8S 4D 2C")
    explanation = showdown_hand_explanation(value)

    assert value.name == "One Pair"
    assert codes(explanation["combination_cards"]) == {"TS", "TD"}
    assert explanation["kicker_cards"] == []


def test_two_pair_highlights_four_combination_cards():
    assert_combo_count("TS TD AH AC 8S 4D 2C", "Two Pair", 4, 0)


def test_three_of_a_kind_highlights_three_combination_cards():
    assert_combo_count("7S 7D 7C AH KS 4D 2C", "Three of a Kind", 3, 0)


def test_four_of_a_kind_highlights_four_combination_cards():
    assert_combo_count("7S 7D 7C 7H KS 4D 2C", "Four of a Kind", 4, 0)


def test_straight_highlights_five_combination_cards():
    assert_combo_count("AS KD QH JC TS 4D 2C", "Straight", 5)


def test_flush_highlights_five_combination_cards():
    assert_combo_count("AS QS 9S 6S 3S 4D 2C", "Flush", 5)


def test_full_house_highlights_five_combination_cards():
    assert_combo_count("AS AD AH KC KS 4D 2C", "Full House", 5)


def test_high_card_highlights_only_top_card_without_rendered_kickers():
    value = E("AS KD QH 9C 8S 4D 2C")
    explanation = showdown_hand_explanation(value)

    assert value.name == "High Card"
    assert codes(explanation["combination_cards"]) == {"AS"}
    assert explanation["kicker_cards"] == []


def test_equal_pairs_can_describe_deciding_kicker():
    player = E("TS TD AH 9C 8S 4D 2C")
    bot = E("TH TC KH 9D 8C 4S 2D")

    player_explanation = showdown_hand_explanation(player, bot)
    bot_explanation = showdown_hand_explanation(bot, player)

    assert len(player_explanation["combination_cards"]) == 2
    assert len(bot_explanation["combination_cards"]) == 2
    assert codes(player_explanation["kicker_cards"]) == {"AH"}
    assert codes(bot_explanation["kicker_cards"]) == {"KH"}
    assert "кикер туз" in player_explanation["summary"]
    assert "кикер король" in bot_explanation["summary"]
