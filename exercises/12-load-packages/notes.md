# Notes — Load packages

- **Load package = atomic unit.** dlt stages files on disk first (extracted → normalized → staged) and only when all are ready does it commit to the destination. A crash mid-load leaves no half-written data — the package is replayable.
- **`_dlt_loads` is the audit log.** `(load_id, status, inserted_at, schema_version_hash)` — every load is recorded. Use it to answer "what changed last Tuesday at 03:00?".
- **`_dlt_load_id` everywhere** = perfect lineage. Roll back by `load_id`, not by timestamp window. Replays are cheap and exact.
- **`_dlt_loads` survives even when the resource isn't rerun** — failed/aborted packages get a row with `status != 0`.
- **Hygiene:** truncate old packages on disk after merge — `pipeline.drop()` or `pipeline.activate_destination_state(...)` are not the same; usually you let the working dir self-clean.
