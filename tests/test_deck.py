import pytest
from poker.deck import Deck


def test_deck_has_52_unique_cards():
    deck = Deck()
    assert len(deck.cards) == 52
    assert len(set(deck.cards)) == 52


def test_deal_reduces_count_and_no_duplicate():
    deck = Deck()
    card = deck.deal_one()
    assert len(deck) == 51
    assert card not in deck.cards
    dealt = deck.deal(10)
    assert len(dealt) == len(set(dealt))
    assert len(deck) == 41


def test_not_enough_cards_error():
    deck = Deck()
    with pytest.raises(ValueError, match="Not enough"):
        deck.deal(53)
