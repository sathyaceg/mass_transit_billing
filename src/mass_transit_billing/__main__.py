from __future__ import annotations

import sys
from pathlib import Path

from mass_transit_billing.helper.billing_csv import (
    read_journey_events,
    read_zone_map,
    write_totals,
)
from mass_transit_billing.helper.billing_engine import BillingEngine


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 3:
        print(
            "Usage: python -m mass_transit_billing "
            "<zones_file_path> <journey_data_path> <output_file_path>",
            file=sys.stderr,
        )
        return 1

    zones_path = Path(args[0])
    journeys_path = Path(args[1])
    output_path = Path(args[2])

    zone_map = read_zone_map(zones_path)
    events = read_journey_events(journeys_path)

    engine = BillingEngine(zone_map)
    for event in events:
        engine.process(event)

    engine.finalize()  # finalize any left over "errored" open journeys
    write_totals(output_path, engine.totals())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
