"""Reference solution for exercise 18 — idempotency under different dispositions."""
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


# (1) append — duplicates on re-run
@dlt.resource(name="t", write_disposition="append")
def r_append():
    yield from [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}]


p = make_pipeline("idem_append")
p.run(r_append())
p.run(r_append())
print(f"(1) append              : rows after 2 runs = {count('idem_append')}  (expect 4 — NOT idempotent)")


# (2) merge + primary_key — upsert on re-run
@dlt.resource(name="t", primary_key="id", write_disposition="merge")
def r_merge():
    yield from [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}]


p = make_pipeline("idem_merge")
p.run(r_merge())
p.run(r_merge())
print(f"(2) merge + PK          : rows after 2 runs = {count('idem_merge')}  (expect 2 — idempotent)")


# (3) dev_mode=True — looks idempotent because target moves
p = make_pipeline("idem_dev", dev_mode=True)
p.run(r_merge())
p2 = make_pipeline("idem_dev", dev_mode=True)
p2.run(r_merge())
con = duckdb.connect(WH)
schemas = [r[0] for r in con.execute(
    "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'idem_dev%'"
).fetchall()]
print(f"(3) dev_mode=True       : {len(schemas)} schemas exist {schemas}  (FALSE positive — target moved each run)")


# (4) schema drift v1 -> v2 — data idempotent, schema is not
@dlt.resource(name="t", primary_key="id", write_disposition="merge")
def r_v1():
    yield {"id": 1, "name": "alice"}


@dlt.resource(name="t", primary_key="id", write_disposition="merge")
def r_v2():
    yield {"id": 1, "name": "alice", "email": "alice@x"}  # schema drifted


p = make_pipeline("idem_drift")
p.run(r_v1())
cols_before = sorted(p.default_schema.get_table("t")["columns"])
p.run(r_v2())
cols_after = sorted(p.default_schema.get_table("t")["columns"])
added = set(cols_after) - set(cols_before)
print(f"(4) schema drift        : rows={count('idem_drift')}, added cols={added}  (data idempotent, schema isn't)")


# (5) No PK -> no content-based dedup. Identical rows DO survive as duplicates.
# The foot-gun is the opposite belief: people expect content-hash dedup but dlt
# generates _dlt_id randomly per yielded item, not from content.
@dlt.resource(name="t", write_disposition="append")  # append + no PK
def r_no_pk_dupes():
    yield from [{"v": "a"}, {"v": "a"}]  # two identical rows


p = make_pipeline("idem_collision")
p.run(r_no_pk_dupes())
rows = count("idem_collision")
print(f"(5) no PK + identical   : yielded 2 identical rows, destination has {rows}  (both survive — no content dedup without PK)")
# Fix: declare primary_key + merge to dedupe properly.
