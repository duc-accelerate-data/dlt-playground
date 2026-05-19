"""Reference solution for exercise 12."""
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
loads = con.execute(
    "SELECT load_id, inserted_at FROM bronze_chess._dlt_loads ORDER BY inserted_at"
).fetchall()
print("loads:", loads)

target = loads[1][0]
data_tables = [t["name"] for t in pipeline.default_schema.data_tables()]
for t in data_tables:
    con.execute(f"DELETE FROM bronze_chess.{t} WHERE _dlt_load_id = ?", [target])

print(f"after deleting load_id={target}:")
for t in data_tables:
    rows = con.execute(
        f"SELECT _dlt_load_id, COUNT(*) FROM bronze_chess.{t} GROUP BY 1 ORDER BY 1"
    ).fetchall()
    print(f"  {t}: {rows}")
