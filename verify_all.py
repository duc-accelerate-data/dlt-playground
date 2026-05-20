"""Run every exercise's verify.py end-to-end and report pass / fail.

Each verifier executes its own `solution.py` (idempotent — uses dev_mode where it matters)
and then asserts post-conditions against the DuckDB warehouse. Skipped exercises (those
needing GitHub PAT or multi-section secrets) print "SKIP" instead of failing.

Usage:
    python verify_all.py                    # everything
    python verify_all.py 01 04 14           # selected exercises
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
EX_DIR = REPO / "exercises"


def main(filters: list[str]) -> int:
    exercises = sorted(d for d in EX_DIR.iterdir() if d.is_dir())
    failures: list[str] = []
    # Reset per-exercise state (DuckDB schemas + dlt pipeline dirs) so each
    # verifier starts clean and accumulated runs don't pollute each other.
    targets = [ex.name.split("-", 1)[0] for ex in exercises
               if not filters or any(ex.name.startswith(f) for f in filters)]
    subprocess.run([sys.executable, str(REPO / "reset.py"), *targets], cwd=REPO)
    for ex in exercises:
        if filters and not any(ex.name.startswith(f) for f in filters):
            continue
        verify = ex / "verify.py"
        if not verify.exists():
            print(f"\n!! {ex.name}: no verify.py")
            continue
        print(f"\n>>> {ex.name}")
        rc = subprocess.call([sys.executable, str(verify)], cwd=REPO)
        if rc != 0:
            failures.append(ex.name)

    print("\n" + "=" * 60)
    if failures:
        print(f"FAILED: {failures}")
        return 1
    print("ALL VERIFIERS PASSED (or skipped due to missing secrets)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
