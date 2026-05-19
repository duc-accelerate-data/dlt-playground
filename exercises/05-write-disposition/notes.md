# Notes — Write disposition

- **Decision tree** (from dlt-hub schema-evolution blog):
  1. Stateless events → `append`.
  2. Stateful, no history needed → `merge` + `primary_key`.
  3. Stateful, history needed → `merge` + `strategy="scd2"`.
  4. Small reference data, full refresh fine → `replace`.
- **`merge` strategies** (dlt 1.x): `delete-insert` (default), `upsert`, `scd2`, `insert-only`. Default works for most CRUD sources.
- **`replace` ignores keys.** The whole table is dropped and re-loaded. Use only when the source returns the *full* state every time.
- **Append + downstream dedup** is a valid pattern too: keep bronze append-only for full audit, dedup in silver. Tradeoff: storage cost vs replay safety.
- **Fivetran parallel:** their "history mode" ≈ dlt's `scd2`.
