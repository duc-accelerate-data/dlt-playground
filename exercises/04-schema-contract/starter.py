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
    pipeline.run(events(day=1))
    # day 2 — introduces `experiment` column
    print('------------------------------')
    try:
        pipeline.run(events(day=2), schema_contract=policy)  # TODO: pass `policy`
    except Exception as e:
        print(f"[{dataset}] raised:", type(e).__name__, e)
    cols = pipeline.default_schema.get_table_columns("events").keys()
    print(f"[{dataset}] columns:", sorted(cols))
    print('------------------------------')


# TODO: call run_with_policy 3 times — evolve, freeze, discard_value.
policy_evolve = { # insert and update cols
    "tables": "evolve",
    "columns": "evolve",
    "data_type": "evolve",
}
dataset_evolve = 'bronze_events_evolve'

policy_freeze = { # throws err
    "tables": "evolve",
    "columns": "freeze",
    "data_type": "freeze",
}
dataset_freeze = 'bronze_events_freeze'

policy_discard = { # insert but do not update cols. silent fail
    "tables": "evolve",
    "columns": "discard_value",
    "data_type": "discard_value",
}
dataset_discard = 'bronze_events_discard'

run_with_policy(policy_evolve, dataset=dataset_evolve)
run_with_policy(policy_freeze, dataset=dataset_freeze)
run_with_policy(policy_discard, dataset=dataset_discard)