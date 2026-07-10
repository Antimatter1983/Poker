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
  _bootstrap.py
  example_deck.py
  example_full_deal.py
  example_player.py
  example_table.py
tests/
  test_cards.py
  test_deck.py
  test_engine.py
  test_player.py
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

## Run examples

Examples are small educational scripts that can be launched from the project root:

```bash
python examples/example_deck.py
python examples/example_player.py
python examples/example_table.py
python examples/example_full_deal.py
```

## Run tests

Run the full automated test suite with pytest:

```bash
python -m pytest
```

Run one test file:

```bash
python -m pytest tests/test_deck.py
```

Run one specific test function:

```bash
python -m pytest tests/test_deck.py::test_deck_has_52_unique_cards
```
