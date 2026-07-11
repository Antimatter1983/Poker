from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from poker.contract import (
    ActionRequest,
    EngineResponse,
    EngineStatus,
    HandSetup,
    PlayerAction,
    PlayerState,
    Street,
)


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

request = ActionRequest(
    player_id="player-1",
    action=PlayerAction.CALL,
)

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

print(setup)
print(request)
print(response)
