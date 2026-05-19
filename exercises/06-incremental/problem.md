# 06 — Incremental cursor

`dlt.sources.incremental("<cursor_field>")` keeps state across runs. First run: load everything from `initial_value`. Subsequent runs: only rows with `cursor > last_value`.

## Goal

Use the `issues` resource from `shared/github_source.py` (GitHub PAT required). Run it twice. Verify:

1. First run loads N issues.
2. Second run loads **0** new issues (or close to it — GitHub may have new issues since).
3. The `last_value` is persisted in state.

Then **force a backfill of a specific window** — load only issues updated in March 2026 — using `initial_value` + `end_value`.

## Acceptance

1. Two runs printed; second run's `load_info` shows zero new rows for `issues`.
2. A third run with `initial_value="2026-03-01T00:00:00Z"`, `end_value="2026-04-01T00:00:00Z"` loads only that window into a separate dataset.
3. Discuss: when would you add `lag=3600`? (Hint: late-arriving comments mutating `updated_at`.)

## Hints

- `dlt.sources.incremental("updated_at", initial_value=..., end_value=...)`.
- The resource already declares `updated_at` — you just override `initial_value` / `end_value` at the call site by re-instantiating the resource or passing a custom incremental.
- For full refresh, see `dlt.pipeline.run(..., refresh="drop_resources")`.
- Need GITHUB token — copy `.dlt/secrets.toml.example` → `.dlt/secrets.toml`.
