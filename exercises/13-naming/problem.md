# 13 — Naming convention

dlt has pluggable naming conventions: `snake_case` (default), `direct` (passthrough), `duck_case`, or your own. Destinations enforce their own identifier limits (DuckDB 1024, Snowflake 255, Fabric Lakehouse 128).

## Goal

Load a payload with a mixed-case key (`{"FirstName": "Ada", "favouriteRepo": "dlt"}`) under two naming conventions and observe the resulting column names. Then write a payload whose flattened nested key would exceed a 30-char limit and watch dlt truncate it.

## Acceptance

1. Under `snake_case`: columns are `first_name`, `favourite_repo`.
2. Under `direct`: columns are exactly `FirstName`, `favouriteRepo`.
3. With a deliberately tiny `max_identifier_length`, dlt truncates and de-dupes long names.

## Hints

- Set on schema: `pipeline.default_schema.update_normalizers({"naming": "snake_case"})` *before* the first run.
- Or in `.dlt/config.toml`: `[schema] naming = "direct"`.
- Custom limits live in destination capabilities — easiest demo: use a custom naming module or just print observed truncation behavior.
