# Notes — backfill in dlt

## The trigger

Setting **both** `initial_value` and `end_value` on `dlt.sources.incremental` flips the resource into backfill mode. Just one of them = open-ended incremental (production mode).

```python
dlt.sources.incremental("ts", initial_value=START, end_value=END)
```

## Boundary semantics

| Knob | Default | Other value |
|---|---|---|
| `range_start` | `"closed"` (≥) | `"open"` (>) |
| `range_end` | `"open"` (<) | `"closed"` (≤) |

So `[initial, end)` is the default — half-open. Matches Python `range()` and most slicing conventions.

## What backfill does NOT persist

- The cursor's `last_value` is **not** saved to `_dlt_pipeline_state` on a bounded-window run. Re-running the same backfill re-pulls the same rows (and dedupes via merge+PK).
- This is the property that makes backfill safe alongside production: a backfill of historical data can't move the production cursor forward and accidentally skip future rows.

## Production patterns

### Parallel month-windows

12 backfill pipelines, each into `bronze_orders_2025_<NN>`, then `UNION ALL` for silver. Lets you parallelize a long history without blocking on one giant load.

### Attribution-window (`lag_seconds`)

```python
dlt.sources.incremental("updated_at", lag=7*86400)  # re-pull last 7 days every run
```

For sources where rows can mutate after creation (Salesforce, marketing platforms). Production reads `[max - lag, ∞)` every run instead of `[max, ∞)`. PK + merge collapses the overlap.

### Backfill safety check

Before deploying a long backfill, prove it's isolated:

```python
prod_state_before = pipeline.state.copy()
backfill_pipeline.run(...)
assert pipeline.state == prod_state_before
```

If state changed → backfill is leaking into production.

## Foot-guns

- **Forgot `end_value`?** The "backfill" becomes a normal incremental run and persists the cursor. If you also reused production's pipeline_name, you've now corrupted production's high-water mark.
- **`dataset_name` collision.** Backfill into the production dataset = data merges into prod tables. Usually what you want for "filling a historical gap." Almost never what you want for "exploring a different window."
- **No PK + append disposition.** Re-running the backfill duplicates rows. Backfill is idempotent only with `merge`+`primary_key` (or `replace`).
- **Time-zone mismatches.** `"2026-03-01T00:00:00Z"` ≠ `"2026-03-01T00:00:00+07:00"`. Always normalize to UTC at the boundary.
