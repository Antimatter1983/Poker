import pytest

from poker.actions import (
    ActionNotAvailableError,
    ActionRequest,
    PlayerAction,
    PlayerNotFoundError,
    StackExceededError,
)
from poker.engine import MatchEngine
from poker.player import Player
from poker.table import Table


def make_engine(*players: Player, current_bet: int = 0, pot: int = 0) -> MatchEngine:
    table = Table(table_id="table-1", players=list(players), current_bet=current_bet, pot=pot)
    return MatchEngine(table)


def test_apply_fold_marks_player_without_chips_or_pot_changes() -> None:
    player = Player(id="p1", name="Alice", stack=100)
    engine = make_engine(player, current_bet=0, pot=25)

    result = engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.FOLD))

    assert player.folded is True
    assert player.stack == 100
    assert engine.table.pot == 25
    assert result.amount_paid == 0
    assert player.last_action is PlayerAction.FOLD


def test_apply_check_when_no_call_is_required() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=10)
    engine = make_engine(player, current_bet=10, pot=20)

    result = engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CHECK))

    assert player.stack == 100
    assert engine.table.pot == 20
    assert result.player_current_bet == 10
    assert player.last_action is PlayerAction.CHECK


def test_apply_call_pays_call_amount() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=5)
    engine = make_engine(player, current_bet=20, pot=30)

    result = engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CALL))

    assert result.amount_paid == 15
    assert player.stack == 85
    assert player.current_bet == 20
    assert engine.table.pot == 45
    assert player.all_in is False


def test_apply_partial_call_sets_all_in() -> None:
    player = Player(id="p1", name="Alice", stack=8, current_bet=2)
    engine = make_engine(player, current_bet=20, pot=30)

    result = engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CALL))

    assert result.amount_paid == 8
    assert player.stack == 0
    assert player.current_bet == 10
    assert player.all_in is True
    assert engine.table.pot == 38


def test_apply_bet_creates_current_bet() -> None:
    player = Player(id="p1", name="Alice", stack=100)
    engine = make_engine(player, current_bet=0, pot=0)

    result = engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.BET, amount=25))

    assert result.amount_paid == 25
    assert player.stack == 75
    assert player.current_bet == 25
    assert engine.table.current_bet == 25
    assert engine.table.pot == 25


def test_apply_raise_treats_amount_as_new_full_bet() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=10)
    engine = make_engine(player, current_bet=20, pot=40)

    result = engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.RAISE, amount=50))

    assert result.amount_paid == 40
    assert player.stack == 60
    assert player.current_bet == 50
    assert engine.table.current_bet == 50
    assert engine.table.pot == 80


def test_apply_all_in_commits_remaining_stack_and_updates_current_bet() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=10)
    engine = make_engine(player, current_bet=20, pot=40)

    result = engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.ALL_IN))

    assert result.amount_paid == 100
    assert player.stack == 0
    assert player.current_bet == 110
    assert player.all_in is True
    assert engine.table.current_bet == 110
    assert engine.table.pot == 140


def test_apply_check_is_forbidden_when_call_is_required() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=5)
    engine = make_engine(player, current_bet=10)

    with pytest.raises(ActionNotAvailableError):
        engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CHECK))


def test_apply_bet_is_forbidden_when_bet_already_exists() -> None:
    player = Player(id="p1", name="Alice", stack=100, current_bet=10)
    engine = make_engine(player, current_bet=10)

    with pytest.raises(ActionNotAvailableError):
        engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.BET, amount=20))


def test_apply_action_rejects_unknown_player() -> None:
    player = Player(id="p1", name="Alice", stack=100)
    engine = make_engine(player)

    with pytest.raises(PlayerNotFoundError):
        engine.apply_action(ActionRequest(player_id="missing", action=PlayerAction.FOLD))


def test_apply_bet_rejects_amount_greater_than_stack() -> None:
    player = Player(id="p1", name="Alice", stack=100)
    engine = make_engine(player)

    with pytest.raises(StackExceededError):
        engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.BET, amount=101))
