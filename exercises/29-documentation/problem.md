# 29 — Documentation discipline

**Bucket 8 of the practitioner patterns doc.** A pipeline without docs is the *next* engineer's tax. dlt makes most documentation queryable from code via decorator metadata; you just have to put it there. Three artefacts:

1. **Resource docstring** — the WHAT and the WHY: what entity, what cadence, what auth, what rate-limits.
2. **Column descriptions** — declared via `columns=` hints, surface in `dlt.default_schema.to_pretty_yaml()` and downstream dbt sources.
3. **Pipeline runbook** — a `RUNBOOK.md` next to the pipeline file: how to backfill, how to roll back, who to page.

## Goal

Take the GitHub `repos` resource and give it the full treatment:

1. A multi-line docstring covering: purpose, source URL, auth method, rate limit, incremental cursor, write disposition, owner.
2. Column-level descriptions on `id`, `name`, `full_name`, `updated_at` via `columns=` hint.
3. A `RUNBOOK.md` in the solution folder covering: how to backfill, how to roll back a load, common 429 errors, owner contact.

## Acceptance

`verify.py` asserts:
1. The decorated resource has a docstring ≥ 100 chars covering source/auth/cursor.
2. `pipeline.default_schema.get_table("repos")["columns"][col]["description"]` is non-empty for the four named columns.
3. `RUNBOOK.md` exists, ≥ 200 chars, contains the strings `Backfill`, `Rollback`, `Owner`.
4. `pipeline.default_schema.to_pretty_yaml()` includes the column descriptions (round-trip test).

## Hints

- Column description goes inside the `columns=` dict: `columns={"id": {"description": "GitHub repo numeric id", "data_type": "bigint"}}`.
- After `pipeline.run()`, fetch the schema with `pipeline.default_schema.get_table("repos")`.
- The runbook is just a text file; the verifier reads it as plain text.
- This is the only exercise where solution.py is *also* the documentation example — your goal is to make the file itself readable.
