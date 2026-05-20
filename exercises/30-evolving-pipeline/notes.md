# Notes — Evolving a live pipeline

- **dlt does state, not migration.** It tracks cursors and load packages; it does not rewrite tables when you change resource hints. Any hint change that affects row identity (`primary_key`, `merge_key`, `write_disposition`) is a **migration** — plan it like one.
- **Add resources freely.** New `@dlt.resource` in an existing source = new table, no risk to existing ones. State is per-resource.
- **Add columns freely** under `columns: evolve`. They appear on the next load, existing rows get NULL for the new column unless you yield a backfill value.
- **Switching `replace` → `merge`** is safe iff you also declare `primary_key`. dlt MERGEs new rows against the now-existing population. First merge run effectively backfills.
- **Switching `merge` → `scd2`** is *not* an in-place change — historical rows have no `_dlt_valid_from`. Plan a backfill: drop, set new strategy, reload from source (or a stored snapshot).
- **Changing `primary_key`** = drop + reload. There is no clean in-place migration: `_dlt_id`s are content-addressed off the row contents, so the old `_dlt_id`s no longer make sense under the new key. The right path:
  1. Block writes (pause schedule).
  2. Snapshot the table to `<table>_v_old` for safety.
  3. Drop the live table.
  4. Update `primary_key` in code.
  5. Reload from source.
- **Renaming a table** = old table lingers. dlt has no GC. Either explicitly `DROP TABLE` the old one, or accept that downstream queries will see two tables. For zero-downtime: write to new name, dual-read for one release, drop old.
- **Anti-pattern: changing pipeline_name to "reset".** That orphans the old state file and creates a parallel pipeline. Use `pipeline.drop()` to clear state cleanly, or just delete the working dir under `~/.dlt/pipelines/`.
- **Always test migrations on a clone first.** Spin up a copy of the destination, run the migration end-to-end, diff the row counts and key columns *before* you touch prod.
- **CHANGELOG.md per pipeline.** Each migration earns one entry: date, what changed, who, what to test. The runbook (exercise 29) references the CHANGELOG when things go wrong.
