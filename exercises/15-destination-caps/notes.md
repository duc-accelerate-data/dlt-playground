# Notes — Destination capabilities

- **Capabilities are not user-configurable knobs.** They're declarations from the destination driver that tell normalize: "I accept these types, this max identifier length, this merge strategy." Normalize adapts to fit.
- **Cross-destination portability** comes from honoring the *most restrictive* destination you'll ship to. If your prod is Fabric (128-char ids), keep dev identifiers under 128 even on DuckDB.
- **`supported_merge_strategies`** controls what's available — Snowflake has `delete-insert`, `upsert`, `scd2`; BigQuery has `delete-insert`, `scd2` (no upsert); DuckDB has all three.
- **`supported_loader_file_formats`** matters for staging: Snowflake/BigQuery prefer `parquet`, DuckDB takes `insert_values` or `parquet`. Larger loads → parquet staging > row-by-row insert.
- **JSON column handling differs:** Postgres stores `jsonb`, BigQuery stores `JSON`, DuckDB stores `JSON`, Snowflake stores `VARIANT`. Same dlt code, different destination type — query downstream accordingly.
