"""Verify exercise 11 — requires SOURCES__GITHUB__ACCESS_TOKEN."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_exists, db

header("11-state")
if not os.environ.get("SOURCES__GITHUB__ACCESS_TOKEN"):
    print("  ⚠ SKIP: set SOURCES__GITHUB__ACCESS_TOKEN to verify this exercise.")
    sys.exit(0)

run_solution(__file__)

check(table_exists("bronze_github_etag", "org_repos"), "org_repos table created")
state = db().execute(
    "SELECT state FROM bronze_github_etag._dlt_pipeline_state ORDER BY version DESC LIMIT 1"
).fetchone()
check(state is not None and b"etag" in (state[0] if isinstance(state[0], (bytes,bytearray)) else str(state[0]).encode()),
      "ETag is persisted in pipeline state")
done()
