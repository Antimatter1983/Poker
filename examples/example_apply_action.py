from _bootstrap import add_project_root_to_path

add_project_root_to_path()

from poker.actions import ActionRequest, PlayerAction
from poker.engine import MatchEngine
from poker.player import Player
from poker.table import Table


def print_state(label: str, table: Table) -> None:
    print(label)
    print(f"Table: current_bet={table.current_bet}, pot={table.pot}, street={table.street}")
    for player in table.players:
        print(
            "Player "
            f"{player.id}: stack={player.stack}, current_bet={player.current_bet}, "
            f"folded={player.folded}, all_in={player.all_in}, last_action={player.last_action}"
        )


alice = Player(id="p1", name="Alice", stack=100)
bob = Player(id="p2", name="Bob", stack=100, current_bet=10)
table = Table(table_id="example-table", players=[alice, bob], pot=10, current_bet=10, street="preflop")
engine = MatchEngine(table)
request = ActionRequest(player_id="p1", action=PlayerAction.CALL)

print_state("Before action", table)
print(f"\nAction: {request}")
result = engine.apply_action(request)
print(f"ActionResult: {result}\n")
print_state("After action", table)
