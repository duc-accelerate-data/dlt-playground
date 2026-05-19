# 14 — Merge keys / `primary_key` vs `merge_key` / dedup_sort

`primary_key` = identity (one row per key in the destination).
`merge_key` = upsert match key (can be composite; used to find rows to replace in `delete-insert`).
`dedup_sort` = "when two incoming rows have the same key, keep the one with the largest <field>".

## Goal

Use the Postgres `orders` source (or fall back to synthetic). Load it with three configurations and observe behaviour:

1. `primary_key="id"` only — straightforward upsert.
2. `merge_key=["customer_id", "placed_at"]` (no PK) — replaces all matching rows, useful for partition-style reloads.
3. `primary_key="id"` + duplicate input → set `dedup_sort=("updated_at", "desc")` — keeps the latest.

## Acceptance

For each config: load, mutate input, reload, check row count and which version of the duplicate survived.

## Hints

- If you don't have Postgres running, the synthetic events resource works the same way.
- `dedup_sort` only kicks in *within a single load package*; cross-load dedup is the destination's merge strategy.
