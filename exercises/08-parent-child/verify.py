"""Verify exercise 08."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_exists, row_count, db

header("08-parent-child")
run_solution(__file__)

check(table_exists("bronze_chess", "player_archive_url"), "child table exists")
check(row_count("bronze_chess", "player_archive_url") > 0, "child table has rows")

orphans = db().execute("""
    SELECT COUNT(*) FROM bronze_chess.player_archive_url WHERE _dlt_parent_id IS NULL
""").fetchone()[0]
check(orphans == 0, f"no orphan child rows (got {orphans} with NULL _dlt_parent_id)")

joined = db().execute("""
    SELECT COUNT(*) FROM bronze_chess.player_archive_url c
    JOIN bronze_chess.player_profile p ON p._dlt_id = c._dlt_parent_id
""").fetchone()[0]
check(joined == row_count("bronze_chess", "player_archive_url"),
      "every child row joins to a parent on _dlt_parent_id = _dlt_id")
done()
