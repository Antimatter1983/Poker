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


def test_tournament_page_sets_csrf_cookie_and_accepts_join_form_with_token():
    lobby = game_store.create("Daily", "Admin", 3)
    client = Client(enforce_csrf_checks=True)

    page = client.get(reverse("web:tournament_detail", kwargs={"code": lobby.code}))
    csrf_token = client.cookies[settings.CSRF_COOKIE_NAME].value
    response = client.post(
        reverse("web:join_tournament", kwargs={"code": lobby.code}),
        {"name": "Alice", "csrfmiddlewaretoken": csrf_token},
    )

    assert page.status_code == 200
    assert csrf_token
    assert response.status_code == 302
    assert "Alice" in lobby.player_names
