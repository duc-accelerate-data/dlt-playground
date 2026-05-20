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
info_first = pipeline.run(issues('duc-accelerate-data', 'monitoring-test', 'gho_REDACTED_USE_YOUR_OWN_PAT'))
print(pipeline.last_trace.last_normalize_info.row_counts)
print('------------------')
# TODO: run a second time and confirm 0 new rows.
info_second = pipeline.run(issues('duc-accelerate-data', 'monitoring-test', 'gho_REDACTED_USE_YOUR_OWN_PAT'))
print(pipeline.last_trace.last_normalize_info.row_counts)
# TODO: build a third pipeline (different dataset!) with initial_value + end_value to backfill March 2026.

pipeline_2 = dlt.pipeline(
    pipeline_name="github_bronze_backfill",
    destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
    dataset_name="bronze_github_backfill",
)
pipeline_2.run(issues('duc-accelerate-data', 'monitoring-test', 'gho_REDACTED_USE_YOUR_OWN_PAT', dlt.sources.incremental('updated_at', initial_value="2026-03-03T00:00:00Z", end_value="2026-03-31T11:59:59Z")))
print(pipeline_2.last_trace.last_normalize_info.row_counts)
