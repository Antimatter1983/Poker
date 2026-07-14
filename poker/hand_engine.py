from time import monotonic

from .deck import Deck
from .player import Player
from .hand_evaluator import HandEvaluator, HandValue

FOLD = "FOLD"; CHECK = "CHECK"; CALL = "CALL"; BET = "BET"; RAISE = "RAISE"; ALL_IN = "ALL_IN"
PREFLOP = "PREFLOP"; FLOP = "FLOP"; TURN = "TURN"; RIVER = "RIVER"; SHOWDOWN = "SHOWDOWN"; FINISHED = "FINISHED"


class HandEngine:
    def __init__(self, player1: Player, player2: Player, small_blind_player_id: str, small_blind: int, big_blind: int):
        self.players = [player1, player2]
        self.small_blind_player_id = str(small_blind_player_id)
        self.small_blind = int(small_blind)
        self.big_blind = int(big_blind)
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.street = PREFLOP
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.current_player: Player | None = None
        self.finished = False
        self.winners: list[Player] = []
        self.hand_values: dict[str, HandValue] = {}
        self.finish_reason: str | None = None
        self.pending: set[str] = set()
        self.last_aggressor: str | None = None
        self.returned_chips = 0
        self.starting_stacks: dict[str, int] = {}
        self.finished_at: float | None = None

    @property
    def small_blind_player(self):
        return self._player(self.small_blind_player_id)

    @property
    def big_blind_player(self):
        return self.players[1] if self.players[0].player_id == self.small_blind_player_id else self.players[0]

    def start_hand(self, deck_cards: list | None = None) -> None:
        self._validate()
        self.deck = Deck()
        if deck_cards is None:
            self.deck.shuffle()
        else:
            self.deck.cards = list(deck_cards)
        self.community_cards = []
        self.pot = 0; self.street = PREFLOP; self.current_bet = self.big_blind; self.min_raise = self.big_blind
        self.finished = False; self.winners = []; self.hand_values = {}; self.finish_reason = None; self.returned_chips = 0; self.finished_at = None
        self.starting_stacks = {p.player_id: p.stack for p in self.players}
        for p in self.players: p.reset_for_new_hand()
        self.pot += self.small_blind_player.commit_chips(self.small_blind)
        self.pot += self.big_blind_player.commit_chips(self.big_blind)
        for _ in range(2):
            for p in self.players: p.receive_cards([self.deck.deal_one()])
        self.current_player = self.small_blind_player
        self.last_aggressor = self.big_blind_player.player_id
        self.pending = {p.player_id for p in self.players if p.can_act()}
        if not self.current_player.can_act():
            self.current_player = self.big_blind_player if self.big_blind_player.can_act() else None
            if self.current_player is None:
                self._runout_and_showdown()

    def legal_actions(self, player: Player | None = None) -> list[str]:
        if self.finished:
            return []
        p = player or self.current_player
        if not p or not p.can_act(): return []
        to_call = self.to_call(p)
        actions = [FOLD, ALL_IN]
        actions.append(CHECK if to_call == 0 else CALL)
        if self.max_bet_or_raise_to(p) is not None:
            actions.append(BET if self.current_bet == 0 else RAISE)
        return actions

    def to_call(self, player: Player) -> int:
        return max(0, self.current_bet - player.street_bet)

    def max_bet_or_raise_to(self, player: Player) -> int | None:
        """Maximum total street bet allowed by the tournament pot-limit rule.

        The project rule caps the raise/bet increase at the current pot size before
        the action. Returned value uses the engine convention: total amount committed
        by this player on the current street, not the extra chips to add.
        """
        if not player.can_act():
            return None
        if self.current_bet == 0:
            minimum = self.big_blind
        else:
            minimum = self.current_bet + self.min_raise
        maximum = player.street_bet + self.to_call(player) + min(player.stack - self.to_call(player), self.pot)
        maximum = min(maximum, player.street_bet + player.stack)
        return maximum if maximum >= minimum else None

    def act(self, action: str, amount: int | None = None) -> None:
        if self.finished: raise ValueError("Hand is already finished")
        p = self.current_player
        if p is None or not p.can_act(): raise ValueError("No player can act now")
        action = action.upper().replace("-", "_")
        if action == FOLD: self._fold(p); return
        if action == CHECK: self._check(p)
        elif action == CALL: self._call(p)
        elif action == BET: self._bet_or_raise(p, amount, is_raise=False)
        elif action == RAISE: self._bet_or_raise(p, amount, is_raise=True)
        elif action == ALL_IN: self._all_in(p)
        else: raise ValueError(f"Unknown action: {action}")
        p.last_action = action
        self._after_action(p)

    def _check(self, p):
        if self.to_call(p) != 0: raise ValueError("CHECK is not allowed: call is required")

    def _call(self, p):
        need = self.to_call(p)
        if need <= 0: raise ValueError("CALL is not allowed: nothing to call")
        self.pot += p.commit_chips(need)

    def _bet_or_raise(self, p, amount, is_raise):
        if amount is None: raise ValueError("Amount is required")
        amount = int(amount)
        if amount <= p.street_bet: raise ValueError("Amount must be greater than current street bet")
        if is_raise and self.current_bet == 0: raise ValueError("RAISE is not allowed without an existing bet")
        if not is_raise and self.current_bet != 0: raise ValueError("BET is not allowed after a bet exists")
        increase = amount - self.current_bet
        minimum = self.min_raise if is_raise else self.big_blind
        if increase < minimum: raise ValueError(f"Minimum {'raise' if is_raise else 'bet'} is {self.current_bet + minimum if is_raise else minimum}")
        maximum = self.max_bet_or_raise_to(p)
        if maximum is None or amount > maximum:
            raise ValueError(f"Maximum {'raise' if is_raise else 'bet'} is {maximum}")
        self.pot += p.commit_chips(amount - p.street_bet)
        self._set_aggressor(p, amount, increase)

    def _all_in(self, p):
        new_total = p.street_bet + p.stack
        old_bet = self.current_bet
        self.pot += p.commit_chips(p.stack)
        if new_total > old_bet:
            increase = new_total - old_bet
            # A short all-in raise does not reopen action; only a full raise resets pending responses.
            if old_bet == 0 or increase >= self.min_raise:
                self._set_aggressor(p, new_total, increase)
            else:
                self.current_bet = new_total

    def _set_aggressor(self, p, new_bet, increase):
        self.current_bet = new_bet
        self.min_raise = increase
        self.last_aggressor = p.player_id
        self.pending = {o.player_id for o in self.players if o is not p and o.can_act()}

    def _after_action(self, p):
        self.pending.discard(p.player_id)
        if self._everyone_all_in_or_done():
            self._runout_and_showdown(); return
        if not self.pending and self._bets_equal_for_active():
            if any(p.all_in for p in self.players if not p.folded):
                self._runout_and_showdown(); return
            self._advance_street(); return
        self.current_player = self._other(p)
        if not self.current_player.can_act():
            self._advance_street()

    def _advance_street(self):
        if self.street == RIVER:
            self._showdown(); return
        for p in self.players: p.reset_street_bet()
        self.current_bet = 0; self.min_raise = self.big_blind; self.last_aggressor = None
        if self.street == PREFLOP:
            self._burn(); self.community_cards.extend(self.deck.deal(3)); self.street = FLOP
        elif self.street == FLOP:
            self._burn(); self.community_cards.extend(self.deck.deal(1)); self.street = TURN
        elif self.street == TURN:
            self._burn(); self.community_cards.extend(self.deck.deal(1)); self.street = RIVER
        self.current_player = self.big_blind_player
        self.pending = {p.player_id for p in self.players if p.can_act()}
        if self._everyone_all_in_or_done(): self._runout_and_showdown()

    def _runout_and_showdown(self):
        while len(self.community_cards) < 5:
            self._burn()
            self.community_cards.extend(self.deck.deal(3 if len(self.community_cards) == 0 else 1))
        self._showdown()

    def _showdown(self):
        self._return_uncalled()
        self.street = SHOWDOWN
        active = [p for p in self.players if not p.folded]
        for p in active:
            self.hand_values[p.player_id] = HandEvaluator.evaluate(p.cards + self.community_cards)
        if self.hand_values[active[0].player_id] > self.hand_values[active[1].player_id]:
            self.winners = [active[0]]
        elif self.hand_values[active[1].player_id] > self.hand_values[active[0].player_id]:
            self.winners = [active[1]]
        else:
            self.winners = active[:]
        self._award_pot()
        self.finish_reason = "showdown"; self.street = FINISHED; self.finished = True; self.finished_at = monotonic()

    def _fold(self, p):
        p.folded = True; p.last_action = FOLD
        self._return_uncalled()
        winner = self._other(p); self.winners = [winner]; winner.stack += self.pot; self.pot = 0
        self.finish_reason = "fold"; self.street = FINISHED; self.finished = True; self.finished_at = monotonic()

    def _return_uncalled(self):
        a, b = self.players
        extra = abs(a.total_bet - b.total_bet)
        if extra:
            richer = a if a.total_bet > b.total_bet else b
            richer.stack += extra; richer.total_bet -= extra; self.pot -= extra; self.returned_chips += extra

    def _award_pot(self):
        if len(self.winners) == 1:
            self.winners[0].stack += self.pot
        else:
            share = self.pot // 2
            for w in self.winners: w.stack += share
            if self.pot % 2: self.small_blind_player.stack += 1
        self.pot = 0

    def _everyone_all_in_or_done(self):
        return all((not p.can_act()) for p in self.players if not p.folded)

    def _bets_equal_for_active(self):
        active = [p for p in self.players if not p.folded]
        return len({p.street_bet for p in active}) == 1

    def _burn(self): self.deck.deal_one()
    def _other(self, p): return self.players[1] if self.players[0] is p else self.players[0]
    def _player(self, pid):
        for p in self.players:
            if p.player_id == str(pid): return p
        raise ValueError(f"Unknown player id: {pid}")
    def _validate(self):
        if len({p.player_id for p in self.players}) != 2: raise ValueError("Players must have unique ids")
        if self.small_blind <= 0 or self.big_blind <= 0 or self.big_blind < self.small_blind: raise ValueError("Invalid blind sizes")
        self._player(self.small_blind_player_id)
