"""Exercise 06 — incremental cursor over GitHub issues."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.github_source import issues

pipeline = dlt.pipeline(
    pipeline_name="github_bronze",
    destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
    dataset_name="bronze_github",
)

# TODO: run once with the resource's default incremental.
# TODO: run a second time and confirm 0 new rows.
# TODO: build a third pipeline (different dataset!) with initial_value + end_value to backfill March 2026.
