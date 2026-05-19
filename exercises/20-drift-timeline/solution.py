"""Reference solution for exercise 20."""
import json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt, duckdb

DATA = REPO / "data" / "synthetic" / "drift-timeline"
WH = REPO / "data" / "warehouse.duckdb"


@dlt.resource(name="people", primary_key="id", write_disposition="merge")
def people(version: int):
    with (DATA / f"v{version}.jsonl").open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def run_scenario(label: str, policy: dict):
    print(f"\n=== {label} :: {policy} ===")
    dataset = f"drift_{label}"
    pipeline = dlt.pipeline(
        pipeline_name=f"drift_{label}",
        destination=dlt.destinations.duckdb(str(WH)),
        dataset_name=dataset,
        dev_mode=True,
    )
    for v in (1, 2, 3, 4):
        raised = None
        try:
            pipeline.run(people(v), schema_contract=policy)
        except Exception as e:
            raised = type(e).__name__
        try:
            cols = sorted(c for c in pipeline.default_schema.get_table("people")["columns"]
                          if not c.startswith("_dlt_"))
            rows = duckdb.connect(str(WH)).execute(f"SELECT COUNT(*) FROM {dataset}.people").fetchone()[0]
        except Exception:
            cols, rows = [], 0
        print(f"  v{v}: raised={raised:<22}  rows={rows}  cols={cols}")


run_scenario("permissive", {"tables": "evolve", "columns": "evolve", "data_type": "evolve"})
run_scenario("strict",     {"tables": "evolve", "columns": "freeze", "data_type": "freeze"})
run_scenario("hybrid",     {"tables": "evolve", "columns": "evolve", "data_type": "freeze"})

# Production checklist (printed for the reader):
print("""
Promotion checklist by transition:
  v1 -> v2 (column add)    : safe. Bronze evolves columns. Downstream should reference cols explicitly.
  v2 -> v3 (column rename) : NOT safe automatically. Old column lingers NULL-filled.
                              Action: create silver view aliasing full_name <- coalesce(full_name, name),
                              then drop `name` from bronze in a separate migration.
  v3 -> v4 (type widen)    : freeze in prod. Action: explicit migration — add `age_str`, dual-write,
                              cut downstream over, drop `age_int`.
""")
