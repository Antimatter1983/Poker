import pytest

from poker.actions import (
    ActionRequest,
    MissingAmountError,
    NonPositiveAmountError,
    PlayerAction,
    StackExceededError,
)
from poker.betting import BettingActionProcessor
from poker.player import Player
from poker.table import Table


def make_table(player: Player, *, current_bet: int = 0, pot: int = 0) -> Table:
    return Table(table_id="table-1", players=[player], current_bet=current_bet, pot=pot)


def apply_action(player: Player, action: PlayerAction, *, amount: int | None = None, current_bet: int = 0, pot: int = 0):
    table = make_table(player, current_bet=current_bet, pot=pot)
    request = ActionRequest(player_id=player.id, action=action, amount=amount)
    result = BettingActionProcessor().apply(table, player, request)
    return table, result


def test_processor_fold_marks_player_without_chips_or_pot_changes() -> None:
    player = Player(id="p1", name="Alice", stack=100)

    table, result = apply_action(player, PlayerAction.FOLD, pot=25)

    assert player.folded is True
    assert player.stack == 100
    assert table.pot == 25
    assert result.amount_paid == 0
    assert player.last_action is PlayerAction.FOLD


def test_processor_check_when_no_call_is_required() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=10)

    table, result = apply_action(player, PlayerAction.CHECK, current_bet=10, pot=20)

    assert player.stack == 100
    assert table.pot == 20
    assert result.player_current_bet == 10
    assert player.last_action is PlayerAction.CHECK


def test_processor_call_pays_call_amount() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=5)

    table, result = apply_action(player, PlayerAction.CALL, current_bet=20, pot=30)

    assert result.amount_paid == 15
    assert player.stack == 85
    assert player.current_bet == 20
    assert table.pot == 45
    assert player.all_in is False


def test_processor_partial_call_sets_all_in() -> None:
    player = Player(id="p1", name="Alice", stack=8, current_bet=2)

    table, result = apply_action(player, PlayerAction.CALL, current_bet=20, pot=30)

    assert result.amount_paid == 8
    assert player.stack == 0
    assert player.current_bet == 10
    assert player.all_in is True
    assert table.pot == 38


def test_processor_bet_creates_current_bet() -> None:
    player = Player(id="p1", name="Alice", stack=100)

    table, result = apply_action(player, PlayerAction.BET, amount=25)

    assert result.amount_paid == 25
    assert player.stack == 75
    assert player.current_bet == 25
    assert table.current_bet == 25
    assert table.pot == 25


def test_processor_raise_treats_amount_as_new_full_bet() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=10)

    table, result = apply_action(player, PlayerAction.RAISE, amount=50, current_bet=20, pot=40)

    assert result.amount_paid == 40
    assert player.stack == 60
    assert player.current_bet == 50
    assert table.current_bet == 50
    assert table.pot == 80


def test_processor_all_in_commits_remaining_stack_and_updates_current_bet() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=10)

    table, result = apply_action(player, PlayerAction.ALL_IN, current_bet=20, pot=40)

    assert result.amount_paid == 100
    assert player.stack == 0
    assert player.current_bet == 110
    assert player.all_in is True
    assert table.current_bet == 110
    assert table.pot == 140


@pytest.mark.parametrize("amount, error", [(None, MissingAmountError), (0, NonPositiveAmountError), (-1, NonPositiveAmountError)])
def test_processor_rejects_invalid_amount(amount: int | None, error: type[Exception]) -> None:
    player = Player(id="p1", name="Alice", stack=100)
    table = make_table(player)

    with pytest.raises(error):
        BettingActionProcessor().apply(
            table,
            player,
            ActionRequest(player_id="p1", action=PlayerAction.BET, amount=amount),
        )


def test_processor_rejects_bet_greater_than_stack() -> None:
    player = Player(id="p1", name="Alice", stack=100)
    table = make_table(player)

    with pytest.raises(StackExceededError):
        BettingActionProcessor().apply(
            table,
            player,
            ActionRequest(player_id="p1", action=PlayerAction.BET, amount=101),
        )
