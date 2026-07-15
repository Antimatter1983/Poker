import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "poker_web.settings")

import django

django.setup()

import pytest
from django.conf import settings
from django.test import Client
from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.urls import reverse

from poker.hand_engine import CALL, CHECK
from web import game_store


def finish_player_hand(tournament, player_id):
    table = next(table for table in tournament.tables if table.player.player_id == player_id)
    while not table.engine.finished:
        action = CALL if CALL in table.engine.legal_actions(table.player) else CHECK
        tournament.submit_player_action(player_id, action)


@pytest.fixture(autouse=True)
def cookie_sessions():
    settings.SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"


@pytest.fixture(autouse=True)
def clear_store():
    game_store.TOURNAMENTS.clear()
    yield
    game_store.TOURNAMENTS.clear()


def make_lobby(players=("alice", "bob"), hand_count=2):
    lobby = game_store.LobbyTournament("code", "Daily", "admin", hand_count=hand_count, player_names=list(players))
    game_store.TOURNAMENTS[lobby.code] = lobby
    lobby.start()
    return lobby


def client_as(name):
    client = Client()
    session = SessionStore()
    session["player:code"] = name
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    return client


def test_player_finishes_early_waits_without_bot_cards_or_other_results():
    lobby = make_lobby()
    finish_player_hand(lobby.game, "alice")

    response = client_as("alice").get(reverse("web:tournament_detail", kwargs={"code": "code"}), follow=True)

    assert response.resolver_match.url_name == "hand_wait"
    content = response.content.decode()
    assert "Ожидаем остальных игроков" in content
    assert "Карты бота" not in content
    assert "bot_hand" not in content
    assert "Ваш итог по фишкам" not in content
    status = client_as("alice").get(reverse("web:hand_status", kwargs={"code": "code", "hand_number": 1})).json()
    assert status == {"status": "waiting", "finished_count": 1, "total_count": 2}


def test_last_player_moves_common_hand_to_reveal_and_all_get_results_url(monkeypatch):
    now = 100.0
    monkeypatch.setattr(game_store, "monotonic", lambda: now)
    lobby = make_lobby()
    finish_player_hand(lobby.game, "alice")
    finish_player_hand(lobby.game, "bob")

    status = client_as("alice").get(reverse("web:hand_status", kwargs={"code": "code", "hand_number": 1})).json()
    other_status = client_as("bob").get(reverse("web:hand_status", kwargs={"code": "code", "hand_number": 1})).json()

    assert lobby.hand_state == game_store.HAND_REVEAL
    assert lobby.reveal_started_at == 100.0
    assert lobby.reveal_until == 110.0
    assert status["status"] == "reveal"
    assert status["url"] == reverse("web:hand_results", kwargs={"code": "code", "hand_number": 1})
    assert other_status == status


def test_results_page_only_reveals_bot_cards_and_full_table_in_reveal():
    lobby = make_lobby()
    finish_player_hand(lobby.game, "alice")

    early = client_as("alice").get(reverse("web:hand_results", kwargs={"code": "code", "hand_number": 1}), follow=True)
    assert early.resolver_match.url_name == "hand_wait"
    assert "Карты бота" not in early.content.decode()

    finish_player_hand(lobby.game, "bob")
    lobby.start_reveal()
    reveal = client_as("alice").get(reverse("web:hand_results", kwargs={"code": "code", "hand_number": 1}))
    content = reveal.content.decode()
    assert "Карты бота" in content
    assert "Бот:" in content
    assert "Комбинация бота" not in content
    assert "Общая раздача" not in content
    assert "bob" in content


def test_reveal_timer_creates_single_next_hand_and_reuses_url(monkeypatch):
    now = 100.0
    monkeypatch.setattr(game_store, "monotonic", lambda: now)
    lobby = make_lobby()
    finish_player_hand(lobby.game, "alice")
    finish_player_hand(lobby.game, "bob")
    lobby.start_reveal()

    reveal = client_as("alice").get(reverse("web:reveal_status", kwargs={"code": "code", "hand_number": 1})).json()
    assert reveal == {"status": "reveal", "seconds_left": 10}

    now = 116.0
    first = client_as("alice").get(reverse("web:reveal_status", kwargs={"code": "code", "hand_number": 1})).json()
    second = client_as("bob").get(reverse("web:reveal_status", kwargs={"code": "code", "hand_number": 1})).json()

    assert first["status"] == "next_hand"
    assert second == first
    assert lobby.game.hand_number == 2
    assert len(lobby.next_hand_by_completed_hand) == 1


def test_foreign_user_cannot_access_wait_results_or_json():
    make_lobby()
    stranger = Client()
    wait = stranger.get(reverse("web:hand_wait", kwargs={"code": "code", "hand_number": 1}))
    results = stranger.get(reverse("web:hand_results", kwargs={"code": "code", "hand_number": 1}))
    status = stranger.get(reverse("web:hand_status", kwargs={"code": "code", "hand_number": 1}))

    assert wait.status_code == 404
    assert results.status_code == 404
    assert status.status_code == 404


def test_chip_net_sum_is_preserved_for_reveal_results():
    lobby = make_lobby()
    finish_player_hand(lobby.game, "alice")
    finish_player_hand(lobby.game, "bob")
    lobby.start_reveal()

    rows = game_store.hand_results(lobby)

    assert sum(row["net"] for row in rows) == sum(
        table.player.stack - table.engine.starting_stacks[table.player.player_id]
        for table in lobby.game.tables
    )


def test_final_hand_goes_directly_to_leaderboard_without_extra_reveal():
    lobby = make_lobby(hand_count=1)
    finish_player_hand(lobby.game, "alice")
    finish_player_hand(lobby.game, "bob")

    response = client_as("alice").get(reverse("web:tournament_detail", kwargs={"code": "code"}), follow=True)
    status = client_as("alice").get(reverse("web:reveal_status", kwargs={"code": "code", "hand_number": 1})).json()

    assert lobby.status == game_store.FINISHED
    assert response.resolver_match.url_name == "leaderboard"
    assert "Итоги турнира" in response.content.decode()
    assert status["status"] == "finished"
    assert status["url"] == reverse("web:leaderboard", kwargs={"code": "code"})
