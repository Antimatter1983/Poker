"""Example: create a table and add players to it."""

from _bootstrap import add_project_root_to_path

add_project_root_to_path()

from poker.player import Player
from poker.table import Table


def main() -> None:
    table = Table(table_id="table-1", players=[], small_blind=5, big_blind=10)
    table.players.append(Player(id="p1", name="Alice", stack=1_000))
    table.players.append(Player(id="p2", name="Bob", stack=1_000))

    print(f"Table: {table.table_id}")
    print(f"Blinds: {table.small_blind}/{table.big_blind}")
    print("Players:")
    for position, player in enumerate(table.players):
        print(f"  Seat {position}: {player.name}, stack {player.stack}")


if __name__ == "__main__":
    main()
