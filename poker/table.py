"""Table state for a Texas Hold'em hand."""

from dataclasses import dataclass, field

from poker.cards import Card
from poker.game_log import GameLog
from poker.player import Player


@dataclass(slots=True)
class Table:
    """A poker table with players and hand state."""

    table_id: str
    players: list[Player]
    button_position: int = 0
    small_blind: int = 5
    big_blind: int = 10
    pot: int = 0
    community_cards: list[Card] = field(default_factory=list)
    current_bet: int = 0
    street: str = "pre_hand"
    game_log: GameLog = field(default_factory=GameLog)

    def reset_for_new_hand(self) -> None:
        """Reset hand-specific table and player state."""

        self.pot = 0
        self.community_cards.clear()
        self.current_bet = 0
        self.street = "preflop"
        self.game_log.clear()
        for player in self.players:
            player.reset_for_new_hand()

    def player_at(self, position: int) -> Player:
        """Return a player by circular table position."""

        if not self.players:
            raise ValueError("Table has no players")
        return self.players[position % len(self.players)]
