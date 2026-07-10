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
    acting_player_index: int | None = None
    game_log: GameLog = field(default_factory=GameLog)

    def reset_for_new_hand(self) -> None:
        """Reset hand-specific table and player state."""

        self.pot = 0
        self.community_cards.clear()
        self.current_bet = 0
        self.street = "preflop"
        self.acting_player_index = None
        self.game_log.clear()
        for player in self.players:
            player.reset_for_new_hand()

    def player_at(self, position: int) -> Player:
        """Return a player by circular table position."""

        if not self.players:
            raise ValueError("Table has no players")
        return self.players[position % len(self.players)]

    def get_acting_player(self) -> Player | None:
        """Return the player whose turn it is, if action is currently assigned."""

        if self.acting_player_index is None:
            return None
        if not self.players:
            self.acting_player_index = None
            return None
        return self.player_at(self.acting_player_index)

    def set_first_actor(self) -> Player | None:
        """Assign and return the first player to act for the current street."""

        if not self.players:
            return self._clear_actor("No players are available to act")

        start_position = self._first_actor_search_start()
        player = self._find_next_actor_from(start_position, include_start=True)
        if player is None:
            return self._clear_actor("No players are available to act")

        self.acting_player_index = self.players.index(player)
        self._log_actor_event(
            "first_actor",
            f"{player.name} has the first action on {self.street}",
        )
        return player

    def move_to_next_actor(self) -> Player | None:
        """Advance action to the next eligible player, or clear the turn."""

        if self.acting_player_index is None:
            return self._clear_actor("No players remain to act")

        player = self._find_next_actor_from(self.acting_player_index + 1, include_start=True)
        if player is None:
            return self._clear_actor("No players remain to act")

        self.acting_player_index = self.players.index(player)
        self._log_actor_event("next_actor", f"Action passed to {player.name}")
        return player

    def _first_actor_search_start(self) -> int:
        if len(self.players) == 2:
            if self.street == "preflop":
                return self.button_position
            return self.button_position + 1

        if self.street == "preflop":
            return self.button_position + 3
        return self.button_position + 1

    def _find_next_actor_from(self, start_position: int, *, include_start: bool) -> Player | None:
        total_players = len(self.players)
        if total_players == 0:
            return None

        max_steps = total_players if include_start else total_players - 1
        for offset in range(max_steps):
            index = (start_position + offset) % total_players
            if index == self.acting_player_index and self.acting_player_index is not None:
                continue
            player = self.players[index]
            if self._can_player_act(player):
                return player
        return None

    def _can_player_act(self, player: Player) -> bool:
        in_hand = getattr(player, "in_hand", True)
        return bool(in_hand) and not player.folded and not player.all_in

    def _clear_actor(self, description: str) -> None:
        self.acting_player_index = None
        self._log_actor_event("no_actor", description)
        return None

    def _log_actor_event(self, event_type: str, description: str) -> None:
        self.game_log.add_event(
            event_type=event_type,
            description=description,
            street=self.street,
            pot=self.pot,
            current_bet=self.current_bet,
        )
