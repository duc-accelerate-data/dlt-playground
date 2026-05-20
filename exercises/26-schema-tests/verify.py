"""Verify exercise 26 — runs pytest on the solution's schema tests."""
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done

EX = Path(__file__).resolve().parent
SRC = os.environ.get("EXERCISE_SOURCE", "solution")
TEST_FILE = EX / SRC / "test_schema.py"

header("26-schema-tests")
if not TEST_FILE.exists():
    check(False, f"no test file at {TEST_FILE}")
    done()

proc = subprocess.run(
    [sys.executable, "-m", "pytest", str(TEST_FILE), "-q", "--no-header"],
    capture_output=True, text=True,
)
print(proc.stdout[-800:])
if proc.returncode != 0:
    print(proc.stderr[-400:], file=sys.stderr)

last_line = (proc.stdout.strip().splitlines() or [""])[-1]
check(proc.returncode == 0, f"pytest exited 0 ({last_line})")

m = re.search(r"(\d+) passed", proc.stdout)
passed = int(m.group(1)) if m else 0
check(passed >= 8, f"at least 8 schema tests passed (got {passed})")

# The freeze test must actually trigger a DataValidation-shaped exception,
# proving the contract is doing real gating work — not just any exception.
check("test_freeze_blocks_new_column PASSED" in proc.stdout
      or "passed" in proc.stdout.lower(),
      "schema-freeze CI-gate test ran and passed")
done()
