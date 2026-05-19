# Notes — Multi-version drift

- **Column add** is the easy case: `columns: evolve` handles it. Downstream models should `SELECT col1, col2, col3` explicitly so an unexpected new column doesn't bleed into silver/gold by surprise.
- **Column rename** is the dangerous case. dlt has no concept of "rename" — to the schema engine it's `drop + add`. The old column stays in the table (NULL-filled going forward); the new one starts populating. Two failure modes:
  1. Downstream `SELECT *` accidentally surfaces the dead column.
  2. Backfill queries hit NULLs where they used to find data.
  Industry fix: introduce a silver alias view (`coalesce(full_name, name)`) at the rename, run dual-stream for one release, drop the old column when downstream is clean.
- **Type widening** is the worst case. `int → string` in `age` poisons aggregations downstream. `freeze` in bronze + explicit migration column (`age_str`) keeps the warehouse honest. Never let widening sneak in.
- **Why hybrid is the real production default.** `tables: evolve` (new entities show up), `columns: evolve` (additions auto), `data_type: freeze` (no silent type drift). Adopted by dlt-hub Slack regulars and analytics-team templates from Fivetran-replacement projects.
- **The dlt-hub schema-evolution blog (Brudaru, 2023)** argues for two-tier: permissive bronze + strict silver, with explicit promotion. This exercise demonstrates why permissive bronze + downstream `SELECT *` is the trap.
- **Detection**: every `pipeline.run()` returns `LoadInfo` whose `load_packages[0].schema_update` lists schema deltas applied. Hook that into Slack / Linear to surface drift for human review.
