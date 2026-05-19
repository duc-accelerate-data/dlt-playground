"""Reference solution for exercise 13.

Naming convention is resolved at first dlt import in a Python process — once locked,
later runs in the same process ignore env overrides. To demonstrate both side-by-side,
we spawn a subprocess per naming with a fresh dlt import.
"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WH = REPO / "data" / "warehouse.duckdb"

CHILD = r"""
import sys, json
sys.path.insert(0, {repo!r})
import dlt
pipeline = dlt.pipeline(
    pipeline_name='naming_{name}',
    destination=dlt.destinations.duckdb({wh!r}),
    dataset_name={ds!r},
)
pipeline.run([{{'FirstName': 'Ada', 'favouriteRepo': 'dlt'}}], table_name='people')
cols = sorted(c for c in pipeline.default_schema.get_table('people')['columns']
              if not c.startswith('_dlt_'))
print('RESULT', json.dumps({{'naming': '{name}', 'cols': cols}}))
"""


def run_with_naming(naming: str, dataset: str):
    env = {**os.environ, "SCHEMA__NAMING": naming, "RUNTIME__LOG_LEVEL": "ERROR"}
    proc = subprocess.run(
        [sys.executable, "-c",
         CHILD.format(repo=str(REPO), wh=str(WH), name=naming, ds=dataset)],
        env=env, capture_output=True, text=True, check=True,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("RESULT "):
            print(line[len("RESULT "):])


run_with_naming("snake_case", "naming_snake")
run_with_naming("direct",     "naming_direct")
