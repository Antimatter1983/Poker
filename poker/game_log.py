"""Game event journal for poker hands."""

from dataclasses import dataclass
from typing import TextIO


@dataclass(frozen=True, slots=True)
class GameEvent:
    """A single chronological event in a poker hand."""

    number: int
    event_type: str
    description: str
    street: str
    pot: int
    current_bet: int


class GameLog:
    """Chronological journal of game events for a hand."""

    def __init__(self) -> None:
        self._events: list[GameEvent] = []

    def add_event(
        self,
        event_type: str,
        description: str,
        street: str,
        pot: int,
        current_bet: int,
    ) -> GameEvent:
        """Add a new event and assign the next sequential event number."""

        event = GameEvent(
            number=len(self._events) + 1,
            event_type=event_type,
            description=description,
            street=street,
            pot=pot,
            current_bet=current_bet,
        )
        self._events.append(event)
        return event

    def events(self) -> list[GameEvent]:
        """Return a copy of recorded events in chronological order."""

        return list(self._events)

    def clear(self) -> None:
        """Remove all events from the journal."""

        self._events.clear()

    def format(self) -> str:
        """Return the journal in a human-readable multiline format."""

        return "\n".join(
            f"#{event.number} [{event.street}] {event.event_type}: "
            f"{event.description} (pot={event.pot}, current_bet={event.current_bet})"
            for event in self._events
        )

    def print_journal(self, file: TextIO | None = None) -> None:
        """Write the formatted journal to a text stream."""

        text = self.format()
        if file is None:
            import sys

            file = sys.stdout
        file.write(text)
        file.write("\n")
