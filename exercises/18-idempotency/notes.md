# Notes — idempotency in dlt

## The four mechanisms

| Layer | Mechanism | Failure mode if missing |
|---|---|---|
| Extract | incremental cursor | re-pulls all rows every run |
| Normalize | `_dlt_id` row identity (PK-derived when PK declared, random otherwise) | without PK: no automatic dedup |
| Load | `primary_key` + `merge` | rows duplicate on re-run |
| Load (recovery) | per-job resume on failure | failed run = need full re-do |

Defense in depth — even if extract pulls a row twice (cursor overlap), normalize/load layers dedupe it.

## Disposition cheat-sheet

| Disposition | Re-run with same input | Idempotent? |
|---|---|---|
| `append` (no PK) | rows duplicate | **No** |
| `append` + PK | rows still duplicate (PK is metadata only for append) | **No** |
| `merge` + `primary_key` | upsert by PK | Yes |
| `merge` + `merge_key` | delete-by-key then insert | Yes |
| `replace` | full reload | Yes (state-wise) |
| `scd2` | hash-based; same input → no new version | Yes (semantically) |

## Foot-guns

- **`append` with PK does not dedupe.** PK is informational for append; only `merge` uses it for upsert.
- **No PK = no content dedup.** `_dlt_id` is generated per yielded item, not content-hashed, so identical rows survive as duplicates. People often assume the opposite (because dlt docs mention `_dlt_id` as a "row identity"). Declare a real `primary_key` + use `merge` to actually dedupe.
- **`dev_mode=True` is fake idempotency.** Each run targets a new timestamped dataset. Use only for local debugging, never in CI.
- **Schema drift breaks "same input → same schema."** Adding a column under `data_type=evolve` mints new columns on the second run. Data is idempotent; schema isn't. Use `data_type="freeze"` in bronze + alert on the failed load.
- **Wall-clock cursors.** `incremental("updated_at")` where the source emits `updated_at = NOW()` never settles — cursor keeps advancing, re-runs keep pulling. Use server-side timestamps that are stable across reads.

## Production checklist

1. Declare a real `primary_key` on every resource that represents a stateful entity.
2. Use `merge` (not `append`) unless the data is genuinely immutable (events, audit logs).
3. Set `schema_contract={"data_type": "freeze"}` in bronze + alert.
4. Never enable `dev_mode=True` outside local debugging.
5. Use server-side `updated_at` for incremental, never `now()`-style fields.
