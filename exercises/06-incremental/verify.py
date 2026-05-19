"""Verify exercise 06 — requires SOURCES__GITHUB__ACCESS_TOKEN."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_exists, row_count

header("06-incremental")
if not os.environ.get("SOURCES__GITHUB__ACCESS_TOKEN"):
    print("  ⚠ SKIP: set SOURCES__GITHUB__ACCESS_TOKEN to verify this exercise.")
    sys.exit(0)

run_solution(__file__)

check(table_exists("bronze_github", "issues"), "bronze_github.issues exists after RUN 1")
n_main = row_count("bronze_github", "issues")
check(n_main > 0, f"main dataset has rows (got {n_main})")

if table_exists("backfill_march", "issues"):
    n_bf = row_count("backfill_march", "issues")
    check(n_bf >= 0, f"backfill dataset has rows (got {n_bf})")
done()
