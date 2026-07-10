"""Show basic player action availability states."""

from _bootstrap import add_project_root_to_path

add_project_root_to_path()

from poker.actions import available_actions
from poker.player import Player
from poker.table import Table


def action_names(player: Player, table: Table) -> list[str]:
    """Return sorted action names for readable example output."""

    return sorted(action.name for action in available_actions(player, table))


def show_state(label: str, player: Player, table: Table) -> None:
    """Print call amount and available actions for a state."""

    print(label)
    print(f"  call amount: {player.call_amount(table.current_bet)}")
    print(f"  actions: {', '.join(action_names(player, table)) or 'none'}")


def main() -> None:
    """Run the actions example."""

    owes_blind = Player(id="p1", name="Alice", stack=100, current_bet=5)
    owes_table = Table(table_id="actions-1", players=[owes_blind], current_bet=10)
    show_state("Player must add chips to match the blind", owes_blind, owes_table)

    matched = Player(id="p2", name="Bob", stack=100, current_bet=10)
    matched_table = Table(table_id="actions-2", players=[matched], current_bet=10)
    show_state("Player has already matched the current bet", matched, matched_table)

    all_in = Player(id="p3", name="Carol", stack=0, current_bet=25, all_in=True)
    all_in_table = Table(table_id="actions-3", players=[all_in], current_bet=25)
    show_state("Player is all-in", all_in, all_in_table)


if __name__ == "__main__":
    main()
