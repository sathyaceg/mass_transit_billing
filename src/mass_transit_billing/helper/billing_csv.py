from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from mass_transit_billing.models.direction import Direction
from mass_transit_billing.models.journey_event import JourneyEvent

EXPECTED_ZONE_COLUMNS = {"station", "zone"}
EXPECTED_JOURNEY_COLUMNS = {"user_id", "station", "direction", "time"}


def read_zone_map(path: Path) -> dict[str, int]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        _validate_columns(path, reader.fieldnames, EXPECTED_ZONE_COLUMNS)

        zone_map: dict[str, int] = {}
        for line_number, row in enumerate(reader, start=2):
            station = _require_value(path, line_number, row, "station")
            zone_text = _require_value(path, line_number, row, "zone")

            try:
                zone = int(zone_text)
            except ValueError as exc:
                raise ValueError(
                    "Invalid zone value '{}' at {} line {}".format(
                        zone_text, path, line_number
                    )
                ) from exc

            if station in zone_map:
                raise ValueError(
                    "Duplicate station '{}' at {} line {}".format(
                        station, path, line_number
                    )
                )

            zone_map[station] = zone

    return zone_map


def read_journey_events(path: Path) -> list[JourneyEvent]:
    events: list[JourneyEvent] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        _validate_columns(path, reader.fieldnames, EXPECTED_JOURNEY_COLUMNS)

        for line_number, row in enumerate(reader, start=2):  # data starts from line 2
            user_id = _require_value(path, line_number, row, "user_id")
            station = _require_value(path, line_number, row, "station")
            direction_text = _require_value(path, line_number, row, "direction")
            timestamp_text = _require_value(path, line_number, row, "time")

            try:
                direction = Direction(direction_text)
            except ValueError as exc:
                raise ValueError(
                    "Invalid direction '{}' at {} line {}".format(
                        direction_text, path, line_number
                    )
                ) from exc

            try:
                timestamp = datetime.fromisoformat(timestamp_text)
            except ValueError as exc:
                raise ValueError(
                    "Invalid timestamp '{}' at {} line {}".format(
                        timestamp_text, path, line_number
                    )
                ) from exc

            events.append(
                JourneyEvent(
                    user_id=user_id,
                    station=station,
                    direction=direction,
                    timestamp=timestamp,
                )
            )

    return events


def write_totals(path: Path, totals: dict[str, Decimal]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for user_id in sorted(totals):
            writer.writerow((user_id, f"{totals[user_id]:.2f}"))


def _validate_columns(
    path: Path, fieldnames: list[str] | None, expected_columns: set[str]
) -> None:
    if fieldnames is None:
        raise ValueError("Missing header row in {}".format(path))

    actual_columns = set(fieldnames)
    if actual_columns != expected_columns:
        raise ValueError(
            "Expected columns {} but got {} in {}".format(
                sorted(expected_columns), sorted(actual_columns), path
            )
        )


def _require_value(
    path: Path, line_number: int, row: dict[str, str | None], key: str
) -> str:
    value = row.get(key)
    if value is None or not value.strip():
        raise ValueError(
            "Missing value for '{}' at {} line {}".format(key, path, line_number)
        )
    return value.strip()
