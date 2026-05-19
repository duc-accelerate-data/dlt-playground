"""Reference solution for exercise 16."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.github_source import github_source


def run_for_section(section: str, org: str, dataset: str):
    pipeline = dlt.pipeline(
        pipeline_name=f"github_{section}",
        destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
        dataset_name=dataset,
    )
    # with_args(section=...) rebinds the TOML section for credentials resolution.
    src = github_source.with_args(section=section)(org=org)
    src = src.with_resources("repos")
    print(f"[{section}] -> {pipeline.run(src)}")


run_for_section("github_a", "dlt-hub", "bronze_github_a")
run_for_section("github_b", "duckdb",  "bronze_github_b")
