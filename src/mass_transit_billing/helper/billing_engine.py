from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from mass_transit_billing.helper import fare_rules
from mass_transit_billing.helper.fare_rules import DAILY_CAP, MONTHLY_CAP
from mass_transit_billing.models.direction import Direction
from mass_transit_billing.models.journey_event import JourneyEvent
from mass_transit_billing.models.open_journey import OpenJourney


class BillingEngine:
    def __init__(self, zone_map: dict[str, int]) -> None:
        self.zone_map = zone_map
        self.fare_rules = fare_rules
        self.user_to_open_journey: dict[str, OpenJourney] = {}
        self.user_to_charge: dict[str, Decimal] = {}
        self.user_to_daily_total: dict[str, dict[date, Decimal]] = {}
        self.user_to_monthly_total: dict[str, dict[tuple[int, int], Decimal]] = {}

    def process(self, event: JourneyEvent) -> None:
        """Process one journey event."""
        if event.direction == Direction.IN:
            self._process_in(event)
        if event.direction == Direction.OUT:
            self._process_out(event)

    def advance_time(self, now: datetime) -> None:
        """Expire open journeys from earlier days if this mode is used."""
        for user_id, open_journey in list(self.user_to_open_journey.items()):
            if open_journey.journey_date < now.date():
                self._add_charge(
                    user_id,
                    self.fare_rules.ERROR_JOURNEY_FARE,
                    open_journey.journey_date,
                )
                self.user_to_open_journey.pop(user_id)

    def finalize(self) -> None:
        """Finalize the billing engine."""
        for user_id, open_journey in list(self.user_to_open_journey.items()):
            self._add_charge(
                user_id,
                self.fare_rules.ERROR_JOURNEY_FARE,
                open_journey.journey_date,  # Orphaned "IN" at end of input.
            )
            self.user_to_open_journey.pop(user_id)

    def totals(self) -> dict[str, Decimal]:
        """Return final or current totals by user."""
        return dict(self.user_to_charge)

    def _process_in(self, event: JourneyEvent) -> None:
        if event.user_id in self.user_to_open_journey:
            self._add_charge(
                event.user_id,
                self.fare_rules.ERROR_JOURNEY_FARE,
                self.user_to_open_journey[
                    event.user_id
                ].journey_date,  # Earlier "IN" never got an "OUT".
            )
            self.user_to_open_journey.pop(event.user_id)
        self.user_to_open_journey[event.user_id] = OpenJourney(
            event.station, event.timestamp
        )

    def _process_out(self, event: JourneyEvent) -> None:
        if event.user_id in self.user_to_open_journey:
            open_journey = self.user_to_open_journey[event.user_id]
            # A journey that crosses midnight is split into two errors:
            # the old open journey is orphaned, and the current OUT is unmatched.
            if open_journey.timestamp.date() != event.timestamp.date():
                self._add_charge(
                    event.user_id,
                    self.fare_rules.ERROR_JOURNEY_FARE,
                    open_journey.journey_date,
                )
                self.user_to_open_journey.pop(event.user_id)
                self._add_charge(
                    event.user_id,
                    self.fare_rules.ERROR_JOURNEY_FARE,
                    event.timestamp.date(),
                )
                return
            # Unknown station names are treated as a recoverable journey error rather
            # than invalid input - charged one time ERROR_JOURNEY_FARE
            elif (
                open_journey.station not in self.zone_map
                or event.station not in self.zone_map
            ):
                self._add_charge(
                    event.user_id,
                    self.fare_rules.ERROR_JOURNEY_FARE,
                    open_journey.journey_date,
                )
            # Same-day good journey
            else:
                in_station_zone = self.zone_map[open_journey.station]
                out_station_zone = self.zone_map[event.station]
                self._add_charge(
                    event.user_id,
                    self.fare_rules.BASE_JOURNEY_FARE
                    + self.fare_rules.zone_surcharge(in_station_zone)
                    + self.fare_rules.zone_surcharge(out_station_zone),
                    open_journey.journey_date,
                )
            self.user_to_open_journey.pop(event.user_id)
            return
        # Erroneous "OUT" without "IN"
        self._add_charge(
            event.user_id,
            self.fare_rules.ERROR_JOURNEY_FARE,
            event.timestamp.date(),
        )

    def _add_charge(self, user_id: str, amount: Decimal, journey_date: date) -> None:
        if user_id not in self.user_to_daily_total:
            self.user_to_daily_total[user_id] = {}
        if user_id not in self.user_to_monthly_total:
            self.user_to_monthly_total[user_id] = {}
        current_day_total = self.user_to_daily_total[user_id].get(
            journey_date, Decimal("0.00")
        )
        current_month_total = self.user_to_monthly_total[user_id].get(
            (journey_date.year, journey_date.month), Decimal("0.00")
        )

        remaining_day = max(Decimal("0.00"), DAILY_CAP - current_day_total)
        remaining_month = max(Decimal("0.00"), MONTHLY_CAP - current_month_total)
        applied_amount = min(amount, remaining_day, remaining_month)

        new_day_total = current_day_total + applied_amount
        new_month_total = current_month_total + applied_amount

        self.user_to_daily_total[user_id][journey_date] = new_day_total
        self.user_to_monthly_total[user_id][
            (journey_date.year, journey_date.month)
        ] = new_month_total
        self.user_to_charge[user_id] = (
            self.user_to_charge.get(user_id, Decimal("0.00")) + applied_amount
        )
