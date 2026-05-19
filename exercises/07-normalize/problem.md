# 07 — Normalize stage + control columns

dlt's pipeline is **extract → normalize → load**. The normalize stage:

- Flattens nested JSON (`{"size":{"weight":7}}` → `size__weight`).
- Splits nested arrays into child tables linked via `_dlt_parent_id`.
- Injects three control columns into every table:
  - `_dlt_id` — row identity (content hash unless `primary_key` is declared).
  - `_dlt_parent_id` — FK pointing at the parent row's `_dlt_id` (child tables only).
  - `_dlt_load_id` — id of the load package that wrote the row.

## Goal

Load chess player profiles (nested) and observe what dlt does without you asking.

## Acceptance

1. `bronze_chess.player_profile` has `_dlt_id`, `_dlt_load_id` columns and a flattened `last_online`-like field.
2. Print the schema for the table — confirm at least one `__`-flattened column.
3. Run a query joining `player_profile` → `_dlt_loads` on `_dlt_load_id` to find when each row was loaded.

## Hints

- After running, query `information_schema.columns` or use `pipeline.default_schema.get_table("player_profile")["columns"]`.
- `_dlt_loads` lives in the same dataset.
