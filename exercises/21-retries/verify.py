"""Verify exercise 21."""
import sys, importlib, runpy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, table_exists, row_count

header("21-retries")

# Run solution as a module so we can inspect the ATTEMPTS counter.
ns = runpy.run_path(str(Path(__file__).resolve().parent / "solution.py"), run_name="__exercise__")
attempts = ns["ATTEMPTS"]["n"]

check(attempts >= 1, f"the permanent-401 path executed (attempts seen={attempts})")
check(table_exists("resilience", "items"), "flaky endpoint eventually loaded into 'items'")
check(row_count("resilience", "items") == 2, "exactly 2 items landed after the 3 retries succeeded")
done()
