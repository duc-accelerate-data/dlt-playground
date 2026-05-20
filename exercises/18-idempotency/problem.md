# 18 — Idempotency: when re-running is safe (and when it isn't)

Idempotency = running the same pipeline twice with the same input gives the same destination state. dlt achieves this through **four layered mechanisms**:

1. **`_dlt_id` row identity** — every row gets a unique id. With a declared `primary_key`, it's derived from the PK (so the *same key* lands in the *same slot* across runs). Without a PK, it's random per yield (no automatic dedup).
2. **`primary_key` + `merge` disposition** — upsert by PK instead of append
3. **Incremental cursor** — re-runs skip already-seen rows (exercise 06 already drilled this)
4. **Per-job resume** — failed jobs retried; successful jobs not re-applied (exercise 22 drills this)

This exercise pins down *which dispositions* and *which configurations* actually preserve the property — and where it leaks.

## Goal

Run five scenarios. For each, run the pipeline **twice with the same input** and report whether the destination state matches the first run.

## Acceptance

| # | Setup | Re-run state | Idempotent? |
|---|---|---|---|
| 1 | `write_disposition="append"`, 2 rows | 4 rows | **No** — appends duplicate |
| 2 | `merge` with `primary_key="id"`, 2 rows | 2 rows | Yes — upsert by PK |
| 3 | `dev_mode=True` + merge | 2 datasets exist with timestamp suffixes | **False positive** — looks idempotent because target moves |
| 4 | Run v1 `{id, name}`, then v2 `{id, name, email}` (PK=id, merge, evolve) | row count stable but **schema differs** (added `email` column) | **Partial** — data idempotent, schema isn't |
| 5 | Yield two identical rows `{v:"a"}` *with no PK* | **both rows survive** — `_dlt_id` is generated per yield, not content-hashed | **Reverse foot-gun**: people assume dlt dedupes by content; without a PK it doesn't |

## Hints

- For scenario 3, use `pipeline = dlt.pipeline(..., dev_mode=True)` — dlt appends `_<timestamp>` to `dataset_name` each run. List datasets via `information_schema.schemata`.
- For scenario 4, no schema_contract is needed — `data_type` defaults to `evolve` which auto-adds new columns.
- For scenario 5, the foot-gun is *not declaring a primary_key*. Without a PK, dlt generates `_dlt_id` per yielded item (not from content), so identical rows do NOT dedupe. If your source emits the same logical row twice, both land. Fix: declare `primary_key` + use `merge`.
- Use a different `dataset_name` per scenario so they don't share state.
