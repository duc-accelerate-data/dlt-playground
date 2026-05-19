"""Reference solution for exercise 04."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.synthetic_source import events


def run_with_policy(policy, dataset: str):
    pipeline = dlt.pipeline(
        pipeline_name=f"events_{dataset}",
        destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
        dataset_name=dataset,
    )
    pipeline.run(events(day=1))
    try:
        pipeline.run(events(day=2), schema_contract=policy)
    except Exception as e:
        print(f"[{dataset}] raised:", type(e).__name__, str(e)[:160])
    cols = pipeline.default_schema.get_table("events")["columns"].keys()
    print(f"[{dataset}] columns:", sorted(cols), "\n")


# Permissive — what dlt does by default.
run_with_policy({"tables": "evolve", "columns": "evolve", "data_type": "evolve"},
                "bronze_events_evolve")

# Strict bronze — production default for known-stable schemas.
run_with_policy({"tables": "evolve", "columns": "freeze", "data_type": "freeze"},
                "bronze_events_freeze")

# Forensic — log everything that fits, silently drop new fields.
run_with_policy({"tables": "evolve", "columns": "discard_value", "data_type": "discard_value"},
                "bronze_events_discard")
