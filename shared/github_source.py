"""GitHub REST source — used by exercises 04, 06, 10, 11, 14.

Demonstrates:
  - dlt.secrets.value for the PAT (resolved from .dlt/secrets.toml [sources.github])
  - rate-limit / 304 handling kept simple; bump page_size or sleep if you hit limits
  - cursor-based incremental on `updated_at`
"""
from __future__ import annotations

from typing import Iterator

import dlt
from dlt.sources.helpers import requests

API = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "dlt-playground",
    }


@dlt.resource(
    name="repos",
    primary_key="id",
    write_disposition="merge",
)
def repos(
    org: str = dlt.config.value,
    access_token: str = dlt.secrets.value,
) -> Iterator[dict]:
    """All public repos for an org. Merge on id — captures rename/visibility changes."""
    url = f"{API}/orgs/{org}/repos"
    while url:
        r = requests.get(url, headers=_headers(access_token), params={"per_page": 100})
        r.raise_for_status()
        yield from r.json()
        url = r.links.get("next", {}).get("url")


@dlt.resource(
    name="issues",
    primary_key="id",
    write_disposition="merge",
)
def issues(
    org: str = dlt.config.value,
    repo: str = dlt.config.value,
    access_token: str = dlt.secrets.value,
    # GitHub's /issues endpoint returns [] for since=1970-01-01 (epoch is silently rejected).
    # 2008 predates GitHub itself, so it's a safe "from the beginning" sentinel.
    updated_at=dlt.sources.incremental("updated_at", initial_value="2008-01-01T00:00:00Z"),
) -> Iterator[dict]:
    """Cursor-based incremental on GitHub's server-side `updated_at`.

    Note: `since` filter on GitHub returns rows where updated_at >= since,
    so dlt's deduplication on primary_key handles the overlap automatically.
    """
    url = f"{API}/repos/{org}/{repo}/issues"
    params = {
        "state": "all",
        "since": updated_at.start_value,
        "per_page": 100,
        "sort": "updated",
        "direction": "asc",
    }
    while url:
        r = requests.get(url, headers=_headers(access_token), params=params)
        r.raise_for_status()
        yield from r.json()
        url = r.links.get("next", {}).get("url")
        params = None  # next-page URL already has params


@dlt.source(
    name="github",
    schema_contract={"tables": "evolve", "columns": "freeze", "data_type": "freeze"},
)
def github_source(org: str = dlt.config.value):
    return [repos(org=org), issues(org=org, repo="dlt")]
