"""Exercise 19 — bounded-window backfill."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
import duckdb

WH = str(REPO / "data" / "warehouse.duckdb")


EVENTS = [
    {"id": 1, "ts": "2026-01-15T00:00:00Z", "v": "jan"},
    {"id": 2, "ts": "2026-02-01T00:00:00Z", "v": "feb-boundary"},
    {"id": 3, "ts": "2026-02-15T00:00:00Z", "v": "feb"},
    {"id": 4, "ts": "2026-03-15T00:00:00Z", "v": "mar"},
    {"id": 5, "ts": "2026-04-15T00:00:00Z", "v": "apr"},
    {"id": 6, "ts": "2026-05-15T00:00:00Z", "v": "may"},
]


def make_resource(incremental):
    @dlt.resource(name="events", primary_key="id", write_disposition="merge")
    def events(ts=incremental):
        for e in EVENTS:
            yield e
    return events


def make_pipeline(dataset: str) -> dlt.Pipeline:
    return dlt.pipeline(
        pipeline_name=f"backfill_{dataset}",
        destination=dlt.destinations.duckdb(WH),
        dataset_name=dataset,
    )


def count(schema: str) -> int:
    return duckdb.connect(WH).execute(f"SELECT COUNT(*) FROM {schema}.events").fetchone()[0]


# TODO 1: backfill window [Feb 1, Apr 1) into dataset "backfill_window". Expect 3 rows.

# TODO 2: prod pipeline (no end_value) into "prod_stream" — pulls all 6.
#         Separate backfill pipeline with [Feb 1, Apr 1) into "prod_backfill" — pulls 3.
#         Confirm neither row count changes after both run.

# TODO 3: three monthly backfills (jan/feb/mar) into "backfill_jan"/"backfill_feb"/"backfill_mar".
#         Expect 1/2/1 rows respectively.

# TODO 4: backfill [Feb 1, Feb 16) with range_start="closed" → 2 rows (boundary + feb-15).
#         Same window with range_start="open" → 1 row (feb-15 only).

# TODO 5: backfill [Feb 1, Apr 1) into "backfill_idem". Run twice. Row count must not grow.
