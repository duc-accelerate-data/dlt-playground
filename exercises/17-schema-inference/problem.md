# 17 — Schema inference: how dlt decides column types

When dlt sees a JSON value for the first time, it picks a SQL type. When a later value disagrees, the `data_type` knob (from `schema_contract`) decides what happens. This exercise drills the inference rules and the resolution behavior — the layer *below* the contract policies you learned in 04.

## What you should observe

| Input | dlt's inferred type | Notes |
|---|---|---|
| `42` | `bigint` | integers always widen to bigint |
| `3.14` | `double` | |
| `"alice"` | `text` | |
| `true` | `bool` | |
| `"2026-01-01T00:00:00Z"` | `timestamp` | ISO-8601 auto-detected (string → timestamp) |
| `None` | column stays untyped; `nullable=true` | |

When a *second* value conflicts (e.g. column was `bigint`, now you yield a string):

- `data_type="evolve"` (default) → dlt creates a **variant column** named `<col>__v_<new_type>` and writes the conflicting value there. Original column stays the original type.
- `data_type="freeze"` → raises `DataValidationError`.

## Goal

Run five tiny pipelines that each demonstrate one rule. After every run, print the inferred column → type map.

## Acceptance

1. **First-sight inference**: load `{"id": 42, "name": "alice", "score": 3.14, "active": true}` and confirm `id=bigint, name=text, score=double, active=bool`.
2. **Nullable inference**: load `{"id": 1, "note": None}` then `{"id": 2, "note": "x"}` — `note` exists, is `text`, nullable.
3. **ISO-8601 auto-detect**: load `{"id": 1, "created": "2026-01-01T00:00:00Z"}` — `created` is `timestamp`, not text.
4. **Variant column on type drift** (`evolve`): load `{"x": 42}` then `{"x": "forty-two"}`. Expect *two* columns: `x` (bigint) and `x__v_text` (text).
5. **`freeze` on type drift raises**: same drift as (4) but with `data_type="freeze"` → `DataValidationError`.

Use a different `dataset_name` per scenario so they don't share schema.

## Hints

- Read the inferred schema via `pipeline.default_schema.get_table(name)["columns"]` — each column has a `data_type` field.
- For (5), wrap the second `pipeline.run()` in `try/except dlt.exceptions.DataValidationError` and print the message.
- The variant suffix is literally `__v_<type>` (e.g. `__v_text`, `__v_double`). It's how dlt avoids destroying the original column when a conflicting value arrives.
