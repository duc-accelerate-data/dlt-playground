"""Verify exercise 23."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, row_count

header("23-streaming")
run_solution(__file__)

for ds in ("stream_naive", "stream_smart"):
    n = row_count(ds, "rows")
    check(n == 100_000, f"{ds}.rows has 100,000 rows (got {n})")
done()
