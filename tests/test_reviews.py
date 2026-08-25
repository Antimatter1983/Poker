import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "poker_web.settings")

import django

django.setup()

from django.contrib.staticfiles import finders
from django.test import Client
from django.urls import reverse


def test_reviews_page_and_assets_are_available():
    client = Client()

    home_response = client.get(reverse("web:home"))
    reviews_response = client.get(reverse("web:reviews"))
    assert home_response.status_code == 200
    assert reverse("web:reviews") in home_response.content.decode()
    assert reviews_response.status_code == 200
    content = reviews_response.content.decode()
    assert "Отзывы покупателей" in content
    assert "Пользователь из Саратова" in content
    assert 'data-voice-audio' in content
    assert '<audio class="voice-audio" controls' in content
    assert finders.find("web/reviews/1787547870943.jpg")
    assert finders.find("web/reviews/2_5217695076280474580.ogg")
