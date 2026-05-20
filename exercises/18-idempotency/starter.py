"""Exercise 18 — idempotency: when re-running is safe."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
import duckdb

WH = str(REPO / "data" / "warehouse.duckdb")


def make_pipeline(dataset: str, *, dev_mode: bool = False) -> dlt.Pipeline:
    return dlt.pipeline(
        pipeline_name=f"idem_{dataset}",
        destination=dlt.destinations.duckdb(WH),
        dataset_name=dataset,
        dev_mode=dev_mode,
    )


def count(schema: str, table: str = "t") -> int:
    con = duckdb.connect(WH)
    try:
        return con.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]
    except Exception:
        return -1


# TODO 1: build a resource with write_disposition="append" yielding 2 rows.
#         Run twice with dataset "idem_append". Print row count — expect 4.

# TODO 2: same 2 rows but with primary_key="id" + write_disposition="merge".
#         Run twice with dataset "idem_merge". Print row count — expect 2.

# TODO 3: make_pipeline("idem_dev", dev_mode=True). Run twice.
#         Query information_schema.schemata for schemas LIKE 'idem_dev%'. Expect 2.

# TODO 4: v1 resource yields {"id":1,"name":"alice"}; v2 yields {"id":1,"name":"alice","email":"a@x"}.
#         Both with primary_key="id" + merge. Run v1 then v2 into dataset "idem_drift".
#         Print row count (expect 1) and which columns were added.

# TODO 5: resource yielding [{"v":"a"},{"v":"a"}] — two identical rows, NO primary_key.
#         Run into dataset "idem_collision". Print row count — both rows survive (2).
#         Foot-gun: people expect content-hash dedup but dlt doesn't dedupe without a PK.
