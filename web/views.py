from __future__ import annotations

from django.contrib import messages
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import game_store


def _lobby_or_404(code: str) -> game_store.LobbyTournament:
    try:
        return game_store.get(code)
    except ValueError as exc:
        raise Http404(str(exc)) from exc



def _tournament_context(lobby: game_store.LobbyTournament, player_name: str | None, *, is_waiting_room: bool = False, completed_hand_number: int | None = None):
    table = lobby.table_for(player_name) if player_name else None
    engine = table.engine if table else None
    player_turn = bool(engine and table and not engine.finished and engine.current_player is table.player)
    return {
        "lobby": lobby,
        "player_name": player_name,
        "table": table,
        "engine": engine,
        "hole_cards": game_store.card_view(table.player.cards) if table else [],
        "bot_cards": game_store.card_view(table.bot.cards) if table and engine and engine.finished else [],
        "bot_hidden": not (table and engine and engine.finished),
        "board": game_store.card_view(engine.community_cards) if engine else [],
        "legal_actions": game_store.legal_action_options(engine) if player_turn and not is_waiting_room else [],
        "betting_buttons": game_store.betting_buttons(engine, table.player) if player_turn and not is_waiting_room else [],
        "result": game_store.hand_result(engine, table.player.player_id if table else None),
        "hero_hand_summary": game_store.current_hand_summary((table.player.cards if table else []) + (engine.community_cards if engine else [])),
        "bot_hand_summary": game_store.current_hand_summary((table.bot.cards if table and engine and engine.finished else []) + (engine.community_cards if engine else [])),
        "race_standings": lobby.race_standings(),
        "can_advance_hand": lobby.can_advance_hand(),
        "player_can_advance_hand": False if is_waiting_room else lobby.player_can_advance_hand(player_name),
        "next_hand_actor_name": lobby.next_hand_actor_name,
        "final_hand_ready": bool(lobby.game and lobby.game.hand_number >= lobby.hand_count and lobby.can_advance_hand()),
        "next_hand_wait_seconds": None,
        "action_timer_seconds": None if is_waiting_room else (lobby.game.seconds_to_action_deadline() if lobby.game else None),
        "unfinished_players": lobby.unfinished_player_names(),
        "hero_blind": "МБ" if engine and table and engine.small_blind_player is table.player else "ББ" if engine and table else "",
        "bot_blind": "МБ" if engine and table and engine.small_blind_player is table.bot else "ББ" if engine and table else "",
        "is_waiting_room": is_waiting_room,
        "completed_hand_number": completed_hand_number,
        "finished_player_count": lobby.finished_player_count(completed_hand_number),
        "total_player_count": len(lobby.player_names),
    }

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
    lobby.advance_finished_hands()
    player_name = request.session.get(f"player:{code}")
    table = lobby.table_for(player_name) if player_name else None
    if table and lobby.status == game_store.RUNNING and table.engine.finished:
        return redirect("web:hand_wait", code=code, hand_number=lobby.game.hand_number)
    return render(request, "web/tournament.html", _tournament_context(lobby, player_name))


def hand_wait(request: HttpRequest, code: str, hand_number: int):
    lobby = _lobby_or_404(code)
    player_name = request.session.get(f"player:{code}")
    return render(request, "web/tournament.html", _tournament_context(lobby, player_name, is_waiting_room=True, completed_hand_number=hand_number))


def hand_status(request: HttpRequest, code: str, hand_number: int):
    lobby = _lobby_or_404(code)
    if lobby.game:
        lobby.game.process_timeouts()
    lobby.complete_current_hand_and_maybe_start_next()
    next_ready = lobby.next_hand_ready(hand_number)
    return JsonResponse({
        "next_hand_ready": next_ready,
        "next_url": reverse("web:tournament_detail", kwargs={"code": code}) if next_ready else "",
        "finished_count": lobby.finished_player_count(hand_number),
        "total_count": len(lobby.player_names),
        "status": lobby.status,
    })


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
def next_hand(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    try:
        if lobby.status == game_store.FINISHED:
            raise ValueError("Турнир уже завершён")
        player_name = request.session.get(f"player:{code}")
        if not lobby.can_advance_hand():
            waiting = ", ".join(lobby.unfinished_player_names()) or "другие игроки"
            raise ValueError(f"Игроки {waiting} ещё играют раздачу. Ждите.")
        if not lobby.player_can_advance_hand(player_name):
            raise ValueError("Кнопка следующей раздачи доступна только игроку, который завершил раздачу последним. Остальные столы обновятся автоматически.")
        hand_number = lobby.game.hand_number if lobby.game else 0
        lobby.complete_current_hand_and_maybe_start_next()
        if lobby.status == game_store.FINISHED:
            messages.success(request, "Турнир завершён")
        else:
            messages.success(request, "Ожидаем остальных игроков")
        return redirect("web:hand_wait", code=code, hand_number=hand_number)
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
        if lobby.status == game_store.FINISHED:
            raise ValueError("Турнир завершён. Создайте новый турнир, чтобы играть снова")
        if lobby.game is None:
            raise ValueError("Турнир ещё не начался")
        hand_number = lobby.game.hand_number
        lobby.game.submit_player_action(player_name, action, amount)
        table = lobby.table_for(player_name)
        if table and table.engine.finished:
            lobby.complete_current_hand_and_maybe_start_next()
            return redirect("web:hand_wait", code=code, hand_number=hand_number)
        lobby.advance_finished_hands()
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("web:tournament_detail", code=code)


def leaderboard(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    return render(request, "web/leaderboard.html", {"lobby": lobby})


@require_POST
def finish_tournament(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    try:
        lobby.finish()
        messages.success(request, "Турнир завершён")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("web:leaderboard", code=code)
