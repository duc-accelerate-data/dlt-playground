"""Exercise 22 — crash mid-extract, then resume on next run."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt

CRASH_FLAG = REPO / "exercises" / "22-partial-failure" / ".crash"


@dlt.resource(name="numbers", primary_key="n", write_disposition="merge")
def numbers():
    # TODO: yield 1, 2 then raise RuntimeError("simulated crash") if CRASH_FLAG exists
    # TODO: yield 3, 4, 5 only if CRASH_FLAG does not exist
    ...


# TODO: write CRASH_FLAG, run pipeline, catch the exception, print pipeline.has_pending_data
# TODO: delete CRASH_FLAG, run again, verify all 5 rows present.
