from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from mass_transit_billing import __main__
from mass_transit_billing.models.direction import Direction
from mass_transit_billing.models.journey_event import JourneyEvent


class FakeBillingEngine:
    def __init__(self, zone_map: dict[str, int]) -> None:
        self.zone_map = zone_map
        self.processed_events: list[JourneyEvent] = []
        self.finalized = False

    def process(self, event: JourneyEvent) -> None:
        self.processed_events.append(event)

    def finalize(self) -> None:
        self.finalized = True

    def totals(self) -> dict[str, Decimal]:
        return {"alpha": Decimal("7.50")}


def test_main_returns_error_for_wrong_argument_count(capsys) -> None:
    exit_code = __main__.main([])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Usage: python -m mass_transit_billing" in captured.err


def test_main_reads_inputs_processes_events_and_writes_output(
    monkeypatch, tmp_path
) -> None:
    zones_path = tmp_path / "zones.csv"
    journeys_path = tmp_path / "journeys.csv"
    output_path = tmp_path / "output.csv"

    fake_events = [
        JourneyEvent(
            user_id="user1",
            station="alpha",
            direction=Direction.IN,
            timestamp=datetime(2022, 4, 4, 9, 40, 0),
        )
    ]
    created_engines: list[FakeBillingEngine] = []

    def fake_read_zone_map(path):
        assert path == zones_path
        return {"alpha": 1}

    def fake_read_journey_events(path):
        assert path == journeys_path
        return fake_events

    def fake_write_totals(path, totals):
        assert path == output_path
        assert totals == {"alpha": Decimal("7.50")}
        path.write_text("alpha,7.50\n", encoding="utf-8")

    def fake_engine_factory(zone_map):
        engine = FakeBillingEngine(zone_map)
        created_engines.append(engine)
        return engine

    monkeypatch.setattr(__main__, "read_zone_map", fake_read_zone_map)
    monkeypatch.setattr(__main__, "read_journey_events", fake_read_journey_events)
    monkeypatch.setattr(__main__, "write_totals", fake_write_totals)
    monkeypatch.setattr(__main__, "BillingEngine", fake_engine_factory)

    exit_code = __main__.main([str(zones_path), str(journeys_path), str(output_path)])

    engine = created_engines[0]
    assert exit_code == 0
    assert engine.zone_map == {"alpha": 1}
    assert engine.processed_events == fake_events
    assert engine.finalized is True
    assert output_path.read_text(encoding="utf-8") == "alpha,7.50\n"
