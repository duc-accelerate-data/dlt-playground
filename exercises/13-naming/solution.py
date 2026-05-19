"""Reference solution for exercise 13."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import os, dlt


def run_with_naming(naming: str, dataset: str):
    # Naming is set on the schema; easiest knob is via env var before pipeline construction.
    os.environ["SCHEMA__NAMING"] = naming
    pipeline = dlt.pipeline(
        pipeline_name=f"naming_{naming}",
        destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
        dataset_name=dataset,
        dev_mode=True,
    )
    pipeline.run([{"FirstName": "Ada", "favouriteRepo": "dlt"}], table_name="people")
    cols = list(pipeline.default_schema.get_table("people")["columns"].keys())
    print(f"{naming:<12} -> {sorted(c for c in cols if not c.startswith('_dlt_'))}")


run_with_naming("snake_case", "naming_snake")
run_with_naming("direct",     "naming_direct")
