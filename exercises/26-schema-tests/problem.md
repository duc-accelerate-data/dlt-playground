# 26 — Schema tests (standard data tests)

**Bucket 3 of the practitioner patterns doc.** After `pipeline.run()`, your bronze layer has a known shape. Schema tests assert *that shape stays stable* across loads — tables present, columns present, types correct, no failed jobs, control columns intact. Failures gate CI before the data ever reaches downstream consumers.

## What you'll cover

| Pattern | Demonstrated |
|---|---|
| 3.1 tables exist in `pipeline.default_schema.tables` | `test_expected_tables_exist` |
| 3.2 column presence + data type | `test_column_types_match_contract` |
| 3.3 row-count smoke test in DuckDB | `test_row_count_in_range` |
| 3.4 `load_info.has_failed_jobs` master assertion | `test_no_failed_jobs` |
| 3.5 a load package was created | `test_load_package_recorded` |
| 3.6 `schema_contract="freeze"` as CI gate | `test_freeze_blocks_new_column` |
| 3.13 schema-version-hash assertion | `test_schema_hash_is_stable` |
| 3.15 nested child tables materialized | `test_child_tables_present` |

## Goal

Run the `chess_source` once into a clean dataset, then assert all of the above via `pytest`. Then deliberately *break* the schema (feed an extra column) under `schema_contract="freeze"` and assert it raises `DataValidationError`.

## Acceptance

`verify.py` runs `pytest exercises/26-schema-tests/solution/test_schema.py -q` and expects:
1. Exit code 0.
2. At least 8 tests pass.
3. The "freeze blocks drift" test actually triggers `DataValidationError` (not just any exception).

## Hints

- `pipeline.last_trace` and `pipeline.last_trace.last_load_info` give you `LoadInfo` with `has_failed_jobs`, `loads_ids`, `load_packages`.
- `pipeline.default_schema.stored_version_hash` is the deterministic schema fingerprint.
- For the freeze test, *separate* pipeline so it doesn't fight the happy-path one (`pipeline_name="schema_freeze_demo"`).
- Use `dlt.exceptions.DataValidationError` (or its parent) — don't catch `Exception` broadly.
