"""Match engine for simple Texas Hold'em hand flow."""

from poker.deck import Deck
from poker.table import Table


class MatchEngine:
    """Coordinates dealing and blind posting for a table."""

    def __init__(self, table: Table, deck: Deck | None = None) -> None:
        self.table = table
        self.deck = deck or Deck()

    def start_hand(self) -> None:
        """Start a new hand through blinds and hole-card dealing."""

        if len(self.table.players) < 2:
            raise ValueError("At least two players are required to start a hand")
        self.deck = Deck()
        self.deck.shuffle()
        self.table.reset_for_new_hand()
        self.post_blinds()
        self.deal_hole_cards()

    def post_blinds(self) -> None:
        """Post small and big blinds."""

        small_blind_player = self.table.player_at(self.table.button_position + 1)
        big_blind_player = self.table.player_at(self.table.button_position + 2)

        small_blind_paid = small_blind_player.bet(self.table.small_blind)
        big_blind_paid = big_blind_player.bet(self.table.big_blind)

        self.table.pot += small_blind_paid + big_blind_paid
        self.table.current_bet = max(small_blind_player.current_bet, big_blind_player.current_bet)
        self.table.street = "preflop"

    def deal_hole_cards(self) -> None:
        """Deal two private cards to each player."""

        for _ in range(2):
            for player in self.table.players:
                player.hand.append(self.deck.deal_one())

    def deal_flop(self) -> None:
        """Deal the three-card flop."""

        self.table.community_cards.extend(self.deck.deal_many(3))
        self.table.street = "flop"

    def deal_turn(self) -> None:
        """Deal the one-card turn."""

        self.table.community_cards.extend(self.deck.deal_many(1))
        self.table.street = "turn"

    def deal_river(self) -> None:
        """Deal the one-card river."""

        self.table.community_cards.extend(self.deck.deal_many(1))
        self.table.street = "river"
