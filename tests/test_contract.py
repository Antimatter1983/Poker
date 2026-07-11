from __future__ import annotations

import pytest

from poker.contract import (
    ActionRequest,
    EngineResponse,
    EngineStatus,
    FinishReason,
    HandSetup,
    PlayerAction,
    PlayerState,
    Street,
)
from poker.hand_engine import HandEngine


def test_player_action_enum_values() -> None:
    assert [action.name for action in PlayerAction] == [
        "FOLD",
        "CHECK",
        "CALL",
        "BET",
        "RAISE",
        "ALL_IN",
    ]


def test_engine_status_enum_values() -> None:
    assert [status.name for status in EngineStatus] == [
        "WAITING_FOR_ACTION",
        "HAND_FINISHED",
    ]


def test_street_enum_values() -> None:
    assert [street.name for street in Street] == [
        "PREFLOP",
        "FLOP",
        "TURN",
        "RIVER",
        "SHOWDOWN",
        "FINISHED",
    ]


def test_finish_reason_enum_values() -> None:
    assert [reason.name for reason in FinishReason] == ["FOLD", "SHOWDOWN"]


def test_create_hand_setup() -> None:
    setup = HandSetup(
        player1_id="player-1",
        player2_id="player-2",
        player1_stack=1000,
        player2_stack=1000,
        small_blind_player_id="player-1",
        big_blind_player_id="player-2",
        small_blind=10,
        big_blind=20,
    )

    assert setup.player1_id == "player-1"
    assert setup.big_blind == 20


def test_create_action_request() -> None:
    request = ActionRequest(
        player_id="player-1",
        action=PlayerAction.BET,
        amount=100,
    )

    assert request.player_id == "player-1"
    assert request.action is PlayerAction.BET
    assert request.amount == 100


def test_create_player_state() -> None:
    state = PlayerState(
        player_id="player-1",
        starting_stack=1000,
        stack=980,
        cards=["As", "Kh"],
        street_bet=20,
        total_bet=20,
        folded=False,
        all_in=False,
        last_action=PlayerAction.CALL,
        is_small_blind=True,
        is_big_blind=False,
        is_button=True,
    )

    assert state.cards == ["As", "Kh"]
    assert state.is_button is True


def test_create_engine_response() -> None:
    player1 = PlayerState(
        player_id="player-1",
        starting_stack=1000,
        stack=990,
        cards=["As", "Kh"],
        street_bet=10,
        total_bet=10,
        folded=False,
        all_in=False,
        last_action=None,
        is_small_blind=True,
        is_big_blind=False,
        is_button=True,
    )
    player2 = PlayerState(
        player_id="player-2",
        starting_stack=1000,
        stack=980,
        cards=["Qc", "Qd"],
        street_bet=20,
        total_bet=20,
        folded=False,
        all_in=False,
        last_action=None,
        is_small_blind=False,
        is_big_blind=True,
        is_button=False,
    )
    response = EngineResponse(
        status=EngineStatus.WAITING_FOR_ACTION,
        street=Street.PREFLOP,
        acting_player_id="player-1",
        available_actions=[PlayerAction.FOLD, PlayerAction.CALL, PlayerAction.RAISE],
        call_amount=10,
        minimum_bet=None,
        minimum_raise_to=40,
        pot=30,
        current_bet=20,
        board=[],
        players=[player1, player2],
        winner_ids=[],
        finish_reason=None,
    )

    assert response.players == [player1, player2]
    assert response.status is EngineStatus.WAITING_FOR_ACTION


def test_hand_engine_public_methods_exist() -> None:
    engine = HandEngine()

    assert callable(engine.start)
    assert callable(engine.apply_action)


def test_hand_engine_start_raises_not_implemented_error() -> None:
    engine = HandEngine()
    setup = HandSetup(
        player1_id="player-1",
        player2_id="player-2",
        player1_stack=1000,
        player2_stack=1000,
        small_blind_player_id="player-1",
        big_blind_player_id="player-2",
        small_blind=10,
        big_blind=20,
    )

    with pytest.raises(NotImplementedError):
        engine.start(setup)


def test_hand_engine_apply_action_raises_not_implemented_error() -> None:
    engine = HandEngine()
    request = ActionRequest(player_id="player-1", action=PlayerAction.CALL)

    with pytest.raises(NotImplementedError):
        engine.apply_action(request)
