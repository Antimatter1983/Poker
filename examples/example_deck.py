"""Example: create, shuffle, and deal cards from a deck."""

from _bootstrap import add_project_root_to_path

add_project_root_to_path()

from poker.deck import Deck


def main() -> None:
    deck = Deck()
    print(f"New deck contains {len(deck)} cards.")

    deck.shuffle()
    dealt_cards = deck.deal_many(5)
    print("Dealt cards:", " ".join(str(card) for card in dealt_cards))
    print(f"Cards left in deck: {len(deck)}")


if __name__ == "__main__":
    main()
