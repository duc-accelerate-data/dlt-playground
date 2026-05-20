"""Exercise 01 — build a pipeline and load 3 chess profiles into DuckDB."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dlt import pipeline, destinations
from shared.chess_source import player_profile

# print(pipeline)
# pipeline_name = 'test_p'
# pipeline_dest = 'duckdb'
# pipeline_dataset_name = = 'test_dataset'

# TODO: configure destination to land in ./data/warehouse.duckdb (relative to repo root)
# destination = 'duckdb' (unpinned)
path = str(Path(__file__).resolve().parents[2] / "data" / "warehouse.duckdb")
destination = destinations.duckdb(path)

# TODO: build a pipeline named "chess_bronze" with dataset "bronze_chess"
dataset_name = 'bronze_chess'
chess_bronze = pipeline('chess_bronze', destination=destination, dataset_name=dataset_name)

usernames = ["magnuscarlsen", "hikaru", "liemle"]

# TODO: run the player_profile resource for these three users
info = chess_bronze.run(player_profile(usernames))
# print(info)
