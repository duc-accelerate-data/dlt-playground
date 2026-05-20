"""Exercise 04 — schema contracts in three flavours."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.synthetic_source import events


def run_with_policy(policy: dict, dataset: str):
    pipeline = dlt.pipeline(
        pipeline_name=f"events_{dataset}",
        destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
        dataset_name=dataset,
    )
    # day 1 — establishes the schema
    # pipeline.run(events(day=1))
    # day 2 — introduces `experiment` column
    try:
        pipeline.run(events(day=2))  # TODO: pass `policy`
    except Exception as e:
        print(f"[{dataset}] raised:", type(e).__name__, e)
    cols = pipeline.default_schema.get_table_columns("events").keys()
    print(f"[{dataset}] columns:", sorted(cols))


# TODO: call run_with_policy 3 times — evolve, freeze, discard_value.
policy = {}
dataset = 'bronze_events'
run_with_policy(policy, dataset = dataset)