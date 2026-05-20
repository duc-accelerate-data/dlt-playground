# 05 — Write disposition

Three modes:

| Disposition | When | Behavior |
|-------------|------|----------|
| `replace`   | small reference data, full snapshot acceptable | drop+reload destination table |
| `append`    | immutable events (page views, logs)            | insert all rows, never dedup  |
| `merge`     | stateful entities (orders, users)              | upsert by `primary_key` / `merge_key` |

## Goal

Load the same `events` resource three times under three different dispositions and observe row counts.

## Acceptance

After loading day-1 + day-2 events twice (so 4 runs total):

| Disposition | Expected row count | Reasoning |
|-------------|---|---|
| `replace`   | 5  | drops + reloads each run; only day-2 survives |
| `append`    | 20 | 5 rows × 4 runs, no dedup |
| `merge` (primary_key=event_id) | 9 | distinct event_ids across day-1 (e1–e5) + day-2 new (e6–e9); day-2's duplicate of e3 collapses |

Print the actuals — the *insight* is that the math falls out of the disposition rule.

## Hints

- `replace` ignores `primary_key`.
- `append` always grows.
- `merge` needs `primary_key="event_id"`.
- Reset between policies — different `dataset_name` per disposition.
