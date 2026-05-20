"""Verify exercise 30."""
import os
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done

EX = Path(__file__).resolve().parent
SRC = os.environ.get("EXERCISE_SOURCE", "solution")
SOLUTION = EX / SRC / "solution.py"

header("30-evolving-pipeline")
if not SOLUTION.exists():
    check(False, f"no solution.py at {SOLUTION}")
    done()

ns = runpy.run_path(str(SOLUTION), run_name="__exercise__")
state = ns["STATE"]

check(state.get("step1_rows") == 3, f"step1 baseline users rows = 3 (got {state.get('step1_rows')})")
check(state.get("step2_users_rows") == 3 and state.get("step2_events_rows") == 2,
      f"step2 events added, users unchanged (users={state.get('step2_users_rows')}, events={state.get('step2_events_rows')})")
check(state.get("step3_has_country") is True, "step3 added `country` column to users")
check(state.get("step4_rows") == 4 and state.get("step4_updated") == "GB",
      f"step4 merge: 4 rows total, id=2 country updated to GB (got rows={state.get('step4_rows')}, country={state.get('step4_updated')})")
check(state.get("step5_rows") == 4 and state.get("step5_pk_is_email") is True,
      f"step5 PK migration: 4 rows after drop+reload (got {state.get('step5_rows')})")
check(state.get("step6_customers_rows") == 4 and state.get("step6_users_dropped") is True,
      f"step6 rename: customers loaded ({state.get('step6_customers_rows')} rows), old users table dropped ({state.get('step6_users_dropped')})")
done()
