"""Run a minimal Texas Hold'em deal from the command line."""

import sys
from pathlib import Path
from collections.abc import Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
    engine.deal_flop()
    engine.deal_turn()
    engine.deal_river()

    for player in table.players:
        print(f"{player.name}: {format_cards(player.hand)}")
    print(f"Flop: {format_cards(table.community_cards[:3])}")
    print(f"Turn: {table.community_cards[3]}")
    print(f"River: {table.community_cards[4]}")
    print(f"Pot: {table.pot}")


if __name__ == "__main__":
    main()
