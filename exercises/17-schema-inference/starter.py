"""Exercise 17 — schema inference: how dlt picks SQL types from JSON."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt


WH = str(REPO / "data" / "warehouse.duckdb")


def types_of(pipeline: dlt.Pipeline, table: str) -> dict[str, str]:
    cols = pipeline.default_schema.get_table(table)["columns"]
    return {c: meta.get("data_type", "?") for c, meta in cols.items() if not c.startswith("_dlt_")}


def make_pipeline(dataset: str) -> dlt.Pipeline:
    return dlt.pipeline(
        pipeline_name=f"infer_{dataset}",
        destination=dlt.destinations.duckdb(WH),
        dataset_name=dataset,
    )


# TODO 1: load {"id": 42, "name": "alice", "score": 3.14, "active": True} into dataset "infer_first"
#         then print types_of(p, "t") — confirm id=bigint, name=text, score=double, active=bool.

# TODO 2: load {"id": 1, "note": None} then {"id": 2, "note": "x"} into dataset "infer_nullable".
#         Print the `note` column meta — confirm data_type=text and nullable=True.

# TODO 3: load {"id": 1, "created": "2026-01-01T00:00:00Z"} into dataset "infer_iso".
#         Print types — confirm `created` was auto-detected as `timestamp`, not `text`.

# TODO 4: load {"x": 42}, then {"x": "forty-two"} with schema_contract={"data_type": "evolve"}
#         into dataset "infer_variant". Print types — confirm both `x` (bigint) AND `x__v_text` (text) exist.

# TODO 5: same drift as 4 but with data_type="freeze". Wrap in try/except, print the inner exception class.
