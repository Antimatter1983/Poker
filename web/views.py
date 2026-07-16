from __future__ import annotations

from django.contrib import messages
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from . import game_store
from poker.equity import calculate_equity


SITE_PLAYER_SESSION_KEY = "site_player_name"
SITE_PASSWORD_SESSION_KEY = "site_player_password"


def _lobby_or_404(code: str) -> game_store.LobbyTournament:
    try:
        return game_store.get(code)
    except ValueError as exc:
        raise Http404(str(exc)) from exc



def _require_player(lobby: game_store.LobbyTournament, code: str, request: HttpRequest) -> str:
    player_name = request.session.get(f"player:{code}")
    if not player_name or player_name not in lobby.player_names:
        raise Http404("Вы не участвуете в этом турнире")
    return player_name


def _blind_label_and_role(engine, participant) -> tuple[str, str]:
    if not engine or not participant:
        return "", ""
    if engine.small_blind_player is participant:
        return "МБ", "sb"
    return "ББ", "bb"


def _site_player_name(request: HttpRequest) -> str:
    return str(request.session.get(SITE_PLAYER_SESSION_KEY, "")).strip()


def _register_site_player(request: HttpRequest) -> str:
    name = request.POST.get("nickname", "")[:40].strip()
    password = request.POST.get("password", "")
    if not name:
        raise ValueError("Введите ник")
    if not password:
        raise ValueError("Введите пароль")
    request.session[SITE_PLAYER_SESSION_KEY] = name
    request.session[SITE_PASSWORD_SESSION_KEY] = password
    if request.POST.get("remember"):
        request.session.set_expiry(60 * 60 * 24 * 365)
    else:
        request.session.set_expiry(0)
    return name


def _tournament_context(lobby: game_store.LobbyTournament, player_name: str | None, *, is_waiting_room: bool = False, completed_hand_number: int | None = None):
    table = lobby.table_for(player_name) if player_name else None
    engine = table.engine if table else None
    player_turn = bool(engine and table and not engine.finished and engine.current_player is table.player)
    hero_blind, hero_blind_role = _blind_label_and_role(engine, table.player if table else None)
    bot_blind, bot_blind_role = _blind_label_and_role(engine, table.bot if table else None)
    equity = None
    if table and engine and not engine.finished and not engine.community_cards:
        equity = calculate_equity(table.player.cards)
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
        "call_amount": engine.to_call(table.player) if player_turn and table and not is_waiting_room else 0,
        "hero_committed": table.player.street_bet if table else 0,
        "bot_committed": table.bot.street_bet if table else 0,
        "result": game_store.hand_result(engine, table.player.player_id if table else None),
        "equity": equity,
        "hero_hand_summary": game_store.current_hand_summary_ru((table.player.cards if table else []) + (engine.community_cards if engine else [])),
        "bot_hand_summary": game_store.current_hand_summary_ru((table.bot.cards if table and engine and engine.finished else []) + (engine.community_cards if engine else [])),
        "is_postflop": bool(engine and len(engine.community_cards) >= 3),
        "pot_amount": engine.pot if engine else 0,
        "race_standings": lobby.race_standings(),
        "can_advance_hand": lobby.can_advance_hand(),
        "common_hand_status": lobby.hand_state,
        "player_can_advance_hand": False if is_waiting_room else lobby.player_can_advance_hand(player_name),
        "next_hand_actor_name": lobby.next_hand_actor_name,
        "final_hand_ready": bool(lobby.game and lobby.game.hand_number >= lobby.hand_count and lobby.can_advance_hand()),
        "next_hand_wait_seconds": None,
        "action_timer_seconds": None if is_waiting_room else (lobby.game.seconds_to_action_deadline() if lobby.game else None),
        "unfinished_players": lobby.unfinished_player_names(),
        "hero_blind": hero_blind,
        "hero_blind_role": hero_blind_role,
        "bot_blind": bot_blind,
        "bot_blind_role": bot_blind_role,
        "is_waiting_room": is_waiting_room,
        "completed_hand_number": completed_hand_number,
        "finished_player_count": lobby.finished_player_count(completed_hand_number),
        "total_player_count": len(lobby.player_names),
    }

@ensure_csrf_cookie
def home(request: HttpRequest):
    player_name = _site_player_name(request)
    return render(
        request,
        "web/home.html",
        {
            "tournaments": list(game_store.TOURNAMENTS.values()),
            "site_player_name": player_name,
            "default_hand_count": 10,
        },
    )


@require_POST
def register_site_player(request: HttpRequest):
    try:
        name = _register_site_player(request)
        messages.success(request, f"Здравствуйте, {name}. Теперь можно участвовать в турнирах одним нажатием.")
    except ValueError as exc:
        messages.error(request, str(exc))
    next_url = request.POST.get("next") or reverse("web:home")
    return redirect(next_url)


@ensure_csrf_cookie
def admin_tournaments(request: HttpRequest):
    return render(request, "web/admin_tournaments.html", {"default_hand_count": 10})


@require_POST
def create_tournament(request: HttpRequest):
    tournament_number = request.POST.get("tournament_number", "").strip()
    return_url = "web:admin_tournaments" if tournament_number else "web:home"
    try:
        hand_count = int(request.POST.get("hand_count") or 10)
        if not 1 <= hand_count <= 100:
            raise ValueError
    except ValueError:
        messages.error(request, "Количество раздач должно быть от 1 до 100")
        return redirect(return_url)
    if tournament_number:
        title = f"Турнир №{tournament_number}"
    else:
        title = f"Турнир №{len(game_store.TOURNAMENTS) + 1}"
    lobby = game_store.create(title, "admin", hand_count)
    messages.success(request, "Турнир создан. Отправьте ссылку участникам.")
    return redirect("web:tournament_detail", code=lobby.code)


