# 25 — Unit Tests for dlt resources

**Bucket 2 of the practitioner patterns doc.** A dlt resource is just a Python generator with hints — you should test it the same way you test any generator. **Never** hit a live API in unit tests; **never** run a full `pipeline.run()` either (that's an integration test).

## What you'll cover

| Pattern from doc | Demonstrated here |
|---|---|
| 2.1 resource as generator | `test_player_profile_yields_dicts` |
| 2.2 / 2.10 mock the HTTP client | `responses` lib stubs the URL |
| 2.5 paginated source with multiple pages | `test_pagination_walks_all_pages` |
| 2.6 incremental cursor with `Incremental(...)` | `test_incremental_filters_old_records` |
| 2.7 / 2.8 resource hints + apply_hints | `test_hints_are_set` |
| 2.17 `add_map` transform tested in isolation | `test_redact_email_map` |
| 2.21 empty source case | `test_empty_response_yields_nothing` |

## Goal

Write a `pytest` test file that demonstrates each of those patterns against the playground's `shared/github_source.py` (and a tiny inline resource for the cursor / map cases). Aim for **fast** tests — sub-second total, no network, no destination writes.

## Acceptance

`verify.py` runs `pytest exercises/25-unit-tests/solution/test_resources.py -q` and expects:
1. Exit code 0.
2. At least 7 tests collected and passed.
3. No HTTP request actually leaves your machine (the `responses` lib enforces this).

## Hints

- `from responses import RequestsMock, GET` — assertion-mode `responses` stubs.
- A dlt resource is just `iter(resource_instance)` — consume with `list(...)`.
- `dlt.sources.incremental("updated_at", initial_value="...")` is instantiable in test code; pass it as a resource kwarg.
- `resource.add_map(fn)` returns the same resource — iterate it to see the mapped output.
- Anti-pattern check (2.12 / 2.13): never call `pipeline.run()` in this exercise.
