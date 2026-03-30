# Mass Transit Billing

Python solution for the mass transit billing challenge.

The program reads:
- a station-to-zone mapping CSV
- a journey events CSV

and writes a per-user billing summary CSV.

## Structure

- `src/mass_transit_billing/`: application package
- `src/mass_transit_billing/helper/billing_csv.py`: CSV input/output helpers
- `src/mass_transit_billing/models/`: billing model types
- `src/mass_transit_billing/helper/billing_engine.py`: billing engine
- `tests/`: test suite

## Run

From the project root:

```bash
.venv/bin/python3 -m mass_transit_billing <zones_file_path> <journey_data_path> <output_file_path>
```

Example:

```bash
.venv/bin/python3 -m mass_transit_billing src/zone_map.csv src/journey_data.csv output.csv
```

## Setup

Create a local virtual environment and install the dev dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
make setup
```

## Format

```bash
make format
```

## Lint

```bash
make lint
```

## Test

```bash
make test
```

## Check Everything

```bash
make check
```

## High-Level Flow

The program runs in two stages:

1. Read and validate the CSV inputs.
2. Process journey events in order and accumulate charges.

### CSV Validation

While reading the input files, the code checks:

- required headers are present
- required values are not blank
- zone values are integers
- duplicate stations are rejected in the zone map
- direction is either `IN` or `OUT`
- timestamps can be parsed

### Billing Logic

At a high level, the engine handles events like this:

- `IN` with no open journey: start a journey
- `IN` with an existing open journey: charge `£5` for the earlier incomplete journey, then replace it
- `OUT` with no open journey: charge `£5`
- same-day `IN -> OUT` with known stations: charge base fare plus zone surcharges
- cross-day `IN -> OUT`: treat as two errors under the current policy
  first `£5` for the old open journey, then `£5` for the unmatched `OUT`
- unknown station names in journey data: treated as recoverable billing errors charged one ERROR_JOURNEY_FARE
- any open journey left at end of input: charged as `£5` in `finalize()`

Charges are passed through daily and monthly cap handling before totals are stored.

## Notes

- The CLI expects exactly three arguments: zones file, journey data file, and output file.
- Sample input, output file (generated from running this code) are under src/ directory
- The current implementation includes tests for CSV parsing, CLI wiring, engine processing, caps, `finalize()`, and `totals()`.
