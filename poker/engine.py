"""Match engine for simple Texas Hold'em hand flow."""

from poker.actions import (
    ActionNotAvailableError,
    ActionRequest,
    ActionResult,
    PlayerAction,
    PlayerNotFoundError,
    available_actions,
)
from poker.betting import BettingActionProcessor
from poker.deck import Deck
from poker.player import Player
from poker.table import Table


class MatchEngine:
    """Coordinates dealing, blind posting, and single-player actions."""

    def __init__(self, table: Table, deck: Deck | None = None) -> None:
        self.table = table
        self.deck = deck or Deck()
        self.betting_action_processor = BettingActionProcessor()

    def start_hand(self) -> None:
        """Start a new hand through blinds and hole-card dealing."""

        if len(self.table.players) < 2:
            raise ValueError("At least two players are required to start a hand")
        self.deck = Deck()
        self.deck.shuffle()
        self.table.reset_for_new_hand()
        self._log_event("hand_start", f"Hand started at table {self.table.table_id}")
        self.post_blinds()
        self.deal_hole_cards()
        self.table.set_first_actor()

    def post_blinds(self) -> None:
        """Post small and big blinds."""

        if len(self.table.players) == 2:
            small_blind_player = self.table.player_at(self.table.button_position)
            big_blind_player = self.table.player_at(self.table.button_position + 1)
        else:
            small_blind_player = self.table.player_at(self.table.button_position + 1)
            big_blind_player = self.table.player_at(self.table.button_position + 2)

        small_blind_paid = small_blind_player.bet(self.table.small_blind)
        big_blind_paid = big_blind_player.bet(self.table.big_blind)

        self.table.pot += small_blind_paid
        self.table.current_bet = small_blind_player.current_bet
        self.table.street = "preflop"
        self._log_event(
            "small_blind",
            f"{small_blind_player.name} posted small blind {small_blind_paid}",
        )

        self.table.pot += big_blind_paid
        self.table.current_bet = max(
            small_blind_player.current_bet,
            big_blind_player.current_bet,
        )
        self._log_event(
            "big_blind",
            f"{big_blind_player.name} posted big blind {big_blind_paid}",
        )

    def apply_action(self, request: ActionRequest) -> ActionResult:
        """Apply one validated player action and return the resulting state.

        This method intentionally handles only one action. It does not advance
        action order, complete betting rounds, create side pots, or end hands.
        """

        player = self._find_player(request.player_id)
        self._ensure_player_turn(player)
        actions = available_actions(player, self.table)
        if request.action not in actions:
            raise ActionNotAvailableError(
                f"Action {request.action.name} is not available for player {request.player_id}"
            )

        result = self.betting_action_processor.apply(self.table, player, request)
        self._log_event(
            request.action.name.lower(),
            self._describe_action(player, request.action, result.amount_paid),
        )
        self.table.move_to_next_actor()
        return result

    def _ensure_player_turn(self, player: Player) -> None:
        acting_player = self.table.get_acting_player()
        if acting_player is None:
            return
        if acting_player.id != player.id:
            raise ActionNotAvailableError(
                f"It is {acting_player.name}'s turn to act, not player {player.id}"
            )

    def _find_player(self, player_id: str) -> Player:
        for player in self.table.players:
            if player.id == player_id:
                return player
        raise PlayerNotFoundError(
            f"Player {player_id} was not found at table {self.table.table_id}"
        )

    def deal_hole_cards(self) -> None:
        """Deal two private cards to each player."""

        for _ in range(2):
            for player in self.table.players:
                player.hand.append(self.deck.deal_one())
        for player in self.table.players:
            cards = " ".join(str(card) for card in player.hand)
            self._log_event("hole_cards", f"Dealt hole cards to {player.name}: {cards}")

    def deal_flop(self) -> None:
        """Deal the three-card flop."""

        self._reset_betting_round()
        self.table.community_cards.extend(self.deck.deal_many(3))
        self.table.street = "flop"
        cards = " ".join(str(card) for card in self.table.community_cards[:3])
        self._log_event("flop", f"Flop opened: {cards}")
        self.table.set_first_actor()

    def deal_turn(self) -> None:
        """Deal the one-card turn."""

        self._reset_betting_round()
        self.table.community_cards.extend(self.deck.deal_many(1))
        self.table.street = "turn"
        self._log_event("turn", f"Turn opened: {self.table.community_cards[3]}")
        self.table.set_first_actor()

    def deal_river(self) -> None:
        """Deal the one-card river."""

        self._reset_betting_round()
        self.table.community_cards.extend(self.deck.deal_many(1))
        self.table.street = "river"
        self._log_event("river", f"River opened: {self.table.community_cards[4]}")
        self.table.set_first_actor()

    def _reset_betting_round(self) -> None:
        """Reset per-street betting state before opening a new board card."""

        self.table.current_bet = 0
        for player in self.table.players:
            player.current_bet = 0

    def _log_event(self, event_type: str, description: str) -> None:
        """Record a table-state event in the game log."""

        self.table.game_log.add_event(
            event_type=event_type,
            description=description,
            street=self.table.street,
            pot=self.table.pot,
            current_bet=self.table.current_bet,
        )

    def _describe_action(
        self, player: Player, action: PlayerAction, amount_paid: int
    ) -> str:
        """Build a readable description for a player action event."""

        action_names = {
            PlayerAction.FOLD: "Fold",
            PlayerAction.CHECK: "Check",
            PlayerAction.CALL: "Call",
            PlayerAction.BET: "Bet",
            PlayerAction.RAISE: "Raise",
            PlayerAction.ALL_IN: "All-in",
        }
        description = f"{player.name}: {action_names[action]}"
        if action in {
            PlayerAction.CALL,
            PlayerAction.BET,
            PlayerAction.RAISE,
            PlayerAction.ALL_IN,
        }:
            description += f" {amount_paid}"
        return description
