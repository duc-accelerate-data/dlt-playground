"""Run every exercise's verify_starter.py — checks your starter.py edits.

Same shape as verify_all.py but runs against starter.py (your work) instead
of solution.py (the reference). Exercises whose starter still has TODOs
(`...` placeholders) will fail loudly — that's the point.
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
    for ex in exercises:
        if filters and not any(ex.name.startswith(f) for f in filters):
            continue
        verify = ex / "verify_starter.py"
        if not verify.exists():
            continue
        print(f"\n>>> {ex.name}")
        rc = subprocess.call([sys.executable, str(verify)], cwd=REPO)
        if rc != 0:
            failures.append(ex.name)

    print("\n" + "=" * 60)
    if failures:
        print(f"FAILED (starter incomplete or buggy): {failures}")
        return 1
    print("ALL STARTER VERIFIERS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
