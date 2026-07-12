from __future__ import annotations

from django.contrib import messages
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import game_store


def _lobby_or_404(code: str) -> game_store.LobbyTournament:
    try:
        return game_store.get(code)
    except ValueError as exc:
        raise Http404(str(exc)) from exc


def home(request: HttpRequest):
    return render(request, "web/home.html", {"tournaments": list(game_store.TOURNAMENTS.values())})


@require_POST
def create_tournament(request: HttpRequest):
    title = request.POST.get("title", "")
    admin = request.POST.get("admin", "")
    try:
        hand_count = int(request.POST.get("hand_count") or 100)
        if not 1 <= hand_count <= 100:
            raise ValueError
    except ValueError:
        messages.error(request, "Количество раздач должно быть от 1 до 100")
        return redirect("web:home")
    lobby = game_store.create(title, admin, hand_count)
    messages.success(request, "Турнир создан. Отправьте ссылку участникам.")
    return redirect("web:tournament_detail", code=lobby.code)


def tournament_detail(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    player_name = request.session.get(f"player:{code}")
    lobby.advance_finished_hands()
    table = lobby.table_for(player_name) if player_name else None
    engine = table.engine if table else None
    context = {
        "lobby": lobby,
        "player_name": player_name,
        "table": table,
        "engine": engine,
        "hole_cards": game_store.card_text(table.player.cards) if table else "—",
        "bot_cards": game_store.card_text(table.bot.cards) if table and engine and engine.finished else "Скрыты",
        "board": game_store.card_text(engine.community_cards) if engine else "—",
        "legal_actions": game_store.legal_action_options(engine) if engine and engine.current_player is table.player else [],
    }
    return render(request, "web/tournament.html", context)


@require_POST
def join_tournament(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    name = request.POST.get("name", "")[:40].strip()
    try:
        if name not in lobby.player_names:
            lobby.add_player(name)
        request.session[f"player:{code}"] = name
        messages.success(request, f"Вы зарегистрированы как {name}")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("web:tournament_detail", code=code)


@require_POST
def start_tournament(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    try:
        lobby.start()
        messages.success(request, "Турнир начался")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("web:tournament_detail", code=code)


@require_POST
def submit_action(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    player_name = request.session.get(f"player:{code}")
    if not player_name:
        messages.error(request, "Сначала зарегистрируйтесь в турнире")
        return redirect("web:tournament_detail", code=code)
    action = request.POST.get("action", "")
    amount_raw = request.POST.get("amount", "").strip()
    try:
        amount = int(amount_raw) if amount_raw else None
        if lobby.game is None:
            raise ValueError("Турнир ещё не начался")
        lobby.game.submit_player_action(player_name, action, amount)
        lobby.advance_finished_hands()
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("web:tournament_detail", code=code)


def leaderboard(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    lobby.advance_finished_hands()
    return render(request, "web/leaderboard.html", {"lobby": lobby})
