"""Demonstrate explicit turn-order management in the poker engine."""

from _bootstrap import add_project_root_to_path

add_project_root_to_path()

from poker.actions import ActionRequest, PlayerAction
from poker.engine import MatchEngine
from poker.player import Player
from poker.table import Table


def player_label(table: Table, index: int) -> str:
    player = table.player_at(index)
    return f"seat {index % len(table.players)}: {player.name} ({player.id})"


def acting_label(table: Table) -> str:
    player = table.get_acting_player()
    if player is None:
        return "nobody"
    return f"{player.name} ({player.id})"


players = [
    Player(id="p1", name="Alice", stack=1_000),
    Player(id="p2", name="Bob", stack=1_000),
    Player(id="p3", name="Charlie", stack=1_000),
]
table = Table(
    table_id="turn-order-demo",
    players=players,
    button_position=0,
    small_blind=5,
    big_blind=10,
)
engine = MatchEngine(table)
engine.start_hand()

print("Positions")
print(f"Button:      {player_label(table, table.button_position)}")
print(f"Small blind: {player_label(table, table.button_position + 1)}")
print(f"Big blind:   {player_label(table, table.button_position + 2)}")
print()

print(f"First actor: {acting_label(table)}")

for request in [
    ActionRequest(player_id="p1", action=PlayerAction.CALL),
    ActionRequest(player_id="p2", action=PlayerAction.CALL),
    ActionRequest(player_id="p3", action=PlayerAction.CHECK),
]:
    result = engine.apply_action(request)
    print(f"{result.player_id} {result.action.name.lower()} -> next actor: {acting_label(table)}")

print()
print("GameLog")
for event in table.game_log.events():
    if event.event_type in {"first_actor", "next_actor", "no_actor"}:
        print(f"#{event.number} [{event.street}] {event.event_type}: {event.description}")
