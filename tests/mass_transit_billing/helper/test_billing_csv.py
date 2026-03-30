from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from mass_transit_billing.helper.billing_csv import (
    read_journey_events,
    read_zone_map,
    write_totals,
)
from mass_transit_billing.models.direction import Direction


def test_read_zone_map_returns_station_zone_mapping(tmp_path) -> None:
    zone_map_path = tmp_path / "zone_map.csv"
    zone_map_path.write_text("station,zone\nalpha,1\nbravo,3\n", encoding="utf-8")

    zone_map = read_zone_map(zone_map_path)

    assert zone_map == {"alpha": 1, "bravo": 3}


def test_read_zone_map_rejects_duplicate_station(tmp_path) -> None:
    zone_map_path = tmp_path / "zone_map.csv"
    zone_map_path.write_text("station,zone\nalpha,1\nalpha,2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate station 'alpha'"):
        read_zone_map(zone_map_path)


def test_read_journey_events_parses_enum_and_timestamp(tmp_path) -> None:
    journeys_path = tmp_path / "journeys.csv"
    journeys_path.write_text(
        "user_id,station,direction,time\n"
        "user1,alpha,IN,2022-04-04T09:40:00\n"
        "user1,bravo,OUT,2022-04-04T10:00:00\n",
        encoding="utf-8",
    )

    events = read_journey_events(journeys_path)

    assert len(events) == 2
    assert events[0].user_id == "user1"
    assert events[0].station == "alpha"
    assert events[0].direction is Direction.IN
    assert events[0].timestamp == datetime(2022, 4, 4, 9, 40, 0)
    assert events[1].direction is Direction.OUT


def test_read_journey_events_rejects_invalid_direction(tmp_path) -> None:
    journeys_path = tmp_path / "journeys.csv"
    journeys_path.write_text(
        "user_id,station,direction,time\n"
        "user1,alpha,SIDEWAYS,2022-04-04T09:40:00\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid direction 'SIDEWAYS'"):
        read_journey_events(journeys_path)


def test_write_totals_sorts_users_and_formats_amounts(tmp_path) -> None:
    output_path = tmp_path / "output.csv"

    write_totals(
        output_path,
        {
            "bravo": Decimal("5"),
            "23Charlie": Decimal("3.3"),
            "alpha": Decimal("12.00"),
        },
    )

    assert output_path.read_text(encoding="utf-8") == (
        "23Charlie,3.30\nalpha,12.00\nbravo,5.00\n"
    )
