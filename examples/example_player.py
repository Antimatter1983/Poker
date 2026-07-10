"""Example: create a player and print player state."""

from _bootstrap import add_project_root_to_path

add_project_root_to_path()

from poker.player import Player


def main() -> None:
    player = Player(id="p1", name="Alice", stack=1_000)
    paid = player.bet(25)

    print(f"Player: {player.name} ({player.id})")
    print(f"Paid bet: {paid}")
    print(f"Stack: {player.stack}")
    print(f"Current bet: {player.current_bet}")
    print(f"All-in: {player.all_in}")


if __name__ == "__main__":
    main()
