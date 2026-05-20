"""Reference solution for exercise 19 — bounded-window backfill."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
import duckdb

WH = str(REPO / "data" / "warehouse.duckdb")


EVENTS = [
    {"id": 1, "ts": "2026-01-15T00:00:00Z", "v": "jan"},
    {"id": 2, "ts": "2026-02-01T00:00:00Z", "v": "feb-boundary"},   # exact boundary value
    {"id": 3, "ts": "2026-02-15T00:00:00Z", "v": "feb"},
    {"id": 4, "ts": "2026-03-15T00:00:00Z", "v": "mar"},
    {"id": 5, "ts": "2026-04-15T00:00:00Z", "v": "apr"},
    {"id": 6, "ts": "2026-05-15T00:00:00Z", "v": "may"},
]


def make_resource(default_incremental=None):
    """Resource factory — caller chooses the incremental."""
    @dlt.resource(name="events", primary_key="id", write_disposition="merge")
    def events(ts=default_incremental or dlt.sources.incremental("ts", initial_value="1990-01-01T00:00:00Z")):
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


# (1) Bounded window pulls only rows in [Feb 1, Apr 1) — ids 2, 3, 4
p = make_pipeline("backfill_window")
p.run(make_resource(dlt.sources.incremental(
    "ts", initial_value="2026-02-01T00:00:00Z", end_value="2026-04-01T00:00:00Z",
))())
print(f"(1) window [Feb,Apr)   : {count('backfill_window')} rows  (expect 3 — boundary + feb + mar)")


# (2) Production + backfill don't interfere — separate pipelines/datasets
prod = make_pipeline("prod_stream")
prod.run(make_resource()())  # default (unbounded) — pulls all 6
bf = make_pipeline("prod_backfill")
bf.run(make_resource(dlt.sources.incremental(
    "ts", initial_value="2026-02-01T00:00:00Z", end_value="2026-04-01T00:00:00Z",
))())
print(f"(2) prod + backfill    : prod={count('prod_stream')}, backfill={count('prod_backfill')}  (5+1=6 prod, 3 backfill)")
# Check that production's incremental cursor was persisted, backfill's was not
prod_state = prod.state.get("sources", {})
bf_state = bf.state.get("sources", {})
print(f"     prod state keys   : {list(prod_state)}")
print(f"     backfill state    : {list(bf_state)}  (backfill mode = no persisted cursor)")


# (3) Three monthly backfills into three datasets
for label, start, end, expected in [
    ("jan", "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", 1),
    ("feb", "2026-02-01T00:00:00Z", "2026-03-01T00:00:00Z", 2),  # boundary + feb-15
    ("mar", "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", 1),
]:
    p = make_pipeline(f"backfill_{label}")
    p.run(make_resource(dlt.sources.incremental("ts", initial_value=start, end_value=end))())
    print(f"(3) {label} window      : {count(f'backfill_{label}')} rows  (expect {expected})")


# (4) range_start closed vs open — boundary row (Feb 1) inclusion
p = make_pipeline("range_closed")
p.run(make_resource(dlt.sources.incremental(
    "ts", initial_value="2026-02-01T00:00:00Z", end_value="2026-02-16T00:00:00Z",
    range_start="closed",  # default — ≥
))())
print(f"(4a) range_start=closed: {count('range_closed')} rows  (expect 2 — boundary + feb-15)")

p = make_pipeline("range_open")
p.run(make_resource(dlt.sources.incremental(
    "ts", initial_value="2026-02-01T00:00:00Z", end_value="2026-02-16T00:00:00Z",
    range_start="open",  # >
))())
print(f"(4b) range_start=open  : {count('range_open')} rows  (expect 1 — feb-15 only, boundary excluded)")


# (5) Idempotent re-run within bounded window
p = make_pipeline("backfill_idem")
incremental_args = dict(
    cursor_path="ts", initial_value="2026-02-01T00:00:00Z", end_value="2026-04-01T00:00:00Z",
)
p.run(make_resource(dlt.sources.incremental(**incremental_args))())
first = count("backfill_idem")
p.run(make_resource(dlt.sources.incremental(**incremental_args))())
second = count("backfill_idem")
print(f"(5) re-run same window : {first} -> {second}  (expect 3 -> 3, no growth, no dupes)")
