"""Verify exercise 27 — runs pytest on the solution's business checks."""
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done

EX = Path(__file__).resolve().parent
SRC = os.environ.get("EXERCISE_SOURCE", "solution")
TEST_FILE = EX / SRC / "test_business.py"

header("27-business-checks")
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
check(passed >= 7, f"at least 7 business checks passed (got {passed})")
done()
