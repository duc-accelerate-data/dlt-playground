"""Reference solution for exercise 06."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.github_source import issues


def make_pipeline(dataset: str):
    return dlt.pipeline(
        pipeline_name=f"github_{dataset}",
        destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
        dataset_name=dataset,
    )


# 1) Standard incremental — first call grabs everything from initial_value.
p = make_pipeline("bronze_github")
print("RUN 1:", p.run(issues(org="dlt-hub", repo="dlt")))
# 2) Second call should be ~zero rows.
print("RUN 2:", p.run(issues(org="dlt-hub", repo="dlt")))

# 3) Targeted backfill into a separate dataset (so we don't pollute the main one).
p_bf = make_pipeline("backfill_march")
bf = issues(org="dlt-hub", repo="dlt")
# Override the incremental at call site:
bf.apply_hints(incremental=dlt.sources.incremental(
    "updated_at",
    initial_value="2026-03-01T00:00:00Z",
    end_value="2026-04-01T00:00:00Z",
))
print("BACKFILL:", p_bf.run(bf))
