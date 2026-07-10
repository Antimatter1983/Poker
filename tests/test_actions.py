from poker.actions import PlayerAction, available_actions
from poker.player import Player
from poker.table import Table


def make_table(player: Player | None = None, current_bet: int = 0) -> Table:
    players = [player or Player(id="p1", name="Alice", stack=100)]
    table = Table(table_id="table-1", players=players)
    table.current_bet = current_bet
    return table


def test_call_amount_never_negative() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=15)

    assert player.call_amount(25) == 10
    assert player.call_amount(15) == 0
    assert player.call_amount(5) == 0


def test_available_actions_when_call_is_required() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=5)
    table = make_table(player, current_bet=10)

    assert available_actions(player, table) == {
        PlayerAction.FOLD,
        PlayerAction.CALL,
        PlayerAction.RAISE,
        PlayerAction.ALL_IN,
    }


def test_available_actions_allow_check_when_bet_is_matched() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=10)
    table = make_table(player, current_bet=10)

    assert available_actions(player, table) == {
        PlayerAction.CHECK,
        PlayerAction.RAISE,
        PlayerAction.ALL_IN,
    }


def test_available_actions_empty_for_folded_player() -> None:
    player = Player(id="p1", name="Alice", stack=100, folded=True)
    table = make_table(player, current_bet=10)

    assert available_actions(player, table) == set()


def test_available_actions_empty_for_all_in_player() -> None:
    player = Player(id="p1", name="Alice", stack=0, all_in=True)
    table = make_table(player, current_bet=10)

    assert available_actions(player, table) == set()
