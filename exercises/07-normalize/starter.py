"""Exercise 07 — see what normalize does for free."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
import duckdb
from shared.chess_source import player_profile

WH = REPO / "data" / "warehouse.duckdb"

pipeline = dlt.pipeline(
    pipeline_name="chess_bronze",
    destination=dlt.destinations.duckdb(str(WH)),
    dataset_name="bronze_chess",
)
pipeline.run(player_profile(["magnuscarlsen"]))

# TODO: print the column list of bronze_chess.player_profile and find the _dlt_* ones + a flattened col.
# TODO: join player_profile -> _dlt_loads on _dlt_load_id and print the load timestamp.
