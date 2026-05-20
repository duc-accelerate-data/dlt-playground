"""Exercise 07 — see what normalize does for free.

We load two endpoints that each exercise a different normalize behavior:
  - player_stats   → flattens deeply nested JSON into parent__child columns
  - archive_index  → splits the nested `archives` array into a child table
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
import duckdb
from shared.chess_source import player_stats, player_games_archive_index

WH = REPO / "data" / "warehouse.duckdb"

pipeline = dlt.pipeline(
    pipeline_name="chess_bronze",
    destination=dlt.destinations.duckdb(str(WH)),
    dataset_name="bronze_chess",
)
pipeline.run([
    player_stats(["magnuscarlsen"]),
    player_games_archive_index(["magnuscarlsen"]),
])

# TODO: list columns of bronze_chess.player_stats — find the `chess_*__last__rating` flattened cols.
# TODO: list tables in bronze_chess — find the `player_games_archive_index__archives` child table.
# TODO: join child.* _dlt_parent_id = parent._dlt_id and count archive months per player.
# TODO: join player_stats._dlt_load_id -> _dlt_loads.load_id and print the load timestamp.
