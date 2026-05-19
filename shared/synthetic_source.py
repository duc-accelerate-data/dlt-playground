"""Synthetic file-based source — drives schema-drift / dedup / normalize exercises."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import dlt

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"


@dlt.resource(name="events", primary_key="event_id", write_disposition="merge")
def events(day: int = 1):
    """Yields events from one day's JSONL file. day=2 introduces:
      - a new column `experiment` (schema drift)
      - one duplicate row (event_id=e3 from day 1) — tests dedup on primary_key
    """
    path = DATA_DIR / f"events_day{day}.jsonl"
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


@dlt.resource(name="products", primary_key="sku", write_disposition="merge")
def products():
    """The CSV has dirty booleans (true/TRUE/1) and a missing date — exercise 04 fights this."""
    with (DATA_DIR / "products.csv").open() as f:
        yield from csv.DictReader(f)


@dlt.source(name="synthetic")
def synthetic_source(event_day: int = 1):
    return [events(day=event_day), products()]
