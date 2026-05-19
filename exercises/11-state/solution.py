"""Reference solution for exercise 11."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
import requests


@dlt.resource(name="org_repos", write_disposition="replace")
def org_repos(org: str = "dlt-hub", token: str = dlt.secrets.value):
    state = dlt.current.resource_state()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "dlt-playground",
    }
    if etag := state.get("etag"):
        headers["If-None-Match"] = etag

    r = requests.get(f"https://api.github.com/orgs/{org}/repos?per_page=100", headers=headers)
    if r.status_code == 304:
        print("304 Not Modified — nothing to yield.")
        return
    r.raise_for_status()
    state["etag"] = r.headers.get("ETag", "")
    yield from r.json()


pipeline = dlt.pipeline(
    pipeline_name="github_etag",
    destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
    dataset_name="bronze_github_etag",
)
print("RUN 1:", pipeline.run(org_repos()))
print("RUN 2:", pipeline.run(org_repos()))  # should hit 304
print("STATE:", pipeline.state["sources"])
