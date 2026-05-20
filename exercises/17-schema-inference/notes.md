# Notes — schema inference

## Type-inference rules (dlt 1.x)

| JSON value | Python type | dlt `data_type` | DuckDB column |
|---|---|---|---|
| `42` | int | `bigint` | BIGINT |
| `3.14` | float | `double` | DOUBLE |
| `"alice"` | str | `text` | VARCHAR |
| `true` / `false` | bool | `bool` | BOOLEAN |
| `"2026-01-01T00:00:00Z"` | str (ISO-8601) | `timestamp` | TIMESTAMP WITH TIME ZONE |
| `"2026-01-01"` | str (date-only) | `date` | DATE |
| `None` | None | (no type) → nullable=true | nullable |
| `[...]` | list | child table | spawns `parent__field` |
| `{...}` | dict | flattened | parent__child columns |

## The variant column pattern

When a column already has a type and an incoming row has a conflicting type:

- `data_type="evolve"` (default): dlt creates `<col>__v_<new_type>` and writes there
- `data_type="discard_value"`: drop the value, keep the row
- `data_type="discard_row"`: drop the whole row
- `data_type="freeze"`: raise `DataValidationError`

Variant columns are **load-time safety nets**. They prevent crashes when upstream changes a field's type, but they fragment your schema — `x`, `x__v_text`, `x__v_double` are three different columns the downstream consumer must coalesce.

Production rule: `data_type="freeze"` in bronze + alerting on the failed load. Forensic / audit pipelines use `discard_value`. Never silently accept variants in prod.

## Foot-guns

- **ISO-string vs string**: dlt parses ISO-8601 *eagerly*. If your upstream sends `"2024-01-01"` as a *literal label* (not a date), it lands in a DATE column and arithmetic breaks. Override with `apply_hints(columns={"date_label": {"data_type": "text"}})`.
- **Int overflow**: dlt always uses `bigint`, so 64-bit fits. But if you bind to Postgres `INTEGER` (32-bit) downstream, you need explicit hints.
- **`hugeint`**: DuckDB upgrades to `HUGEINT` (128-bit) when it sees ids > 2^63 (e.g. Snowflake row IDs, Twitter snowflake IDs). dlt reports this as `bigint` but DuckDB stores wider — destination-capability quirk.
- **Variant columns are forever**: once dlt creates `x__v_text`, it stays. There's no "demote back to single column" operation. Plan your contract policy before the first bad row lands.
