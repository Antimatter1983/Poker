"""Example: run a small hand and print the game event journal."""

from _bootstrap import add_project_root_to_path

add_project_root_to_path()

from poker.actions import ActionRequest, PlayerAction
from poker.engine import MatchEngine
from poker.player import Player
from poker.table import Table


def main() -> None:
    players = [
        Player(id="p1", name="Alice", stack=1_000),
        Player(id="p2", name="Bob", stack=1_000),
        Player(id="p3", name="Charlie", stack=1_000),
    ]
    table = Table(table_id="table-1", players=players, small_blind=5, big_blind=10)
    engine = MatchEngine(table)

    engine.start_hand()
    engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CALL))
    engine.apply_action(ActionRequest(player_id="p2", action=PlayerAction.CALL))
    engine.apply_action(ActionRequest(player_id="p3", action=PlayerAction.CHECK))
    engine.deal_flop()
    engine.apply_action(ActionRequest(player_id="p2", action=PlayerAction.BET, amount=20))
    engine.apply_action(ActionRequest(player_id="p3", action=PlayerAction.FOLD))
    engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CALL))
    engine.deal_turn()
    engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CHECK))
    engine.apply_action(ActionRequest(player_id="p2", action=PlayerAction.ALL_IN))
    engine.deal_river()

    table.game_log.print_journal()


if __name__ == "__main__":
    main()
