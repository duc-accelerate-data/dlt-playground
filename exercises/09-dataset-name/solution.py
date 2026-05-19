"""Reference solution for exercise 09."""
import os, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.chess_source import chess_source

env = os.environ.get("DLT_ENV", "dev")
dataset = f"bronze_chess_{env}"

pipeline = dlt.pipeline(
    pipeline_name=f"chess_{env}",
    destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
    dataset_name=dataset,
)
print(pipeline.run(chess_source()))
print(f"wrote to dataset: {dataset}")
