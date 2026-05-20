# 19 — Backfill: bounded windows, isolation, and boundaries

dlt's `incremental(initial_value=..., end_value=...)` puts the resource into **backfill mode**: it pulls a bounded window `[initial, end)` and does *not* persist the cursor to pipeline state. That's the property that makes backfills safe to run alongside production.

## What you should observe

| Property | Mechanism |
|---|---|
| **Bounded window** | only rows in `[initial_value, end_value)` are pulled |
| **No cursor persistence** | re-running the same backfill pulls the same rows; production's cursor is untouched |
| **Pipeline isolation** | a backfill pipeline + dataset is independent of the production one — running either does not affect the other |
| **Boundary semantics** | `range_start` defaults to `"closed"` (≥), `range_end` defaults to `"open"` (<); both can be flipped |
| **Re-run idempotency** | with `merge` + `primary_key`, running the same backfill twice gives the same destination state |

## Goal

Run five scenarios against a synthetic stream of events (one per month, Jan–May 2026).

## Acceptance

| # | Setup | Expected |
|---|---|---|
| 1 | Backfill window `[Feb 1, Apr 1)` | Exactly 2 rows: Feb 15 + Mar 15 |
| 2 | Production pipeline pulls all 5 rows; separate backfill pulls only Feb–Mar | Production = 5, backfill = 2; **neither affects the other's row count** |
| 3 | Three monthly backfills (Jan, Feb, Mar) into three separate datasets | Each dataset has exactly 1 row |
| 4 | `range_start="open"` (exclusive) at Feb 1 vs default `"closed"` (inclusive) — yield a row at exactly Feb 1 | `closed`: includes it; `open`: excludes it |
| 5 | Run the same backfill twice with `merge`+PK | Same row count; no duplicates (idempotent within the window) |

## Hints

- Use a different `dataset_name` per scenario so they don't collide.
- For (4), add a row with `ts == initial_value` to the synthetic stream and check it lands in only the `closed` dataset.
- For (5), the proof is two `pipeline.run()` calls back-to-back, then count rows — same number, no growth.
- `pipeline.state` is a dict you can inspect to see whether a cursor's `last_value` was stored. Backfill runs leave incremental state empty.
