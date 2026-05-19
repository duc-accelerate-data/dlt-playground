"""Reference solution for exercise 14."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt, duckdb

WH = REPO / "data" / "warehouse.duckdb"


def two_versions():
    yield {"event_id": "e1", "user_id": "u1", "updated_at": "2026-05-10T08:00:00Z", "value": "v1"}
    yield {"event_id": "e1", "user_id": "u1", "updated_at": "2026-05-10T09:00:00Z", "value": "v2"}


def run(name, hints, dataset):
    @dlt.resource(name="ev", write_disposition="merge", **hints)
    def ev():
        yield from two_versions()

    p = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(WH)),
        dataset_name=dataset,
        dev_mode=True,
    )
    p.run(ev())
    rows = duckdb.connect(str(WH)).execute(f"SELECT value, updated_at FROM {dataset}.ev").fetchall()
    print(f"{name:<22} -> {rows}")


# 1) PK only — last writer in the load wins by insertion order.
run("pk_only", {"primary_key": "event_id"}, "mk_pk")

# 2) merge_key — composite match without strict PK.
run("merge_key", {"merge_key": ["user_id", "event_id"]}, "mk_mk")

# 3) PK + dedup_sort (desc on updated_at) → v2 wins deterministically.
run("pk_dedup_sort",
    {"primary_key": "event_id", "dedup_sort": ("updated_at", "desc")},
    "mk_dedup")
