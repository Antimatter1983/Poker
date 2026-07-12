"""Poker bot policies used by tournament tables."""

from __future__ import annotations

from .hand_engine import CALL, CHECK, HandEngine
from .player import Player


class CallBot:
    """First-level bot: call when facing a bet, otherwise check."""

    name = "Call Bot"

    def choose_action(self, engine: HandEngine, bot: Player) -> tuple[str, int | None]:
        if engine.to_call(bot) > 0:
            return CALL, None
        return CHECK, None
