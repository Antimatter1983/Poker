"""Public interface for a single Texas Hold'em Heads-Up hand engine."""

from __future__ import annotations

from poker.contract import ActionRequest, EngineResponse, HandSetup


class HandEngine:
    """Engine interface for one Texas Hold'em Heads-Up hand."""

    def start(self, setup: HandSetup) -> EngineResponse:
        raise NotImplementedError

    def apply_action(self, request: ActionRequest) -> EngineResponse:
        raise NotImplementedError
