from poker.engine import MatchEngine
from poker.player import Player
from poker.table import Table


def make_table() -> Table:
    players = [
        Player(id="p1", name="Alice", stack=1_000),
        Player(id="p2", name="Bob", stack=1_000),
    ]
    return Table(table_id="table-1", players=players, small_blind=5, big_blind=10)


def test_players_receive_two_hole_cards() -> None:
    table = make_table()
    engine = MatchEngine(table)

    engine.start_hand()

    assert [len(player.hand) for player in table.players] == [2, 2]


def test_blinds_are_posted() -> None:
    table = make_table()
    engine = MatchEngine(table)

    engine.start_hand()

    assert table.players[1].current_bet == 5
    assert table.players[0].current_bet == 10
    assert table.pot == 15
    assert table.current_bet == 10


def test_flop_adds_three_community_cards() -> None:
    table = make_table()
    engine = MatchEngine(table)
    engine.start_hand()

    engine.deal_flop()

    assert len(table.community_cards) == 3
    assert table.street == "flop"


def test_turn_adds_one_community_card() -> None:
    table = make_table()
    engine = MatchEngine(table)
    engine.start_hand()
    engine.deal_flop()

    engine.deal_turn()

    assert len(table.community_cards) == 4
    assert table.street == "turn"


def test_river_adds_one_community_card() -> None:
    table = make_table()
    engine = MatchEngine(table)
    engine.start_hand()
    engine.deal_flop()
    engine.deal_turn()

    engine.deal_river()

    assert len(table.community_cards) == 5
    assert table.street == "river"
