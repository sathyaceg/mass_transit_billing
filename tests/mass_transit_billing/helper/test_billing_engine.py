from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from mass_transit_billing.helper.billing_engine import BillingEngine
from mass_transit_billing.models.direction import Direction
from mass_transit_billing.models.journey_event import JourneyEvent


def test_process_in_opens_journey_without_charge() -> None:
    engine = BillingEngine({"alpha": 1, "bravo": 2})

    engine.process(
        JourneyEvent(
            user_id="user1",
            station="alpha",
            direction=Direction.IN,
            timestamp=datetime(2022, 4, 4, 9, 0, 0),
        )
    )

    assert engine.user_to_open_journey["user1"].station == "alpha"
    assert engine.user_to_daily_total == {}


def test_process_duplicate_in_charges_error_and_replaces_open_journey() -> None:
    engine = BillingEngine({"alpha": 1, "bravo": 2})

    engine.process(
        JourneyEvent(
            user_id="user1",
            station="alpha",
            direction=Direction.IN,
            timestamp=datetime(2022, 4, 4, 9, 0, 0),
        )
    )
    engine.process(
        JourneyEvent(
            user_id="user1",
            station="bravo",
            direction=Direction.IN,
            timestamp=datetime(2022, 4, 4, 10, 0, 0),
        )
    )

    assert engine.user_to_daily_total["user1"][date(2022, 4, 4)] == Decimal("5.00")
    assert engine.user_to_open_journey["user1"].station == "bravo"


def test_process_valid_out_adds_journey_fare_and_clears_open_journey() -> None:
    engine = BillingEngine({"alpha": 1, "bravo": 2})

    engine.process(
        JourneyEvent(
            user_id="user1",
            station="alpha",
            direction=Direction.IN,
            timestamp=datetime(2022, 4, 4, 9, 0, 0),
        )
    )
    engine.process(
        JourneyEvent(
            user_id="user1",
            station="bravo",
            direction=Direction.OUT,
            timestamp=datetime(2022, 4, 4, 10, 0, 0),
        )
    )

    assert engine.user_to_daily_total["user1"][date(2022, 4, 4)] == Decimal("3.30")
    assert "user1" not in engine.user_to_open_journey


def test_process_unmatched_out_charges_error_fare() -> None:
    engine = BillingEngine({"alpha": 1, "bravo": 2})

    engine.process(
        JourneyEvent(
            user_id="user1",
            station="bravo",
            direction=Direction.OUT,
            timestamp=datetime(2022, 4, 4, 10, 0, 0),
        )
    )

    assert engine.user_to_daily_total["user1"][date(2022, 4, 4)] == Decimal("5.00")


def test_process_cross_midnight_out_charges_two_error_fares() -> None:
    engine = BillingEngine({"alpha": 1, "bravo": 2})

    engine.process(
        JourneyEvent(
            user_id="user1",
            station="alpha",
            direction=Direction.IN,
            timestamp=datetime(2022, 4, 4, 23, 55, 0),
        )
    )
    engine.process(
        JourneyEvent(
            user_id="user1",
            station="bravo",
            direction=Direction.OUT,
            timestamp=datetime(2022, 4, 5, 0, 10, 0),
        )
    )

    assert engine.user_to_daily_total["user1"][date(2022, 4, 4)] == Decimal("5.00")
    assert engine.user_to_daily_total["user1"][date(2022, 4, 5)] == Decimal("5.00")
    assert engine.user_to_charge["user1"] == Decimal("10.00")
    assert "user1" not in engine.user_to_open_journey


def test_process_unknown_station_pair_charges_one_error_fare() -> None:
    engine = BillingEngine({"bravo": 2})

    engine.process(
        JourneyEvent(
            user_id="user1",
            station="alpha",
            direction=Direction.IN,
            timestamp=datetime(2022, 4, 4, 9, 0, 0),
        )
    )
    engine.process(
        JourneyEvent(
            user_id="user1",
            station="bravo",
            direction=Direction.OUT,
            timestamp=datetime(2022, 4, 4, 10, 0, 0),
        )
    )

    assert engine.user_to_daily_total["user1"][date(2022, 4, 4)] == Decimal("5.00")
    assert "user1" not in engine.user_to_open_journey


def test_add_charge_applies_full_amount_when_no_cap_is_hit() -> None:
    engine = BillingEngine({})

    engine._add_charge("user1", Decimal("3.30"), date(2022, 4, 4))

    assert engine.user_to_daily_total["user1"][date(2022, 4, 4)] == Decimal("3.30")
    assert engine.user_to_monthly_total["user1"][(2022, 4)] == Decimal("3.30")


def test_add_charge_stops_at_daily_cap() -> None:
    engine = BillingEngine({})
    journey_date = date(2022, 4, 4)

    engine._add_charge("user1", Decimal("14.00"), journey_date)
    engine._add_charge("user1", Decimal("3.00"), journey_date)

    assert engine.user_to_daily_total["user1"][journey_date] == Decimal("15.00")
    assert engine.user_to_monthly_total["user1"][(2022, 4)] == Decimal("15.00")


def test_add_charge_stops_at_monthly_cap() -> None:
    engine = BillingEngine({})

    for day in range(1, 8):
        engine._add_charge("user1", Decimal("15.00"), date(2022, 4, day))
    engine._add_charge("user1", Decimal("5.00"), date(2022, 4, 8))

    assert engine.user_to_daily_total["user1"][date(2022, 4, 7)] == Decimal("10.00")
    assert engine.user_to_daily_total["user1"][date(2022, 4, 8)] == Decimal("0.00")
    assert engine.user_to_monthly_total["user1"][(2022, 4)] == Decimal("100.00")


def test_finalize_charges_orphaned_in_and_clears_open_journeys() -> None:
    engine = BillingEngine({})

    engine.process(
        JourneyEvent(
            user_id="user1",
            station="alpha",
            direction=Direction.IN,
            timestamp=datetime(2022, 4, 4, 9, 0, 0),
        )
    )
    engine.process(
        JourneyEvent(
            user_id="user2",
            station="bravo",
            direction=Direction.IN,
            timestamp=datetime(2022, 4, 5, 10, 0, 0),
        )
    )

    engine.finalize()

    assert engine.user_to_daily_total["user1"][date(2022, 4, 4)] == Decimal("5.00")
    assert engine.user_to_daily_total["user2"][date(2022, 4, 5)] == Decimal("5.00")
    assert engine.user_to_open_journey == {}


def test_totals_returns_sum_of_user_monthly_totals() -> None:
    engine = BillingEngine({})

    engine._add_charge("user1", Decimal("15.00"), date(2022, 4, 1))
    engine._add_charge("user1", Decimal("15.00"), date(2022, 5, 1))
    engine._add_charge("user2", Decimal("5.00"), date(2022, 4, 1))

    assert engine.totals() == {
        "user1": Decimal("30.00"),
        "user2": Decimal("5.00"),
    }
