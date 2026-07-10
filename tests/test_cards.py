from poker.cards import Card, Rank, Suit


def test_card_string_contains_rank_and_suit_initial() -> None:
    card = Card(rank=Rank.ACE, suit=Suit.SPADES)

    assert str(card) == "AS"


def test_card_is_immutable_and_hashable() -> None:
    card = Card(rank=Rank.TEN, suit=Suit.HEARTS)

    assert card in {card}
