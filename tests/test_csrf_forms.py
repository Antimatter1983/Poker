import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "poker_web.settings")

import django

django.setup()

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

from web import game_store


@pytest.fixture(autouse=True)
def cookie_sessions():
    settings.SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"


@pytest.fixture(autouse=True)
def clear_store():
    game_store.TOURNAMENTS.clear()
    yield
    game_store.TOURNAMENTS.clear()


def test_home_sets_csrf_cookie_and_accepts_create_form_with_token():
    client = Client(enforce_csrf_checks=True)

    page = client.get(reverse("web:home"))
    csrf_token = client.cookies[settings.CSRF_COOKIE_NAME].value
    response = client.post(
        reverse("web:create_tournament"),
        {"title": "Daily", "admin": "Admin", "hand_count": "3", "csrfmiddlewaretoken": csrf_token},
    )

    assert page.status_code == 200
    assert csrf_token
    assert response.status_code == 302
    assert len(game_store.TOURNAMENTS) == 1


def test_admin_tournaments_page_is_served_by_web_app():
    client = Client()

    response = client.get("/admin/tournaments/")

    assert response.status_code == 200
    assert "Создать турнир" in response.content.decode()


def test_home_page_does_not_show_admin_button():
    client = Client()

    response = client.get(reverse("web:home"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Страница администратора" not in content
    assert reverse("web:admin_tournaments") not in content


def test_tournament_page_sets_csrf_cookie_and_accepts_join_form_with_token():
    lobby = game_store.create("Daily", "Admin", 3)
    client = Client(enforce_csrf_checks=True)

    page = client.get(reverse("web:tournament_detail", kwargs={"code": lobby.code}))
    csrf_token = client.cookies[settings.CSRF_COOKIE_NAME].value
    client.post(
        reverse("web:register_site_player"),
        {"nickname": "Alice", "password": "secret", "csrfmiddlewaretoken": csrf_token},
    )
    response = client.post(
        reverse("web:join_tournament", kwargs={"code": lobby.code}),
        {"csrfmiddlewaretoken": csrf_token},
    )

    assert page.status_code == 200
    assert csrf_token
    assert response.status_code == 302
    assert "Alice" in lobby.player_names


def test_game_action_post_requires_csrf_token_and_accepts_valid_token():
    lobby = game_store.create("Daily", "Admin", 3)
    lobby.add_player("Alice")
    lobby.start()
    client = Client(enforce_csrf_checks=True)
    session = client.session
    session[f"player:{lobby.code}"] = "Alice"
    session.save()

    page = client.get(reverse("web:tournament_detail", kwargs={"code": lobby.code}))
    csrf_token = client.cookies[settings.CSRF_COOKIE_NAME].value
    action_url = reverse("web:submit_action", kwargs={"code": lobby.code})

    missing_token_response = client.post(action_url, {"action": "FOLD"})
    valid_token_response = client.post(
        action_url,
        {"action": "FOLD", "csrfmiddlewaretoken": csrf_token},
    )

    assert page.status_code == 200
    assert csrf_token
    assert missing_token_response.status_code == 403
    assert valid_token_response.status_code == 302
