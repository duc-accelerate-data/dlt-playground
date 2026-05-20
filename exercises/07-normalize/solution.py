"""Reference solution for exercise 07 — observe the three things normalize does:

1. Flatten nested objects → `parent__child` columns (via player_stats).
2. Split nested arrays into child tables linked by _dlt_parent_id (via archive_index).
3. Inject control columns _dlt_id / _dlt_load_id on every table.
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

con = duckdb.connect(str(WH))

print("\n-- (1) flattening: player_stats columns --")
for col in con.execute(
    "SELECT column_name, data_type FROM information_schema.columns "
    "WHERE table_schema='bronze_chess' AND table_name='player_stats' "
    "ORDER BY ordinal_position"
).fetchall():
    print(" ", col)
# Look for `chess_blitz__last__rating`, `chess_blitz__record__win`, etc.

print("\n-- (2) child table: archive_index spawned __archives --")
for t in con.execute(
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema='bronze_chess' ORDER BY table_name"
).fetchall():
    print(" ", t[0])
# Note: `player_games_archive_index__archives` is the child of the nested `archives` array.

print("\n-- (3) parent/child link via _dlt_parent_id --")
print(con.execute("""
    SELECT p.username, COUNT(c._dlt_id) AS month_count
    FROM bronze_chess.player_games_archive_index            p
    JOIN bronze_chess.player_games_archive_index__archives  c
      ON c._dlt_parent_id = p._dlt_id
    GROUP BY p.username
""").fetchall())

print("\n-- (4) join control columns to _dlt_loads --")
print(con.execute("""
    SELECT s.username, l.inserted_at, l.status
    FROM bronze_chess.player_stats s
    JOIN bronze_chess._dlt_loads   l ON l.load_id = s._dlt_load_id
""").fetchall())
