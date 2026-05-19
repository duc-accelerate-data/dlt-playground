# Notes — Data quality + PII

- **Three layers, three jobs.**
  - `add_filter` — gate: drop rows that violate hard rules. Runs first.
  - `add_map` — transform: redact, normalize, enrich. Pure functions only.
  - Pydantic `columns=` + `schema_contract` — type and shape enforcement, with configurable response (`freeze` blocks; `discard_value` nulls; `discard_row` drops).
- **Pipeline order:** filter → map → normalize. Don't redact in a filter; don't validate in a map.
- **PII discipline:**
  - Hash deterministic = joinable; hash with salt = not joinable. Pick based on downstream needs.
  - Never log redacted-from values, even at DEBUG. dlt's tracer doesn't, but `print(x)` in `add_map` does.
  - Email is the most-leaked field — apply `add_map` *before* any other step that might serialize the record.
- **Pydantic v2** is the supported version. v1 still works in places but verified sources migrated.
- **Industry idiom (Fivetran replacement crowd):** keep bronze redacted-only, do dq assertions in silver with `dbt-expectations`. dlt's resource-level quality is the *baseline*; downstream still owns business rules.
- **Don't reach for `add_yield_map` / batched maps** unless you've measured. The per-row map is cleaner and benchmarks within 5–10% in most pipelines.
