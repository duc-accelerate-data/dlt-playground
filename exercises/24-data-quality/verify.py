"""Verify exercise 24."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, row_count, db

header("24-data-quality")
run_solution(__file__)

n = row_count("bronze_dq", "events")
check(n == 4, f"exactly 4 rows landed after filter+map+validate (got {n})")

leaked = db().execute(
    "SELECT COUNT(*) FROM bronze_dq.events WHERE email LIKE '%@%'"
).fetchone()[0]
check(leaked == 0, f"no email contains '@' (got {leaked} leaks)")

bad_age = db().execute(
    "SELECT COUNT(*) FROM bronze_dq.events WHERE age = 999"
).fetchone()[0]
check(bad_age == 0, f"out-of-range age=999 was nulled (residual rows={bad_age})")
done()
