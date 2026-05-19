"""Verify exercise 14."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, db

header("14-merge-keys")
run_solution(__file__)

# dedup_sort=desc should pick v2 (the later updated_at) deterministically.
val = db().execute("SELECT value FROM mk_dedup.ev").fetchone()
check(val is not None and val[0] == "v2",
      f"dedup_sort kept v2 (the latest updated_at) — got {val}")

# All three datasets ended up with exactly one row after dedup.
for ds in ("mk_pk", "mk_mk", "mk_dedup"):
    n = db().execute(f"SELECT COUNT(*) FROM {ds}.ev").fetchone()[0]
    check(n == 1, f"{ds}.ev has 1 row after merge (got {n})")
done()