@ensure_csrf_cookie
def tournament_detail(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    lobby.advance_finished_hands()
    player_name = request.session.get(f"player:{code}")
    site_player_name = _site_player_name(request)
    table = lobby.table_for(player_name) if player_name else None
    if lobby.status == game_store.FINISHED:
        return redirect("web:leaderboard", code=code)
    if table and lobby.status == game_store.RUNNING and table.engine.finished:
        lobby.mark_waiting_or_reveal()
        if lobby.hand_state == game_store.HAND_REVEAL:
            return redirect("web:hand_results", code=code, hand_number=lobby.game.hand_number)
        return redirect("web:hand_wait", code=code, hand_number=lobby.game.hand_number)
    context = _tournament_context(lobby, player_name)
    context["site_player_name"] = site_player_name
    return render(request, "web/tournament.html", context)


def hand_wait(request: HttpRequest, code: str, hand_number: int):
    lobby = _lobby_or_404(code)
    player_name = _require_player(lobby, code, request)
    if not lobby.game or hand_number != lobby.game.hand_number:
        return redirect("web:tournament_detail", code=code)
    lobby.mark_waiting_or_reveal()
    if lobby.hand_state == game_store.HAND_REVEAL:
        return redirect("web:hand_results", code=code, hand_number=hand_number)
    return render(request, "web/hand_wait.html", _tournament_context(lobby, player_name, is_waiting_room=True, completed_hand_number=hand_number))


@require_GET
def hand_status(request: HttpRequest, code: str, hand_number: int):
    lobby = _lobby_or_404(code)
    _require_player(lobby, code, request)
    if not lobby.game or hand_number != lobby.game.hand_number:
        return JsonResponse({"status": "next_hand", "url": reverse("web:tournament_detail", kwargs={"code": code})})
    if lobby.game:
        lobby.game.process_timeouts()
    lobby.mark_waiting_or_reveal()
    if lobby.hand_state == game_store.HAND_REVEAL:
        return JsonResponse({"status": "reveal", "url": reverse("web:hand_results", kwargs={"code": code, "hand_number": hand_number})})
    return JsonResponse({"status": "waiting", "finished_count": lobby.finished_player_count(hand_number), "total_count": len(lobby.player_names)})


def hand_results(request: HttpRequest, code: str, hand_number: int):
    lobby = _lobby_or_404(code)
    player_name = _require_player(lobby, code, request)
    if not lobby.game or hand_number != lobby.game.hand_number:
        return redirect("web:tournament_detail", code=code)
    lobby.mark_waiting_or_reveal()
    if lobby.hand_state != game_store.HAND_REVEAL:
        return redirect("web:hand_wait", code=code, hand_number=hand_number)
    context = _tournament_context(lobby, player_name, completed_hand_number=hand_number)
    results = game_store.hand_results(lobby)
    hero_result = next((row for row in results if row["player_name"] == player_name), None)
    context.update({"results": results, "hero_result": hero_result, "seconds_left": lobby.reveal_seconds_left()})
    return render(request, "web/hand_results.html", context)


@require_GET
def reveal_status(request: HttpRequest, code: str, hand_number: int):
    lobby = _lobby_or_404(code)
    _require_player(lobby, code, request)
    if not lobby.game:
        raise Http404("Турнир не начат")
    if lobby.status == game_store.FINISHED:
        return JsonResponse({"status": "finished", "url": reverse("web:leaderboard", kwargs={"code": code})})
    if lobby.hand_state != game_store.HAND_REVEAL and lobby.game.hand_number == hand_number:
        return JsonResponse({"status": "waiting", "finished_count": lobby.finished_player_count(hand_number), "total_count": len(lobby.player_names)})
    new_hand = lobby.get_or_create_next_hand_after_reveal(hand_number)
    if new_hand:
        return JsonResponse({"status": "next_hand", "url": reverse("web:tournament_detail", kwargs={"code": code})})
    if lobby.status == game_store.FINISHED:
        return JsonResponse({"status": "finished", "url": reverse("web:leaderboard", kwargs={"code": code})})
    return JsonResponse({"status": "reveal", "seconds_left": lobby.reveal_seconds_left()})


@require_POST
def join_tournament(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    name = _site_player_name(request)
    if not name:
        messages.error(request, "Сначала зарегистрируйтесь на сайте")
        return redirect("web:tournament_detail", code=code)
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
            lobby.mark_waiting_or_reveal()
            if lobby.hand_state == game_store.HAND_REVEAL:
                return redirect("web:hand_results", code=code, hand_number=hand_number)
            return redirect("web:hand_wait", code=code, hand_number=hand_number)
        lobby.advance_finished_hands()
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("web:tournament_detail", code=code)


def leaderboard(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    return render(request, "web/leaderboard.html", {"lobby": lobby, "results": game_store.tournament_results(lobby)})


@require_POST
def finish_tournament(request: HttpRequest, code: str):
    lobby = _lobby_or_404(code)
    try:
        lobby.finish()
        messages.success(request, "Турнир завершён")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("web:leaderboard", code=code)
