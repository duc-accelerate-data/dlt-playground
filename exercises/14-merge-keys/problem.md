# 14 — Merge keys / `primary_key` vs `merge_key` / dedup_sort

`primary_key` = identity (one row per key in the destination).
`merge_key` = upsert match key (can be composite; used to find rows to replace in `delete-insert`).
`dedup_sort` = "when two incoming rows have the same key, keep the one with the largest <field>".

## Goal

Simulate a paginated API that re-emits the same event twice (typical when `since` filters are inclusive — see exercise 06's note). Load with three configurations and observe behaviour:

1. `primary_key="event_id"` only — straightforward upsert.
2. `merge_key=["user_id", "event_id"]` (no PK) — replaces all matching rows, useful for partition-style reloads.
3. `primary_key="event_id"` + duplicate input → use `dedup_sort` inside `write_disposition` to deterministically pick a survivor.

## Acceptance

For each config: load, observe which version of the duplicate survives and the resulting row count.

## Hints

- The source is two yields of `event_id="e1"` with different `updated_at` timestamps — stand-in for an API page boundary.
- `dedup_sort` only kicks in *within a single load package*; cross-load dedup is the destination's merge strategy.
- In dlt 1.x, `dedup_sort` lives **inside** `write_disposition`: `write_disposition={"disposition": "merge", "strategy": "delete-insert", "dedup_sort": ("updated_at", "desc")}`.
