"""Verify exercise 07."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_columns, db, table_exists

header("07-normalize")
run_solution(__file__)

# (1) flattening — player_stats has parent__child columns
cols = table_columns("bronze_chess", "player_stats")
check("_dlt_id" in cols, "_dlt_id present on player_stats")
check("_dlt_load_id" in cols, "_dlt_load_id present on player_stats")
flattened = [c for c in cols if "__" in c and not c.startswith("_dlt_")]
check(len(flattened) > 0, f"player_stats has flattened columns (e.g. {flattened[:3]})")

# (2) child table — nested array spawned a child table
check(table_exists("bronze_chess", "player_games_archive_index__archives"),
      "child table player_games_archive_index__archives exists")

# (3) parent/child link via _dlt_parent_id
linked = db().execute("""
    SELECT COUNT(*) FROM bronze_chess.player_games_archive_index            p
    JOIN bronze_chess.player_games_archive_index__archives  c
      ON c._dlt_parent_id = p._dlt_id
""").fetchone()[0]
check(linked > 0, f"child rows link back to parent via _dlt_parent_id (got {linked})")

# (4) join to _dlt_loads
joined = db().execute("""
    SELECT COUNT(*) FROM bronze_chess.player_stats s
    JOIN bronze_chess._dlt_loads l ON l.load_id = s._dlt_load_id
""").fetchone()[0]
check(joined > 0, f"player_stats rows join cleanly to _dlt_loads (got {joined})")
done()
