# 15 — Destination capabilities

Every dlt destination advertises *capabilities*: supported types, max identifier length, default merge strategy, staging requirements, decimal precision, file formats it accepts.

## Goal

Inspect DuckDB's capabilities and pretty-print:
- max identifier length
- supported merge strategies
- supported file formats for staging
- naming convention default

Then load the dirty `products.csv` (booleans `true`/`TRUE`/`1`, missing date) and observe how DuckDB-specific coercion handles them.

## Acceptance

1. Print the capabilities dict.
2. Load `products` → confirm `active` lands as BOOLEAN, `launched_on` as DATE with NULL for the missing row.
3. Compare against what Postgres / Snowflake would do (just from reading their capability classes — no need to run).

## Hints

- `from dlt.common.destination.capabilities import DestinationCapabilitiesContext`
- Or simpler: `dlt.destinations.duckdb(...).capabilities()`.
