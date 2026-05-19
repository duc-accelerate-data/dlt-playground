"""Exercise 11 — resource state for ETag handling."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
import requests


@dlt.resource(name="org_repos", write_disposition="replace")
def org_repos(org: str = "dlt-hub", token: str = dlt.secrets.value):
    state = dlt.current.resource_state()
    # TODO: build headers including If-None-Match if state has an etag
    # TODO: GET https://api.github.com/orgs/{org}/repos
    # TODO: on 304 return early
    # TODO: on 200 update state["etag"] and yield rows
    ...


pipeline = dlt.pipeline(
    pipeline_name="github_etag",
    destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
    dataset_name="bronze_github_etag",
)
print(pipeline.run(org_repos()))
