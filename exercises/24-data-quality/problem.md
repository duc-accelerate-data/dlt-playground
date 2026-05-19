# 24 — Data quality + PII redaction at the resource boundary

dlt offers three composable mechanisms at the resource boundary:

- **`columns=PydanticModel`** — validate shape + types. Pairs with `schema_contract`.
- **`add_map(fn)`** — transform every record (PII redaction, normalization).
- **`add_filter(fn)`** — drop records that fail a predicate (data quality gate).

## Goal

Process a stream of user events with three quality / privacy rules:

1. **Validate**: every row must have `event_id`, `user_id`, `ts`. Missing → drop.
2. **Redact**: hash `email` field with SHA-256 (truncated to 16 hex chars). The original must never reach bronze.
3. **Bound types**: `age` must be int 0–120; otherwise discard the value.

Use Pydantic for (3) and `add_filter` / `add_map` for (1) and (2).

## Acceptance

1. Run with 6 input rows (2 missing required fields, 1 with `age=999`, 1 with a real email).
2. Final table has 4 rows. Emails are hashed (no `@` in any value). `age=999` is null.
3. Print which records were filtered and which were redacted.

## Hints

- `from pydantic import BaseModel, conint`
- `@dlt.resource(columns=MyModel, schema_contract={"data_type": "discard_value"})`
- `res.add_filter(lambda x: all(k in x for k in required))`
- `res.add_map(lambda x: {**x, "email": hash_email(x.get("email"))})`
