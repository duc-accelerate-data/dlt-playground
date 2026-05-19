"""Verify exercise 10 — requires SOURCES__GITHUB__ACCESS_TOKEN."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_exists, row_count

header("10-verified-source")
if not os.environ.get("SOURCES__GITHUB__ACCESS_TOKEN"):
    print("  ⚠ SKIP: set SOURCES__GITHUB__ACCESS_TOKEN to verify this exercise.")
    sys.exit(0)

run_solution(__file__)

check(table_exists("bronze_github_subset", "issues"), "issues table loaded")
check(not table_exists("bronze_github_subset", "repos"),
      "repos NOT loaded (.with_resources subset honored)")
check(row_count("bronze_github_subset", "issues") > 0, "issues has rows")
done()
