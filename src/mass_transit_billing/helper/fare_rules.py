from __future__ import annotations

from decimal import Decimal

BASE_JOURNEY_FARE = Decimal("2.00")
ERROR_JOURNEY_FARE = Decimal("5.00")
DAILY_CAP = Decimal("15.00")
MONTHLY_CAP = Decimal("100.00")


def zone_surcharge(zone: int) -> Decimal:
    if zone == 1:
        return Decimal("0.80")
    if zone in (2, 3):
        return Decimal("0.50")
    if zone in (4, 5):
        return Decimal("0.30")
    return Decimal("0.10")
