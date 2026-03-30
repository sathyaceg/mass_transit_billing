from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from mass_transit_billing.models.direction import Direction


@dataclass(frozen=True)
class JourneyEvent:
    user_id: str
    station: str
    direction: Direction
    timestamp: datetime
