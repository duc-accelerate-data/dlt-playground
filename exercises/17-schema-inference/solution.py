"""Reference solution for exercise 17 — schema inference + variant columns."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from dlt.common.exceptions import DltException


WH = str(REPO / "data" / "warehouse.duckdb")


def types_of(pipeline: dlt.Pipeline, table: str) -> dict[str, str]:
    cols = pipeline.default_schema.get_table(table)["columns"]
    return {c: meta.get("data_type", "?") for c, meta in cols.items() if not c.startswith("_dlt_")}


def make_pipeline(dataset: str) -> dlt.Pipeline:
    return dlt.pipeline(
        pipeline_name=f"infer_{dataset}",
        destination=dlt.destinations.duckdb(WH),
        dataset_name=dataset,
    )


# (1) First-sight inference
p = make_pipeline("infer_first")
p.run([{"id": 42, "name": "alice", "score": 3.14, "active": True}], table_name="t")
print("\n(1) first-sight :", types_of(p, "t"))

# (2) Nullable inference
p = make_pipeline("infer_nullable")
p.run([{"id": 1, "note": None}], table_name="t")
p.run([{"id": 2, "note": "x"}], table_name="t")
note_col = p.default_schema.get_table("t")["columns"].get("note", {})
print("(2) nullable     :", {"data_type": note_col.get("data_type"), "nullable": note_col.get("nullable")})

# (3) ISO-8601 auto-detect
p = make_pipeline("infer_iso")
p.run([{"id": 1, "created": "2026-01-01T00:00:00Z"}], table_name="t")
print("(3) iso-detect   :", types_of(p, "t"))

# (4) Variant column on type drift (evolve)
p = make_pipeline("infer_variant")
p.run([{"x": 42}], table_name="t")
p.run([{"x": "forty-two"}], table_name="t", schema_contract={"data_type": "evolve"})
print("(4) evolve drift :", types_of(p, "t"))
# Expect `x` (bigint) AND `x__v_text` (text)

# (5) freeze on type drift raises
p = make_pipeline("infer_freeze")
p.run([{"x": 42}], table_name="t")
try:
    p.run([{"x": "forty-two"}], table_name="t", schema_contract={"data_type": "freeze"})
    print("(5) freeze drift : DID NOT RAISE — unexpected")
except Exception as e:
    # dlt wraps the validation error in PipelineStepFailed; walk the chain
    inner = e
    while inner.__cause__ or getattr(inner, "exception", None):
        inner = inner.__cause__ or inner.exception
    print(f"(5) freeze drift : raised {type(inner).__name__}: {str(inner)[:80]}")
