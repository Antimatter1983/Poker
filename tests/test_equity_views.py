from pathlib import Path
from types import SimpleNamespace

import pytest

from poker.card import Card
from web import game_store, views


class FakeLobby:
    status = game_store.RUNNING
    hand_state = "playing"
    hand_count = 1
    game = None
    next_hand_actor_name = None
    player_names = ["Alice"]

    def __init__(self, board):
        player = SimpleNamespace(cards=[Card("A", "S"), Card("K", "S")], street_bet=0, player_id="Alice", stack=100)
        bot = SimpleNamespace(cards=[Card("2", "C"), Card("3", "D")], street_bet=0, player_id="Bot", stack=100)
        engine = SimpleNamespace(
            community_cards=[Card(code[0], code[1]) for code in board],
            finished=False,
            current_player=None,
            pot=0,
            small_blind_player=player,
            to_call=lambda player: 0,
        )
        self.table = SimpleNamespace(player=player, bot=bot, engine=engine)

    def table_for(self, player_name):
        return self.table

    def race_standings(self):
        return []

    def can_advance_hand(self):
        return False

    def player_can_advance_hand(self, player_name):
        return False

    def finished_player_count(self, completed_hand_number):
        return 0

    def unfinished_player_names(self):
        return []


@pytest.mark.parametrize("board", [["QS", "7S", "2D"], ["QS", "7S", "2D", "3C"], ["QS", "7S", "2D", "3C", "4H"]])
def test_tournament_context_does_not_call_equity_after_flop(monkeypatch, board):
    monkeypatch.setattr(views, "calculate_equity", lambda *a, **k: pytest.fail("equity must not be called postflop"))

    context = views._tournament_context(FakeLobby(board), "Alice")

    assert context["equity"] is None


def test_tournament_context_uses_preflop_equity_table(monkeypatch):
    called = {"value": False}

    def fake_equity(cards):
        called["value"] = True
        assert [str(card) for card in cards] == ["AS", "KS"]
        return "table-value"

    monkeypatch.setattr(views, "calculate_equity", fake_equity)

    context = views._tournament_context(FakeLobby([]), "Alice")

    assert called["value"]
    assert context["equity"] == "table-value"


def test_showdown_template_has_no_equity_block():
    template = Path("web/templates/web/hand_results.html").read_text()

    assert "equity" not in template
    assert "Шанс выигрыша" not in template
