# Notes — Modelling

- **SCD2 = history is non-negotiable.** Choose it when business needs to answer "what was X's value last March?". Cost: 2–10× the row count of `merge`. Not for every table — usually dim/customer/account/contract tables, not events.
- **`_dlt_valid_from` / `_dlt_valid_to` are dlt-managed.** Retired rows get a non-null `_dlt_valid_to`; the current row has `_dlt_valid_to IS NULL`. Downstream silver queries `WHERE _dlt_valid_to IS NULL` for "current state".
- **JSON column vs flattened child table.** Default is flatten — DuckDB / warehouses love columnar relational shape. Keep JSON when:
  - The nested shape is heterogeneous and would explode to 100s of columns.
  - Consumers query the JSON sparingly (logging, audit, debugging).
  - You want to preserve forward-compatible API responses without schema-drift fireworks.
  Switch to flattened (default) when consumers join, aggregate, or filter on inner fields.
- **Surrogate vs natural keys.** Prefer the source's natural key (`customer_id`) when it's stable. Fall back to `_dlt_id` only when the source has no PK or composite keys are awkward. Composite PKs are first-class: `primary_key=("tenant_id", "id")`.
- **Don't mix dispositions in one resource.** A resource is `replace` OR `merge` OR `merge-scd2` — not "replace during backfill, merge in steady state." Use a config flag + branch at the *pipeline* level instead.
- **Migration cost.** Switching `customers` from `replace` → `scd2` mid-life requires either a full backfill or a clean break (drop & reload). Plan it like a schema migration, not a code edit. (Exercise 30 covers this.)
- **The dbt-side mental model.** Bronze = whatever the source emits + dlt's normalize. Silver = your business view. Don't over-model in bronze — leave SCD2/JSON decisions for the layer that *owns* business meaning, unless dlt's built-in support is dramatically simpler than rebuilding it in dbt downstream.
