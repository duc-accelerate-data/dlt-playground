"""Exercise 12 — roll back a specific load_id."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt, duckdb
from shared.chess_source import chess_source

WH = REPO / "data" / "warehouse.duckdb"

pipeline = dlt.pipeline(
    pipeline_name="chess_bronze",
    destination=dlt.destinations.duckdb(str(WH)),
    dataset_name="bronze_chess",
)
for _ in range(3):
    pipeline.run(chess_source())

con = duckdb.connect(str(WH))
# TODO: print all load_ids from bronze_chess._dlt_loads
# TODO: pick the middle one and DELETE FROM each data table WHERE _dlt_load_id = ?
# TODO: print row counts per load_id after the cleanup
