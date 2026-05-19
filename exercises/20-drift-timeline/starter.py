"""Exercise 20 — replay 4 versions of `people` through 3 contract policies."""
import json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt

DATA = REPO / "data" / "synthetic" / "drift-timeline"


@dlt.resource(name="people", primary_key="id", write_disposition="merge")
def people(version: int):
    with (DATA / f"v{version}.jsonl").open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def run_scenario(label: str, policy: dict):
    # TODO: build pipeline with dev_mode=True, dataset=f"drift_{label}"
    # TODO: for v in [1,2,3,4]: try pipeline.run(people(v), schema_contract=policy) and capture errors
    # TODO: after each version print (version, raised?, columns, row_count)
    ...


run_scenario("permissive", {"tables": "evolve", "columns": "evolve", "data_type": "evolve"})
run_scenario("strict",     {"tables": "evolve", "columns": "freeze", "data_type": "freeze"})
run_scenario("hybrid",     {"tables": "evolve", "columns": "evolve", "data_type": "freeze"})
