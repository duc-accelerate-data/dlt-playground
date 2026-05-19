# Notes — Incremental cursor

- **Prefer `updated_at` over `created_at`.** `created_at` misses mutations to historical rows; `updated_at` catches them (assuming the source maintains it).
- **State lives in destination.** dlt creates a `_dlt_pipeline_state` table — your cursor survives across machines.
- **`last_value` updates row-by-row.** Inside the resource, `incremental.last_value` reflects the highest value seen so far in the current run.
- **`lag` / attribution window.** Set `lag=3600` (seconds) when records can mutate within the hour after creation — e.g., Stripe payment status updates, Salesforce activity rollups, ad-network conversions. dlt re-fetches the lag window every run.
- **`allow_external_schedulers=True`** lets Airflow / Dagster set start/end values via env vars (`DLT__SOURCES__<NAME>__START_VALUE`). Pairs well with date-partitioned backfills.
- **Backfill discipline.** Don't backfill into the live dataset — use a separate `dataset_name`, validate, then merge.
- **Industry mistake:** forgetting that `since` filters are usually inclusive on the upstream API. The first row of every run is a duplicate by primary key. `write_disposition="merge"` makes this harmless; `append` makes it dangerous.
