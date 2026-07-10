import pytest

from poker.cards import Card, Rank, Suit
from poker.player import Player


def test_player_bet_moves_chips_to_current_bet() -> None:
    player = Player(id="p1", name="Alice", stack=100)

    paid = player.bet(25)

    assert paid == 25
    assert player.stack == 75
    assert player.current_bet == 25
    assert player.all_in is False


def test_player_bet_caps_paid_amount_at_stack_and_marks_all_in() -> None:
    player = Player(id="p1", name="Alice", stack=20)

    paid = player.bet(50)

    assert paid == 20
    assert player.stack == 0
    assert player.current_bet == 20
    assert player.all_in is True


def test_player_bet_rejects_negative_amount() -> None:
    player = Player(id="p1", name="Alice", stack=100)

    with pytest.raises(ValueError, match="negative"):
        player.bet(-1)


def test_player_reset_for_new_hand_clears_hand_state() -> None:
    player = Player(
        id="p1",
        name="Alice",
        stack=100,
        hand=[Card(rank=Rank.ACE, suit=Suit.SPADES)],
        current_bet=10,
        folded=True,
        all_in=True,
    )

    player.reset_for_new_hand()

    assert player.hand == []
    assert player.current_bet == 0
    assert player.folded is False
    assert player.all_in is False
