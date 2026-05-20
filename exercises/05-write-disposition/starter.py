"""Exercise 05 — replace vs append vs merge."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
import json
import duckdb
from shared.synthetic_source import events as events_resource
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "synthetic"

WH = REPO / "data" / "warehouse.duckdb"



def load_for(disposition: str, dataset: str, primary_key=None):
    # TODO: build a resource that wraps events() but with the given disposition.
    @dlt.resource(name="events", write_disposition=disposition, primary_key=primary_key)
    def events(day: int):
        path = DATA_DIR / f"events_day{day}.jsonl"
        with path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    
    pipeline = dlt.pipeline(
        pipeline_name=f"events_{dataset}",
        destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
        dataset_name=dataset,
    )
    
    # TODO: run day=1 then day=2 then day=1 then day=2 — 4 runs.
    pipeline.run(events(day=1))
    pipeline.run(events(day=2))
    pipeline.run(events(day=1))
    pipeline.run(events(day=2))
    # TODO: query the resulting count and print it.
    ...


load_for("replace", "wd_replace")
load_for("append",  "wd_append")
load_for("merge",   "wd_merge", primary_key="event_id")
