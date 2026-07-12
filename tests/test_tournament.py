from poker.hand_engine import BET, CALL, CHECK, RAISE
from poker.bot import CallBot
from poker.tournament import ACTION_TIMEOUT_SECONDS, HAND_COUNT, STARTING_STACK, Tournament


def test_admin_created_tournament_builds_one_bot_table_per_player():
    tournament = Tournament.create_by_admin("admin", "daily", ["alice", "bob"])

    assert tournament.hand_count == HAND_COUNT
    assert tournament.action_timeout_seconds == ACTION_TIMEOUT_SECONDS
    assert [table.player.stack for table in tournament.tables] == [STARTING_STACK, STARTING_STACK]
    assert [table.bot.player_id for table in tournament.tables] == ["bot:alice", "bot:bob"]


def test_all_tables_receive_identical_deal_for_player_bot_and_board():
    tournament = Tournament.create_by_admin("admin", "daily", ["alice", "bob", "carol"])
    tournament.start_next_hand()

    for player_id in ["alice", "bob", "carol"]:
        tournament.submit_player_action(player_id, CALL)

    first = tournament.tables[0].engine
    for table in tournament.tables[1:]:
        assert table.engine.players[0].cards == first.players[0].cards
        assert table.engine.players[1].cards == first.players[1].cards
        assert table.engine.community_cards == first.community_cards
        assert table.engine.street == first.street



class RecordingCallBot(CallBot):
    def __init__(self):
        self.actions = []

    def choose_action(self, engine, bot):
        choice = super().choose_action(engine, bot)
        self.actions.append(choice[0])
        return choice


def test_call_bot_only_checks_or_calls():
    bot = RecordingCallBot()
    tournament = Tournament.create_by_admin("admin", "daily", ["alice"], bot_policy=bot)
    tournament.start_next_hand()

    table = tournament.tables[0]
    tournament.submit_player_action("alice", CALL)
    assert bot.actions[-1] == CHECK

    tournament.submit_player_action("alice", BET, 10)
    assert CALL in bot.actions


def test_pot_limit_rule_caps_bets_and_raises_to_current_pot_size():
    tournament = Tournament.create_by_admin("admin", "daily", ["alice"])
    tournament.start_next_hand()
    table = tournament.tables[0]

    # Preflop pot is 15, Alice has posted 5 and needs 5 to call, so the
    # largest legal raise increase is 15 and the largest raise-to amount is 25.
    assert table.engine.max_bet_or_raise_to(table.player) == 25
    try:
        tournament.submit_player_action("alice", RAISE, 26)
        assert False
    except ValueError as exc:
        assert "Maximum raise" in str(exc)


def test_standings_and_winner_after_configured_hands():
    tournament = Tournament.create_by_admin("admin", "daily", ["alice", "bob"], hand_count=1)
    tournament.start_next_hand()
    tournament.submit_player_action("alice", CALL)
    tournament.submit_player_action("bob", CALL)

    assert tournament.hand_number == 1
    assert len(tournament.winner_ids()) >= 1


def finish_player_hand(tournament, player_id):
    table = next(table for table in tournament.tables if table.player.player_id == player_id)
    while not table.engine.finished:
        action = CALL if CALL in table.engine.legal_actions(table.player) else CHECK
        tournament.submit_player_action(player_id, action)


def test_lobby_next_hand_waits_five_seconds_after_all_tables_finish(monkeypatch):
    from web import game_store

    now = 100.0
    monkeypatch.setattr(game_store, "monotonic", lambda: now)
    lobby = game_store.LobbyTournament("code", "Daily", "admin", hand_count=2, player_names=["alice"])
    lobby.start()
    finish_player_hand(lobby.game, "alice")
    assert lobby.all_hands_finished()

    lobby.advance_finished_hands()
    assert lobby.game.hand_number == 1
    assert not lobby.can_advance_hand()
    assert lobby.seconds_until_next_hand_ready() == 5

    now = 104.9
    assert not lobby.can_advance_hand()
    assert lobby.game.hand_number == 1

    now = 105.0
    assert lobby.can_advance_hand()
    lobby.advance_finished_hands()
    assert lobby.game.hand_number == 2
    assert not lobby.game.tables[0].engine.finished


def test_finished_table_does_not_offer_player_actions():
    from web import game_store

    lobby = game_store.LobbyTournament("code", "Daily", "admin", hand_count=2, player_names=["alice"])
    lobby.start()
    table = lobby.table_for("alice")
    finish_player_hand(lobby.game, "alice")

    assert table.engine.finished
    assert game_store.legal_action_options(table.engine) == []
