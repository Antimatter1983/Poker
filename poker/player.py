from .card import Card


class Player:
    def __init__(self, player_id: str, starting_stack: int):
        if not player_id:
            raise ValueError("player_id is required")
        if starting_stack < 0:
            raise ValueError("starting_stack cannot be negative")
        self.player_id = str(player_id)
        self.starting_stack = int(starting_stack)
        self.stack = int(starting_stack)
        self.cards: list[Card] = []
        self.street_bet = 0
        self.total_bet = 0
        self.folded = False
        self.all_in = self.stack == 0
        self.last_action: str | None = None

    def receive_cards(self, cards: list[Card]) -> None:
        self.cards.extend(cards)

    def commit_chips(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("Cannot commit a negative amount")
        paid = min(amount, self.stack)
        self.stack -= paid
        self.street_bet += paid
        self.total_bet += paid
        if self.stack == 0:
            self.all_in = True
        return paid

    def reset_street_bet(self) -> None:
        self.street_bet = 0
        self.last_action = None

    def reset_for_new_hand(self) -> None:
        self.cards = []
        self.street_bet = 0
        self.total_bet = 0
        self.folded = False
        self.all_in = self.stack == 0
        self.last_action = None

    def clear_cards(self) -> None:
        self.cards = []

    def can_act(self) -> bool:
        return not self.folded and not self.all_in
