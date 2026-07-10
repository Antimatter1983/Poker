"""Match engine for simple Texas Hold'em hand flow."""

from poker.actions import (
    ActionNotAvailableError,
    ActionRequest,
    ActionResult,
    InvalidRaiseError,
    MissingAmountError,
    NonPositiveAmountError,
    PlayerAction,
    PlayerNotFoundError,
    StackExceededError,
    available_actions,
)
from poker.deck import Deck
from poker.player import Player
from poker.table import Table


class MatchEngine:
    """Coordinates dealing, blind posting, and single-player actions."""

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
        self._log_event("hand_start", f"Hand started at table {self.table.table_id}")
        self.post_blinds()
        self.deal_hole_cards()

    def post_blinds(self) -> None:
        """Post small and big blinds."""

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
        actions = available_actions(player, self.table)
        if request.action not in actions:
            raise ActionNotAvailableError(
                f"Action {request.action.name} is not available for player {request.player_id}"
            )

        amount_paid = 0
        if request.action is PlayerAction.FOLD:
            player.folded = True
        elif request.action is PlayerAction.CHECK:
            self._ensure_check_allowed(player)
        elif request.action is PlayerAction.CALL:
            amount_paid = player.bet(player.call_amount(self.table.current_bet))
            self.table.pot += amount_paid
        elif request.action is PlayerAction.BET:
            amount_paid = self._apply_bet(player, request.amount)
        elif request.action is PlayerAction.RAISE:
            amount_paid = self._apply_raise(player, request.amount)
        elif request.action is PlayerAction.ALL_IN:
            amount_paid = player.bet(player.stack)
            self.table.pot += amount_paid
            if player.current_bet > self.table.current_bet:
                self.table.current_bet = player.current_bet

        player.last_action = request.action
        self._log_event(
            request.action.name.lower(),
            self._describe_action(player, request.action, amount_paid),
        )
        return ActionResult(
            player_id=player.id,
            action=request.action,
            amount_paid=amount_paid,
            player_stack=player.stack,
            player_current_bet=player.current_bet,
            table_current_bet=self.table.current_bet,
            pot=self.table.pot,
        )

    def _find_player(self, player_id: str) -> Player:
        for player in self.table.players:
            if player.id == player_id:
                return player
        raise PlayerNotFoundError(
            f"Player {player_id} was not found at table {self.table.table_id}"
        )

    def _ensure_check_allowed(self, player: Player) -> None:
        if player.call_amount(self.table.current_bet) != 0:
            raise ActionNotAvailableError(f"Player {player.id} cannot check while facing a bet")

    def _require_positive_amount(self, amount: int | None) -> int:
        if amount is None:
            raise MissingAmountError("Action amount is required")
        if amount <= 0:
            raise NonPositiveAmountError("Action amount must be positive")
        return amount

    def _apply_bet(self, player: Player, requested_amount: int | None) -> int:
        if self.table.current_bet != 0:
            raise ActionNotAvailableError("Bet is not available after a bet already exists")
        amount = self._require_positive_amount(requested_amount)
        if amount > player.stack:
            raise StackExceededError("Bet amount cannot exceed player stack")

        amount_paid = player.bet(amount)
        self.table.pot += amount_paid
        self.table.current_bet = player.current_bet
        return amount_paid

    def _apply_raise(self, player: Player, requested_amount: int | None) -> int:
        if self.table.current_bet == 0:
            raise ActionNotAvailableError("Raise is not available before a bet exists")
        amount = self._require_positive_amount(requested_amount)
        if amount <= self.table.current_bet:
            raise InvalidRaiseError("Raise amount must be greater than the current table bet")

        additional_amount = amount - player.current_bet
        if additional_amount <= 0:
            raise InvalidRaiseError("Raise amount must exceed the player's current bet")
        if additional_amount > player.stack:
            raise StackExceededError("Raise amount cannot exceed player stack")

        amount_paid = player.bet(additional_amount)
        self.table.pot += amount_paid
        self.table.current_bet = player.current_bet
        return amount_paid

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

    def deal_turn(self) -> None:
        """Deal the one-card turn."""

        self._reset_betting_round()
        self.table.community_cards.extend(self.deck.deal_many(1))
        self.table.street = "turn"
        self._log_event("turn", f"Turn opened: {self.table.community_cards[3]}")

    def deal_river(self) -> None:
        """Deal the one-card river."""

        self._reset_betting_round()
        self.table.community_cards.extend(self.deck.deal_many(1))
        self.table.street = "river"
        self._log_event("river", f"River opened: {self.table.community_cards[4]}")

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
