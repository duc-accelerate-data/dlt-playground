# 20 — Multi-version schema drift over time

Real sources drift across many versions: a column appears, then gets renamed, then a type widens. The "right" reaction depends on which kind of drift it is and which layer is consuming downstream.

This timeline reproduces four common transitions over the same `people` entity:

| Version | Change vs previous |
|---------|--------------------|
| v1 | baseline: `{id, name, country, age:int}` |
| v2 | **column added**: `email` |
| v3 | **column renamed**: `name` → `full_name` |
| v4 | **type widened**: `age` becomes string |

## Goal

Run each version through the same pipeline in order and observe what each contract policy does at each step. Document the resulting schema and row count after every step.

Then propose a **promotion checklist** — what a human should do at each transition (column add = automatic; rename = create alias view; type widen = explicit migration).

## Acceptance

1. Three scenarios run end-to-end:
   - **A. Permissive**: `evolve / evolve / evolve` — everything goes through. Note which columns survive after v3 (renamed) and v4 (widened).
   - **B. Strict**: `evolve / freeze / freeze` — v2 raises (new column), v3 raises (new column too, since renames look like add+abandon), v4 raises (type change).
   - **C. Hybrid**: `evolve / evolve / freeze` — v4 type widening blocks; v2/v3 pass.
2. After each run, print: `(version, raised?, columns, row_count)`.
3. Write `notes.md` extension at the bottom of `solution.py` summarizing how you'd handle each transition in prod.

## Hints

- A column rename in dlt looks like: drop old column (still in schema, no new data), add new column. The old column stays as a NULL-filled ghost — that's why renames need a manual cleanup migration.
- Type widening: `freeze` raises, `evolve` will *coexist* the old + new variant or coerce, depending on `data_type` mode.
- Use `dev_mode=True` per scenario to isolate state.
