"""Reference solution for exercise 01."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.chess_source import player_profile

# Pin DuckDB to the repo so every exercise writes to the same warehouse file.
destination = dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb"))

pipeline = dlt.pipeline(
    pipeline_name="chess_bronze",
    destination=destination,
    dataset_name="bronze_chess",
)

info = pipeline.run(player_profile(["magnuscarlsen", "hikaru", "fabianocaruana"]))
print(info)
print("Tables:", [t["name"] for t in pipeline.default_schema.data_tables()])

# Inspect: SELECT * FROM bronze_chess.player_profile;
