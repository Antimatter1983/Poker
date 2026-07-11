from poker.card import Card
from poker.hand_engine import *
from poker.player import Player


def engine(stacks=(100, 100)):
    e = HandEngine(Player("Alice", stacks[0]), Player("Bob", stacks[1]), "Alice", 5, 10)
    e.start_hand()
    return e


def force_showdown(e, board, a, b):
    e.community_cards = [Card(x[0], x[1]) for x in board.split()]
    e.players[0].cards = [Card(x[0], x[1]) for x in a.split()]
    e.players[1].cards = [Card(x[0], x[1]) for x in b.split()]
    e._showdown()


def test_blinds_and_first_preflop_action():
    e = engine()
    assert (e.players[0].stack, e.players[1].stack, e.pot) == (95, 90, 15)
    assert e.current_player.player_id == "Alice"


def test_first_after_flop_is_big_blind():
    e = engine(); e.act(CALL); e.act(CHECK)
    assert e.street == FLOP
    assert e.current_player.player_id == "Bob"


def test_fold_finishes_and_preserves_chips():
    e = engine(); e.act(FOLD)
    assert e.finished and e.finish_reason == "fold"
    assert e.winners[0].player_id == "Bob"
    assert sum(p.stack for p in e.players) == 200


def test_check_forbidden_when_call_required_and_call_changes_stack_pot():
    e = engine()
    try:
        e.act(CHECK)
        assert False
    except ValueError:
        pass
    e.act(CALL)
    assert e.players[0].stack == 90 and e.pot == 20


def test_bet_and_raise():
    e = engine(); e.act(CALL); e.act(CHECK)
    e.act(BET, 10)
    assert e.current_bet == 10 and e.pot == 30
    e.act(RAISE, 30)
    assert e.current_bet == 30 and e.min_raise == 20 and e.pot == 60


def test_all_in_auto_board_and_unequal_stack_return():
    e = engine((50, 100)); e.act(ALL_IN); e.act(CALL)
    assert e.finished and len(e.community_cards) == 5
    assert sum(p.stack for p in e.players) == 150


def test_street_transitions_to_showdown():
    e = engine()
    e.act(CALL); e.act(CHECK)
    assert e.street == FLOP
    e.act(CHECK); e.act(CHECK)
    assert e.street == TURN
    e.act(CHECK); e.act(CHECK)
    assert e.street == RIVER
    e.act(CHECK); e.act(CHECK)
    assert e.finished and e.finish_reason == "showdown"
    assert sum(p.stack for p in e.players) == 200


def test_showdown_winner_and_split_odd_chip_to_button():
    e = engine(); e.pot = 0
    force_showdown(e, "AS KS QS 2C 3D", "AH AD", "KH KD")
    assert e.winners[0].player_id == "Alice"
    e2 = engine((101, 100))
    e2.players[0].stack = 90; e2.players[1].stack = 90
    e2.players[0].total_bet = 11; e2.players[1].total_bet = 10; e2.pot = 21
    force_showdown(e2, "AS KD QH JC 9S", "3D 2C", "3C 2D")
    assert len(e2.winners) == 2
    assert e2.players[0].stack == 101 and e2.players[1].stack == 100
