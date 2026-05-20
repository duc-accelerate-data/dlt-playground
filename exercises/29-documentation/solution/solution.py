"""Reference solution for exercise 29 — documentation discipline.

Shows the three artefacts: resource docstring, column descriptions, RUNBOOK.md.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

import dlt
from dlt.sources.helpers import requests
import responses

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

API = "https://api.github.com"


@dlt.resource(
    name="repos",
    primary_key="id",
    write_disposition="merge",
    columns={
        "id":         {"description": "GitHub repo numeric id (immutable across renames).",
                       "data_type": "bigint"},
        "name":       {"description": "Repo short name within the org (mutable on rename).",
                       "data_type": "text"},
        "full_name":  {"description": "Org/repo combination, e.g. 'dlt-hub/dlt'. Mutable.",
                       "data_type": "text"},
        "updated_at": {"description": "Server-side last-modified timestamp; cursor field.",
                       "data_type": "timestamp"},
    },
)
def repos(
    org: str = dlt.config.value,
    access_token: str = dlt.secrets.value,
) -> Iterator[dict]:
    """All public repos for a GitHub organization.

    Source         : GitHub REST API — `/orgs/{org}/repos`
    Auth           : Bearer PAT, scope `public_repo`. Read from
                     [sources.github].access_token (secrets.toml).
    Cursor         : none on this resource (issues uses `updated_at`); repos
                     is small enough that a full re-paginate is cheap.
    Write strategy : merge by `id`, so rename / visibility flips upsert in place.
    Rate limit     : authenticated = 5,000 req/h, unauthenticated = 60/h.
                     Each call returns up to 100 items via `per_page=100`.
    Owner          : data-eng@accelerate-data (Slack #data-eng).
    Backfill       : `dbt-style` full reload — `pipeline.drop()` then re-run.
    """
    url = f"{API}/orgs/{org}/repos"
    while url:
        r = requests.get(url, params={"per_page": 100},
                         headers={"Authorization": f"Bearer {access_token}",
                                  "Accept": "application/vnd.github+json",
                                  "User-Agent": "dlt-playground"})
        r.raise_for_status()
        yield from r.json()
        url = r.links.get("next", {}).get("url")


# Smoke-run via mocked HTTP so the docs are exercised even without a real PAT
# Pipeline runs only when executed via verify.py (which sets EXERCISE_SOURCE);
# this lets `__main__` and runpy.run_path both work.

def _run_smoke():
    @responses.activate
    def _do():
        responses.add(
            responses.GET,
            f"{API}/orgs/dlt-hub/repos",
            json=[{"id": 1, "name": "dlt", "full_name": "dlt-hub/dlt",
                   "updated_at": "2026-05-01T00:00:00Z"}],
            status=200,
        )
        p = dlt.pipeline(
            pipeline_name="docs_demo",
            destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
            dataset_name="docs_demo",
        )
        # Inject token directly so we don't need .dlt/secrets.toml
        p.run(repos(org="dlt-hub", access_token="test-token"))
        return p

    return _do()


pipeline = _run_smoke()

# Expose the loaded schema so the verifier can introspect.
print("\nLoaded schema columns for 'repos':")
for name, spec in pipeline.default_schema.get_table("repos")["columns"].items():
    if not name.startswith("_dlt_"):
        print(f"  {name:<14} {spec.get('description', '(no description)')}")
