from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class OpenJourney:
    station: str
    timestamp: datetime

    @property
    def journey_date(self) -> date:
        return self.timestamp.date()
