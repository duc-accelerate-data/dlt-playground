# 12 — Load packages

Every `pipeline.run()` produces a **load package** with a `load_id`. The package is atomic — either all its tables commit or none. `_dlt_load_id` on every row is the FK to `_dlt_loads`. This is the unit of replay / rollback.

## Goal

Run the chess source three times. Then:

1. List all `load_id`s.
2. Pick the second one and **delete every row** belonging to it across all tables (simulating a rollback).
3. Verify no orphans remain.

## Acceptance

1. Print the 3 `load_id`s with timestamps.
2. After deletion, every row's `_dlt_load_id` is either run 1 or run 3 — never run 2.
3. Discuss: why this is safer than `DELETE WHERE created_at > X`.

## Hints

- `SELECT load_id FROM bronze_chess._dlt_loads ORDER BY inserted_at`.
- Loop over the data tables in the schema and `DELETE FROM <t> WHERE _dlt_load_id = ?`.
- `pipeline.default_schema.data_tables()` gives you the table list.
