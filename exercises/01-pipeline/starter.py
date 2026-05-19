"""Exercise 01 — build a pipeline and load 3 chess profiles into DuckDB."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import dlt
from shared.chess_source import player_profile

# TODO: configure destination to land in ./data/warehouse.duckdb (relative to repo root)
destination = ...

# TODO: build a pipeline named "chess_bronze" with dataset "bronze_chess"
pipeline = ...

# TODO: run the player_profile resource for these three users
info = pipeline.run(player_profile(...))
print(info)
