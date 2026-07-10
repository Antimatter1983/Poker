"""Example: run a complete Texas Hold'em board deal."""

from collections.abc import Sequence

from _bootstrap import add_project_root_to_path

add_project_root_to_path()

from poker.cards import Card
from poker.engine import MatchEngine
from poker.player import Player
from poker.table import Table


def format_cards(cards: Sequence[Card]) -> str:
    return " ".join(str(card) for card in cards)


def main() -> None:
    players = [
        Player(id="p1", name="Alice", stack=1_000),
        Player(id="p2", name="Bob", stack=1_000),
    ]
    table = Table(table_id="table-1", players=players, small_blind=5, big_blind=10)
    engine = MatchEngine(table)

    engine.start_hand()
    print("After blinds and hole cards:")
    for player in table.players:
        print(
            f"  {player.name}: hand {format_cards(player.hand)}, "
            f"stack {player.stack}, current bet {player.current_bet}"
        )
    print(f"  Pot: {table.pot}")

    engine.deal_flop()
    print(f"Flop: {format_cards(table.community_cards[:3])}")

    engine.deal_turn()
    print(f"Turn: {table.community_cards[3]}")

    engine.deal_river()
    print(f"River: {table.community_cards[4]}")

    print("Final table state:")
    print(f"  Street: {table.street}")
    print(f"  Board: {format_cards(table.community_cards)}")
    print(f"  Pot: {table.pot}")


if __name__ == "__main__":
    main()
