"""Reference unit tests — bucket 2 of dlt-patterns-expanded.md.

Fast (sub-second), no network, no destination writes. The resources under
test are *inline* tiny dlt resources — not the shared github_source — because
unit tests should isolate behavior from project-wide retry configuration.

Run with:
    pytest exercises/25-unit-tests/solution/test_resources.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

import dlt
import pytest
import requests
import responses

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))


# --- A tiny test-only resource (plain `requests`, no dlt retry layer) -------


@dlt.resource(name="repos", primary_key="id", write_disposition="merge")
def repos(org: str = "demo", access_token: str = "tok") -> Iterator[dict]:
    url = f"https://api.github.com/orgs/{org}/repos"
    while url:
        r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"})
        r.raise_for_status()
        yield from r.json()
        url = r.links.get("next", {}).get("url")


# --- 2.1 + 2.2: resource is a generator; stub HTTP at the URL layer ----------


@responses.activate
def test_repos_yields_dicts_from_stubbed_api():
    responses.add(
        responses.GET,
        "https://api.github.com/orgs/demo/repos",
        json=[{"id": 1, "name": "dlt"}, {"id": 2, "name": "verified-sources"}],
        status=200,
    )
    rows = list(repos())
    assert len(rows) == 2
    assert {r["name"] for r in rows} == {"dlt", "verified-sources"}


# --- 2.5: paginated source walks every page (Link: rel="next") ---------------


@responses.activate
def test_pagination_walks_all_pages():
    base = "https://api.github.com/orgs/demo/repos"
    responses.add(
        responses.GET, base,
        json=[{"id": 1, "name": "p1"}],
        headers={"Link": f'<{base}?page=2>; rel="next"'},
        status=200,
    )
    responses.add(
        responses.GET, f"{base}?page=2",
        json=[{"id": 2, "name": "p2"}],
        status=200,
    )
    rows = list(repos())
    assert len(rows) == 2


@responses.activate
def test_empty_response_yields_nothing():
    responses.add(
        responses.GET,
        "https://api.github.com/orgs/demo/repos",
        json=[], status=200,
    )
    assert list(repos()) == []


# --- 2.6: incremental cursor instantiable in tests ---------------------------


def test_incremental_filters_old_records():
    @dlt.resource(primary_key="id", write_disposition="merge")
    def events(updated_at=dlt.sources.incremental(
        "updated_at", initial_value="2026-01-01T00:00:00Z",
    )):
        yield from [
            {"id": 1, "updated_at": "2025-12-31T00:00:00Z"},  # filtered out
            {"id": 2, "updated_at": "2026-05-01T00:00:00Z"},
            {"id": 3, "updated_at": "2026-05-15T00:00:00Z"},
        ]

    rows = list(events())
    ids = {r["id"] for r in rows}
    assert 1 not in ids, f"row below initial_value should be filtered, got {ids}"
    assert {2, 3}.issubset(ids), f"newer rows must pass, got {ids}"


# --- 2.7 / 2.8: hints are set + apply_hints overrides them -------------------


def test_hints_are_set():
    assert repos.write_disposition == "merge"
    schema = repos.compute_table_schema()
    assert schema["columns"]["id"].get("primary_key") is True


def test_apply_hints_overrides_hints():
    res = repos()
    res.apply_hints(write_disposition="append", primary_key="name")
    assert res.write_disposition == "append"
    schema = res.compute_table_schema()
    assert schema["columns"]["name"].get("primary_key") is True


# --- 2.17: test an add_map transform in isolation ----------------------------


def redact_email(row: dict) -> dict:
    return {**row, "email": "***@***" if row.get("email") else None}


def test_redact_email_map():
    @dlt.resource
    def users():
        yield {"id": 1, "email": "ada@example.com"}
        yield {"id": 2, "email": "alan@example.com"}

    redacted = list(users().add_map(redact_email))
    assert all(r["email"] == "***@***" for r in redacted)
    assert {r["id"] for r in redacted} == {1, 2}
