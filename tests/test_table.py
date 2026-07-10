import pytest

from poker.cards import Card, Rank, Suit
from poker.player import Player
from poker.table import Table


def make_table() -> Table:
    players = [
        Player(id="p1", name="Alice", stack=1_000),
        Player(id="p2", name="Bob", stack=1_000),
    ]
    return Table(table_id="table-1", players=players, small_blind=5, big_blind=10)


def test_player_at_uses_circular_positions() -> None:
    table = make_table()

    assert table.player_at(0).name == "Alice"
    assert table.player_at(1).name == "Bob"
    assert table.player_at(2).name == "Alice"


def test_player_at_rejects_empty_table() -> None:
    table = Table(table_id="empty", players=[])

    with pytest.raises(ValueError, match="no players"):
        table.player_at(0)


def test_reset_for_new_hand_clears_table_and_player_hand_state() -> None:
    table = make_table()
    table.pot = 100
    table.community_cards.append(Card(rank=Rank.ACE, suit=Suit.SPADES))
    table.current_bet = 20
    table.street = "river"
    table.players[0].hand.append(Card(rank=Rank.KING, suit=Suit.HEARTS))
    table.players[0].current_bet = 20
    table.players[0].folded = True

    table.reset_for_new_hand()

    assert table.pot == 0
    assert table.community_cards == []
    assert table.current_bet == 0
    assert table.street == "preflop"
    assert table.players[0].hand == []
    assert table.players[0].current_bet == 0
    assert table.players[0].folded is False
