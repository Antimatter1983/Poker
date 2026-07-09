# Poker Engine

A minimal Texas Hold'em engine skeleton written in pure Python.

The project is intentionally small and framework-free so it can later be connected to Django, WebSocket consumers, or another transport layer.

## Project structure

```text
poker/
  __init__.py
  cards.py
  deck.py
  player.py
  table.py
  engine.py
examples/
  test_deal.py
tests/
  test_deck.py
  test_table.py
```

## Current features

- Card, rank, and suit primitives.
- Standard 52-card deck with shuffle and deal helpers.
- Player and table state models.
- Basic match engine that can:
  - start a hand;
  - post blinds;
  - deal hole cards;
  - deal flop, turn, and river.

## Not implemented yet

- Hand evaluation.
- Betting rounds after blinds.
- Side pots.
- WebSocket or Django integration.

## Run the example

```bash
python examples/test_deal.py
```

## Run tests

```bash
python -m pytest
```
