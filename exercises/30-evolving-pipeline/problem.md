# 30 — Evolving a live pipeline

Real-world dlt isn't `dlt init` → ship. It's **inheriting a pipeline that already runs in prod with months of data** and changing it without breaking history. Five common motions:

1. **Add a new resource** to an existing source without disturbing state of the others.
2. **Add a new column** with a backfill default (no full reload).
3. **Switch `write_disposition`** `replace` → `merge` mid-life on a populated table.
4. **Change `primary_key`** on a populated table (the spicy one).
5. **Rename a table** without losing history.

## Goal

Walk through all five motions on a single pipeline. After each step, assert that:
- previously-loaded data **survives**,
- new behavior **takes effect**,
- pipeline state in `_dlt_pipeline_state` keeps the right cursors.

## Steps

### Step 1 — baseline

Load a `users` resource (3 rows) with `write_disposition="replace"` and `primary_key="id"`. Confirm 3 rows.

### Step 2 — add a new resource (state-safe)

Add an `events` resource to the same pipeline. Run. Both tables must coexist; users still has 3 rows.

### Step 3 — add a column with a backfill default

Modify the `users` resource to also yield `country` (default "??" for the originals, real values for new rows). Run. Verify `country` column exists and existing rows have backfilled values.

### Step 4 — switch `replace` → `merge`

Change `users` to `merge` with `primary_key="id"`. Run with one updated row and one new row. Verify total rowcount = 4 (3 originals + 1 new), updated row's value reflects the update.

### Step 5 — change primary_key (the migration)

Change `primary_key` from `id` to `email`. dlt will **not** automatically migrate; you must drop & reload. Demonstrate the *correct* migration: drop the table, set new PK, reload, verify.

### Step 6 — rename a table

Rename `users` to `customers`. Show the old-table-lingers problem (it stays in the destination with stale data unless you `DROP` it). Demonstrate the safe path: explicit `DROP TABLE` plus reload under new name.

## Acceptance

`verify.py` runs the full sequence and asserts row counts + column presence + the rename cleanup at each step. Six checks total.

## Hints

- `pipeline.drop()` clears local working dir (state cache).
- `pipeline.dataset().__getitem__(table_name).drop()` drops just one table in the destination (or run raw SQL).
- For "backfill default", the resource yields the new column for every row — including the originals — when re-yielded. `replace` is the simplest mechanic; `merge` lets you do it without re-fetching unchanged rows but the upstream API has to support it.
- Step 5 anti-pattern: **never** change `primary_key` and hope dlt figures it out. Plan the migration: drop + reload, or shadow-write into a new table and cut over.
- Step 6 anti-pattern: assuming the old table disappears when you rename the resource. dlt only writes; it doesn't garbage-collect.
