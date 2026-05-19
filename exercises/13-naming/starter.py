"""Exercise 13 — naming conventions."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt


def run_with_naming(naming: str, dataset: str):
    # TODO: build a pipeline whose schema uses `naming`.
    # TODO: pipeline.run([{"FirstName": "Ada", "favouriteRepo": "dlt"}], table_name="people")
    # TODO: print resulting column names.
    ...


run_with_naming("snake_case", "naming_snake")
run_with_naming("direct",     "naming_direct")
