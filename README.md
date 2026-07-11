# Texas Hold'em Heads-Up (one hand)

Учебный консольный движок для одной полноценной раздачи Texas Hold'em Heads-Up. Без сервера, GUI, базы данных, турниров и внешних покерных библиотек.

## Запуск в Pydroid 3

1. Скопируйте папку проекта на устройство.
2. Откройте терминал Pydroid 3 в корне проекта.
3. Запустите:

```bash
python examples/play_heads_up.py
```

## Запуск на Windows

Откройте PowerShell или CMD в корне проекта и выполните:

```bash
python examples/play_heads_up.py
```

Если команда `python` не найдена, попробуйте:

```bash
py examples/play_heads_up.py
```

## Тесты

```bash
python -m pytest
```

## Команды игрока

Полные команды:

```text
fold
check
call
bet 20
raise 40
all-in
```

Короткие команды:

```text
f
x
c
b 20
r 40
a
```

Для `bet` и `raise` сумма означает итоговую ставку игрока на текущей улице, а не добавку.

## Устройство проекта

- `poker/card.py` — карта и значения рангов.
- `poker/deck.py` — колода из 52 уникальных карт.
- `poker/player.py` — простой игрок со стеком, картами и ставками.
- `poker/hand_evaluator.py` — оценка лучшей комбинации из 7 карт.
- `poker/hand_engine.py` — логика одной heads-up раздачи.
- `examples/play_heads_up.py` — ручная консольная игра за двух игроков.
- `tests/` — тесты колоды, оценщика и движка.
