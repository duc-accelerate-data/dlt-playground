"""Verify exercise 22."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, row_count, db

header("22-partial-failure")
run_solution(__file__)

n = row_count("resume_demo", "numbers")
check(n == 5, f"all 5 numbers eventually landed (got {n})")
loads = db().execute(
    "SELECT load_id, status FROM resume_demo._dlt_loads ORDER BY inserted_at"
).fetchall()
successful = [l for l in loads if l[1] == 0]
check(len(successful) >= 1, f"at least one successful load_id (got {len(successful)})")
done()
