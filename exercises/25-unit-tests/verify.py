"""Verify exercise 25 — runs pytest on the solution's unit tests."""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done

EX = Path(__file__).resolve().parent
SRC = os.environ.get("EXERCISE_SOURCE", "solution")
TEST_FILE = EX / SRC / "test_resources.py"

header("25-unit-tests")
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

# pytest -q ends with "N passed in Xs"
last_line = (proc.stdout.strip().splitlines() or [""])[-1]
check(proc.returncode == 0, f"pytest exited 0 ({last_line})")

# extract pass count
import re
m = re.search(r"(\d+) passed", proc.stdout)
passed = int(m.group(1)) if m else 0
check(passed >= 7, f"at least 7 unit tests passed (got {passed})")

# no real HTTP — responses raises ConnectionError if a stub is missing
check("ConnectionError" not in proc.stdout, "no un-stubbed HTTP requests escaped to the network")
done()
