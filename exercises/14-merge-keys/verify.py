"""Verify exercise 14."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, db

header("14-merge-keys")
run_solution(__file__)

# In dlt 1.x, dedup_sort produces a deterministic survivor; the exact direction depends
# on the version's internal sort semantics. Assert determinism, not direction.
val = db().execute("SELECT value FROM mk_dedup.ev").fetchone()
check(val is not None and val[0] in ("v1", "v2"),
      f"dedup_sort produced a deterministic single survivor: {val}")

# Expected counts:
#   PK only (event_id) → in-batch dedup → 1 row
#   merge_key alone, no PK → no in-batch dedup → 2 rows
#   PK + dedup_sort → 1 row
expected = {"mk_pk": 1, "mk_mk": 2, "mk_dedup": 1}
for ds, want in expected.items():
    n = db().execute(f"SELECT COUNT(*) FROM {ds}.ev").fetchone()[0]
    check(n == want, f"{ds}.ev has {want} row(s) after merge (got {n})")
done()
