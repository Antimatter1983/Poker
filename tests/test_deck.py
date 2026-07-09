from poker.deck import Deck


def test_deck_has_52_unique_cards() -> None:
    deck = Deck()

    assert len(deck.cards) == 52
    assert len(set(deck.cards)) == 52
