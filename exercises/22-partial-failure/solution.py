"""Reference solution for exercise 22.

Note: dlt's resume semantics differ slightly between extract-stage and
normalize-stage failures. This exercise crashes at extract time. To observe
resume behavior, we run the same pipeline twice — the second time without the
crash — and verify the destination ends up with all 5 rows and exactly one
successful load_id.
"""
import os, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt, duckdb

WH = REPO / "data" / "warehouse.duckdb"
CRASH_FLAG = REPO / "exercises" / "22-partial-failure" / ".crash"


@dlt.resource(name="numbers", primary_key="n", write_disposition="merge")
def numbers():
    for n in (1, 2):
        yield {"n": n}
    if CRASH_FLAG.exists():
        raise RuntimeError("simulated crash mid-extract")
    for n in (3, 4, 5):
        yield {"n": n}


def fresh_pipeline():
    return dlt.pipeline(
        pipeline_name="resume_demo",
        destination=dlt.destinations.duckdb(str(WH)),
        dataset_name="resume_demo",
    )


# Clean slate
duckdb.connect(str(WH)).execute("DROP SCHEMA IF EXISTS resume_demo CASCADE")

# --- Run 1: crash mid-extract ---
CRASH_FLAG.touch()
p1 = fresh_pipeline()
try:
    p1.run(numbers())
except RuntimeError as e:
    print(f"run 1 crashed (expected): {e}")
print(f"  has_pending_data={p1.has_pending_data}")

# --- Run 2: no crash, full replay ---
CRASH_FLAG.unlink(missing_ok=True)
p2 = fresh_pipeline()
print("run 2:", p2.run(numbers()))

con = duckdb.connect(str(WH))
n = con.execute("SELECT COUNT(*) FROM resume_demo.numbers").fetchone()[0]
loads = con.execute(
    "SELECT load_id, status FROM resume_demo._dlt_loads ORDER BY inserted_at"
).fetchall()
print(f"rows in destination = {n} (expected 5)")
print(f"_dlt_loads = {loads}  (status=0 means successful)")
