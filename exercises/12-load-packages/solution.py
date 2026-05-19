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
# Only top-level tables get _dlt_load_id; child tables (__) inherit through _dlt_parent_id.
for t in data_tables:
    cols = {r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='bronze_chess' AND table_name=?", [t]).fetchall()}
    if "_dlt_load_id" in cols:
        con.execute(f"DELETE FROM bronze_chess.{t} WHERE _dlt_load_id = ?", [target])

print(f"after deleting load_id={target}:")
for t in data_tables:
    cols = {r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='bronze_chess' AND table_name=?", [t]).fetchall()}
    if "_dlt_load_id" in cols:
        rows = con.execute(
            f"SELECT _dlt_load_id, COUNT(*) FROM bronze_chess.{t} GROUP BY 1 ORDER BY 1"
        ).fetchall()
        print(f"  {t}: {rows}")
