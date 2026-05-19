"""Reference solution for exercise 05."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
import duckdb
from shared.synthetic_source import events as events_resource

WH = REPO / "data" / "warehouse.duckdb"


def load_for(disposition: str, dataset: str, primary_key=None):
    @dlt.resource(name="events", write_disposition=disposition, primary_key=primary_key)
    def events(day: int):
        yield from events_resource(day=day)

    pipeline = dlt.pipeline(
        pipeline_name=f"wd_{disposition}",
        destination=dlt.destinations.duckdb(str(WH)),
        dataset_name=dataset,
        dev_mode=True,  # wipe between policies for a clean comparison
    )
    for day in (1, 2, 1, 2):
        pipeline.run(events(day))

    n = duckdb.connect(str(WH)).execute(f"SELECT COUNT(*) FROM {dataset}.events").fetchone()[0]
    print(f"{disposition:<8} rows={n}")


load_for("replace", "wd_replace")
load_for("append",  "wd_append")
load_for("merge",   "wd_merge", primary_key="event_id")
