"""Exercise 05 — replace vs append vs merge."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
import duckdb
from shared.synthetic_source import events as events_resource

WH = REPO / "data" / "warehouse.duckdb"


def load_for(disposition: str, dataset: str, primary_key=None):
    # TODO: build a resource that wraps events() but with the given disposition.
    # TODO: run day=1 then day=2 then day=1 then day=2 — 4 runs.
    # TODO: query the resulting count and print it.
    ...


load_for("replace", "wd_replace")
load_for("append",  "wd_append")
load_for("merge",   "wd_merge", primary_key="event_id")
