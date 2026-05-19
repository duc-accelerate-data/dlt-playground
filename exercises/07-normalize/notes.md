# Notes — Normalize + control columns

- **Normalize is the engine, not a knob.** You configure it indirectly: `schema_contract` (drift), `naming` (identifiers), `primary_key` (controls `_dlt_id` derivation), `columns=` (forces types).
- **`_dlt_id` is content-hashed** when there's no `primary_key`. Same input row twice → same `_dlt_id` → dedup is automatic.
- **`_dlt_parent_id` is the only legitimate FK between bronze tables.** Source-side IDs may collide across vendors; `_dlt_id` won't.
- **`_dlt_load_id` is the gold standard for incident replay.** "Roll back load 1701234567" = `DELETE FROM x WHERE _dlt_load_id='1701234567'` everywhere it appears.
- **Nested → child tables, not JSON columns.** dlt's preference is relational. To preserve nested JSON instead, set `complex_types="json"` on the column or use `dlt.mark.with_table_name` for custom routing.
- **Naming flattening uses `__` (double underscore).** `address.city` → `address__city`. This is the place to predict your downstream `dbt source` definitions.
