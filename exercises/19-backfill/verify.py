"""Verify exercise 19."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, db

header("19-backfill")
run_solution(__file__)

con = db()


def count(schema: str) -> int:
    return con.execute(f"SELECT COUNT(*) FROM {schema}.events").fetchone()[0]


# (1) bounded window
check(count("backfill_window") == 3, f"window [Feb,Apr) = 3 rows (got {count('backfill_window')})")

# (2) isolation — prod and backfill independent
check(count("prod_stream") == 6, f"prod = 6 rows (got {count('prod_stream')})")
check(count("prod_backfill") == 3, f"backfill = 3 rows (got {count('prod_backfill')})")

# (3) monthly splits
check(count("backfill_jan") == 1, f"jan = 1 row (got {count('backfill_jan')})")
check(count("backfill_feb") == 2, f"feb = 2 rows (got {count('backfill_feb')})")
check(count("backfill_mar") == 1, f"mar = 1 row (got {count('backfill_mar')})")

# (4) range_start boundary
check(count("range_closed") == 2, f"range_start=closed = 2 rows (got {count('range_closed')})")
check(count("range_open") == 1, f"range_start=open = 1 row (got {count('range_open')})")

# (5) idempotent re-run
check(count("backfill_idem") == 3, f"idempotent: still 3 rows after re-run (got {count('backfill_idem')})")

done()
