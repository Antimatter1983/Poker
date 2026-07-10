import pytest

from poker.actions import ActionNotAvailableError, ActionRequest, PlayerAction
from poker.engine import MatchEngine
from poker.player import Player
from poker.table import Table


def players(count: int) -> list[Player]:
    names = ["Alice", "Bob", "Charlie", "Diana"]
    return [Player(id=f"p{index + 1}", name=names[index], stack=1_000) for index in range(count)]


def table_with(count: int) -> Table:
    return Table(
        table_id="table-1",
        players=players(count),
        button_position=0,
        small_blind=5,
        big_blind=10,
    )


def test_first_preflop_actor_heads_up_is_small_blind_button() -> None:
    table = table_with(2)
    MatchEngine(table).start_hand()

    assert table.players[0].current_bet == 5
    assert table.players[1].current_bet == 10
    assert table.get_acting_player() == table.players[0]


def test_first_flop_actor_heads_up_is_big_blind() -> None:
    table = table_with(2)
    engine = MatchEngine(table)
    engine.start_hand()
    engine.deal_flop()

    assert table.get_acting_player() == table.players[1]


def test_first_preflop_actor_three_players_is_left_of_big_blind() -> None:
    table = table_with(3)
    MatchEngine(table).start_hand()

    assert table.players[1].current_bet == 5
    assert table.players[2].current_bet == 10
    assert table.get_acting_player() == table.players[0]


def test_first_flop_actor_three_players_is_left_of_button() -> None:
    table = table_with(3)
    engine = MatchEngine(table)
    engine.start_hand()
    engine.deal_flop()

    assert table.get_acting_player() == table.players[1]


def test_action_moves_to_next_player() -> None:
    table = table_with(3)
    engine = MatchEngine(table)
    engine.start_hand()

    engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CALL))

    assert table.get_acting_player() == table.players[1]


def test_next_actor_skips_folded_player() -> None:
    table = table_with(3)
    table.street = "flop"
    table.acting_player_index = 0
    table.players[1].folded = True

    next_player = table.move_to_next_actor()

    assert next_player == table.players[2]
    assert table.acting_player_index == 2


def test_next_actor_skips_all_in_player() -> None:
    table = table_with(3)
    table.street = "flop"
    table.acting_player_index = 0
    table.players[1].all_in = True

    next_player = table.move_to_next_actor()

    assert next_player == table.players[2]
    assert table.acting_player_index == 2


def test_action_out_of_turn_is_rejected() -> None:
    table = table_with(3)
    engine = MatchEngine(table)
    engine.start_hand()

    with pytest.raises(ActionNotAvailableError, match="turn to act"):
        engine.apply_action(ActionRequest(player_id="p2", action=PlayerAction.CALL))


def test_turn_order_is_preserved_after_failed_action() -> None:
    table = table_with(3)
    engine = MatchEngine(table)
    engine.start_hand()
    original_index = table.acting_player_index

    with pytest.raises(ActionNotAvailableError):
        engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CHECK))

    assert table.acting_player_index == original_index
    assert table.get_acting_player() == table.players[0]


def test_no_actor_remains_when_every_other_player_cannot_act() -> None:
    table = table_with(2)
    table.street = "flop"
    table.acting_player_index = 0
    table.players[1].folded = True
    engine = MatchEngine(table)

    engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CHECK))

    assert table.acting_player_index is None
    assert table.get_acting_player() is None
    assert table.game_log.events()[-1].event_type == "no_actor"
