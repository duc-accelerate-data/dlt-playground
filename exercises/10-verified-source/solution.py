"""Reference solution for exercise 10."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.github_source import github_source

src = github_source(org="dlt-hub")
src = src.with_resources("issues")
src.issues.apply_hints(
    write_disposition="merge",
    primary_key="id",
    schema_contract={"tables": "evolve", "columns": "freeze", "data_type": "freeze"},
    incremental=dlt.sources.incremental("updated_at", initial_value="2026-01-01T00:00:00Z"),
)

pipeline = dlt.pipeline(
    pipeline_name="github_subset",
    destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
    dataset_name="bronze_github_subset",
)
print(pipeline.run(src))
