from poker.actions import ActionRequest, PlayerAction
from poker.engine import MatchEngine
from poker.game_log import GameLog
from poker.player import Player
from poker.table import Table


def make_table() -> Table:
    players = [
        Player(id="p1", name="Alice", stack=1_000),
        Player(id="p2", name="Bob", stack=1_000),
        Player(id="p3", name="Charlie", stack=1_000),
    ]
    return Table(table_id="table-1", players=players, small_blind=5, big_blind=10)


def test_game_log_events_get_sequential_numbers() -> None:
    game_log = GameLog()

    first = game_log.add_event("hand_start", "Hand started", "preflop", 0, 0)
    second = game_log.add_event("small_blind", "Small blind posted", "preflop", 5, 5)

    assert first.number == 1
    assert second.number == 2
    assert [event.number for event in game_log.events()] == [1, 2]


def test_game_log_clear_removes_events_and_resets_numbering() -> None:
    game_log = GameLog()
    game_log.add_event("hand_start", "Hand started", "preflop", 0, 0)

    game_log.clear()
    new_event = game_log.add_event("hand_start", "Next hand started", "preflop", 0, 0)

    assert game_log.events() == [new_event]
    assert new_event.number == 1


def test_engine_records_events_in_expected_order() -> None:
    table = make_table()
    engine = MatchEngine(table)

    engine.start_hand()
    engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CALL))
    engine.deal_flop()
    engine.deal_turn()
    engine.deal_river()

    assert [event.event_type for event in table.game_log.events()] == [
        "hand_start",
        "small_blind",
        "big_blind",
        "hole_cards",
        "hole_cards",
        "hole_cards",
        "call",
        "flop",
        "turn",
        "river",
    ]


def test_log_contains_expected_entries_after_hand_flow() -> None:
    table = make_table()
    engine = MatchEngine(table)

    engine.start_hand()
    engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.CALL))
    engine.apply_action(ActionRequest(player_id="p2", action=PlayerAction.CALL))
    engine.apply_action(ActionRequest(player_id="p3", action=PlayerAction.CHECK))
    engine.deal_flop()
    engine.apply_action(ActionRequest(player_id="p1", action=PlayerAction.BET, amount=20))

    events = table.game_log.events()
    event_types = [event.event_type for event in events]
    descriptions = [event.description for event in events]

    assert event_types[:6] == [
        "hand_start",
        "small_blind",
        "big_blind",
        "hole_cards",
        "hole_cards",
        "hole_cards",
    ]
    assert event_types[-2:] == ["flop", "bet"]
    assert any("Bob posted small blind 5" in description for description in descriptions)
    assert any("Charlie posted big blind 10" in description for description in descriptions)
    assert any("Alice: Call 10" in description for description in descriptions)
    assert events[-1].pot == 50
    assert events[-1].current_bet == 20
