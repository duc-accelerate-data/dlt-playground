"""Exercise 01 — build a pipeline and load 3 chess profiles into DuckDB."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dlt import pipeline, destinations
from shared.chess_source import chess_source

# print(pipeline)
# pipeline_name = 'test_p'
# pipeline_dest = 'duckdb'
# pipeline_dataset_name = = 'test_dataset'

# destination = 'duckdb' (unpinned)
path = str(Path(__file__).resolve().parents[2] / "data" / "warehouse.duckdb")
destination = destinations.duckdb(path)
dataset_name = 'bronze_chess'
chess_bronze = pipeline('chess_bronze', destination=destination, dataset_name=dataset_name)

usernames = ["magnuscarlsen", "hikaru", "liemle"]

info = chess_bronze.run(chess_source(usernames))
# print(info)
