"""Verify exercise 12."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, db

header("12-load-packages")
run_solution(__file__)

loads = db().execute("SELECT load_id FROM bronze_chess._dlt_loads ORDER BY inserted_at").fetchall()
check(len(loads) >= 3, f"at least 3 load_ids in _dlt_loads (got {len(loads)})")

# After the rollback, the second load's rows should be gone from the data tables.
target = loads[1][0]
n = db().execute(
    "SELECT COUNT(*) FROM bronze_chess.player_profile WHERE _dlt_load_id = ?", [target]
).fetchone()[0]
check(n == 0, f"second load_id rolled back from player_profile (got {n} residual rows)")
done()
