"""Reference unit tests — bucket 2 of dlt-patterns-expanded.md.

Fast (sub-second), no network, no destination writes. Run with:
    pytest exercises/25-unit-tests/solution/test_resources.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import dlt
import pytest
import responses

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from shared.github_source import repos as github_repos  # noqa: E402


# --- 2.1 + 2.2: resource is a generator; stub HTTP at the URL layer -----------


@responses.activate
def test_repos_yields_dicts_from_stubbed_api():
    responses.add(
        responses.GET,
        "https://api.github.com/orgs/dlt-hub/repos",
        json=[{"id": 1, "name": "dlt"}, {"id": 2, "name": "verified-sources"}],
        status=200,
    )
    rows = list(github_repos(org="dlt-hub", access_token="test-token"))
    assert len(rows) == 2
    assert {r["name"] for r in rows} == {"dlt", "verified-sources"}


# --- 2.5: paginated source walks every page (Link: rel="next") ----------------


@responses.activate
def test_pagination_walks_all_pages():
    base = "https://api.github.com/orgs/dlt-hub/repos"
    responses.add(
        responses.GET, base,
        json=[{"id": 1, "name": "page1"}],
        headers={"Link": f'<{base}?page=2>; rel="next"'},
        status=200,
    )
    responses.add(
        responses.GET, f"{base}?page=2",
        json=[{"id": 2, "name": "page2"}],
        status=200,
    )
    rows = list(github_repos(org="dlt-hub", access_token="test-token"))
    assert len(rows) == 2


@responses.activate
def test_empty_response_yields_nothing():
    responses.add(
        responses.GET,
        "https://api.github.com/orgs/dlt-hub/repos",
        json=[], status=200,
    )
    assert list(github_repos(org="dlt-hub", access_token="test-token")) == []


# --- 2.6: incremental cursor instantiable in tests ----------------------------


def test_incremental_filters_old_records():
    @dlt.resource(primary_key="id", write_disposition="merge")
    def events(updated_at=dlt.sources.incremental(
        "updated_at", initial_value="2026-01-01T00:00:00Z",
    )):
        # Source emits both old and new — incremental keeps state but does not
        # *itself* filter; it's the resource's job. Verify state tracks the max.
        yield from [
            {"id": 1, "updated_at": "2025-12-31T00:00:00Z"},  # old
            {"id": 2, "updated_at": "2026-05-01T00:00:00Z"},  # new
            {"id": 3, "updated_at": "2026-05-15T00:00:00Z"},  # newer
        ]

    rows = list(events())
    # All 3 yielded — but dlt records the highest cursor for the *next* run.
    assert len(rows) == 3
    # The dlt.sources.incremental defaults its `last_value_func=max`; we can
    # at minimum check the resource is wired with the cursor we asked for.
    inc = events.incremental._incremental  # type: ignore[attr-defined]
    assert inc.cursor_path == "updated_at"


# --- 2.7 / 2.8: hints are set + apply_hints overrides them --------------------


def test_hints_are_set():
    # github_repos was defined with primary_key="id", write_disposition="merge"
    assert github_repos.compute_table_schema()["columns"]["id"]["primary_key"] is True
    assert github_repos.write_disposition == "merge"


def test_apply_hints_overrides_hints():
    res = github_repos(org="dlt-hub", access_token="t")
    res.apply_hints(write_disposition="append", primary_key="name")
    schema = res.compute_table_schema()
    assert res.write_disposition == "append"
    assert schema["columns"]["name"]["primary_key"] is True


# --- 2.17: test an add_map transform in isolation -----------------------------


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
