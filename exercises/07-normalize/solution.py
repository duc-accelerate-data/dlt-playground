"""Reference solution for exercise 07."""
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

con = duckdb.connect(str(WH))
print("\n-- columns --")
for col in con.execute(
    "SELECT column_name, data_type FROM information_schema.columns "
    "WHERE table_schema='bronze_chess' AND table_name='player_profile' "
    "ORDER BY ordinal_position"
).fetchall():
    print(" ", col)

print("\n-- join to _dlt_loads --")
print(con.execute("""
    SELECT p.username, l.inserted_at, l.status
    FROM bronze_chess.player_profile p
    JOIN bronze_chess._dlt_loads     l ON l.load_id = p._dlt_load_id
""").fetchall())
