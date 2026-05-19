# 10 — Verified source + `.with_resources()` / `.apply_hints()`

A *verified source* is a maintained connector module — `pip install dlt[github]` ships one. Real teams pin their **subset** with `.with_resources("repos", "issues")` and attach **per-resource hints** (contract, disposition, cursor) with `.apply_hints()`. The vendor code stays untouched.

## Goal

Use the shared `github_source()` but:

1. Only ingest `issues` (skip `repos`).
2. Tighten the resource: `write_disposition="merge"`, `primary_key="id"`, `schema_contract={"columns":"freeze","data_type":"freeze"}`.
3. Override the cursor's `initial_value` to skip ancient issues (`2026-01-01`).

…without editing `shared/github_source.py`.

## Acceptance

1. Only the `issues` table is loaded (no `repos`).
2. Inspect the resource hints — they reflect your overrides.
3. State carries the new `initial_value`.

## Hints

- `src = github_source(org="dlt-hub")`
- `src = src.with_resources("issues")`
- `src.issues.apply_hints(write_disposition="merge", primary_key="id", schema_contract={...}, incremental=dlt.sources.incremental("updated_at", initial_value="2026-01-01T00:00:00Z"))`
