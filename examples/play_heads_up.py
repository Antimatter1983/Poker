from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from poker.hand_engine import FOLD, CHECK, CALL, BET, RAISE, ALL_IN, HandEngine
from poker.player import Player


def ask(prompt, default):
    value = input(f"{prompt} [{default}]: ").strip()
    return value or str(default)


def pause_clear():
    input("Передайте устройство следующему игроку и нажмите Enter...")
    print("\n" * 30)


def cards_text(cards):
    return " ".join(map(str, cards)) if cards else "-"


def parse_action(text):
    parts = text.strip().lower().replace("all-in", "all_in").split()
    if not parts:
        raise ValueError("Введите действие")
    aliases = {"f": FOLD, "fold": FOLD, "x": CHECK, "check": CHECK, "c": CALL, "call": CALL,
               "b": BET, "bet": BET, "r": RAISE, "raise": RAISE, "a": ALL_IN, "all_in": ALL_IN, "allin": ALL_IN}
    action = aliases.get(parts[0])
    if not action:
        raise ValueError("Неизвестная команда")
    amount = int(parts[1]) if len(parts) > 1 else None
    return action, amount


def show_turn(engine):
    p = engine.current_player
    print(f"Улица: {engine.street}")
    print(f"Общие карты: {cards_text(engine.community_cards)}")
    print(f"Банк: {engine.pot}")
    print(f"Текущая ставка: {engine.current_bet}")
    print(f"Ход игрока: {p.player_id}")
    print(f"Ваши карты: {cards_text(p.cards)}")
    print(f"Ваш стек: {p.stack}")
    print(f"Поставлено на улице: {p.street_bet}")
    print(f"Нужно для call: {engine.to_call(p)}")
    actions = ", ".join(a.lower().replace("_", "-") for a in engine.legal_actions())
    print(f"Доступные действия: {actions}")
    if engine.current_bet == 0:
        print(f"Минимальный bet: {engine.big_blind}")
    else:
        print(f"Минимальная итоговая сумма raise: {engine.current_bet + engine.min_raise}")


def main():
    p1_name = ask("Имя игрока 1", "Alice")
    p2_name = ask("Имя игрока 2", "Bob")
    p1 = Player(p1_name, int(ask("Стек игрока 1", 1000)))
    p2 = Player(p2_name, int(ask("Стек игрока 2", 1000)))
    sb = int(ask("Малый блайнд", 5))
    bb = int(ask("Большой блайнд", 10))
    who = ask("Кто ставит малый блайнд — 1 или 2", 1)
    engine = HandEngine(p1, p2, p1.player_id if who == "1" else p2.player_id, sb, bb)
    engine.start_hand()

    while not engine.finished:
        pause_clear()
        show_turn(engine)
        while True:
            try:
                action, amount = parse_action(input("Ваше действие: "))
                engine.act(action, amount)
                break
            except Exception as exc:
                print(f"Ошибка: {exc}")

    print("\nРаздача завершена")
    print(f"Причина: {engine.finish_reason}")
    for p in engine.players:
        print(f"Карты {p.player_id}: {cards_text(p.cards)}")
        hv = engine.hand_values.get(p.player_id)
        print(f"Комбинация {p.player_id}: {hv.name if hv else '-'}")
    print(f"Общие карты: {cards_text(engine.community_cards)}")
    print(f"Банк: {engine.pot}")
    print(f"Победитель: {', '.join(p.player_id for p in engine.winners)}")
    for p in engine.players:
        print(f"Итоговый стек {p.player_id}: {p.stack}")


if __name__ == "__main__":
    main()
