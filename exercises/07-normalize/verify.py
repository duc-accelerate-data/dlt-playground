"""Verify exercise 07."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_columns, db, table_exists

header("07-normalize")
run_solution(__file__)

cols = table_columns("bronze_chess", "player_profile")
check("_dlt_id" in cols, "_dlt_id present")
check("_dlt_load_id" in cols, "_dlt_load_id present")
check(table_exists("bronze_chess", "player_profile__streaming_platforms")
      or any("__" in c for c in cols if not c.startswith("_dlt_")),
      "nested data extracted: child table or flattened column present")

joined = db().execute("""
    SELECT COUNT(*) FROM bronze_chess.player_profile p
    JOIN bronze_chess._dlt_loads l ON l.load_id = p._dlt_load_id
""").fetchone()[0]
check(joined > 0, f"profile rows join cleanly to _dlt_loads (got {joined})")
done()
