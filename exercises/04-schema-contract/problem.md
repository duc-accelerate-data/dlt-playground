# 04 — Schema contract

`schema_contract` tells dlt what to do when incoming data drifts from the existing schema. Three knobs: `tables`, `columns`, `data_type`. Each takes `evolve | freeze | discard_value | discard_row`.

## Goal

Run the synthetic `events` resource twice — once with day 1, once with day 2. Day 2 introduces a new column `experiment`.

Configure schema-contracts to model **three production policies** and observe the difference:

1. **Permissive bronze** (default): `evolve` everything — `experiment` column appears.
2. **Strict bronze**: `columns="freeze"` — the day-2 run raises `DataValidationError`.
3. **Forensic bronze**: `columns="discard_value"` — load succeeds, but `experiment` is silently dropped.

## Acceptance

Three pipeline runs in sequence; each prints the resulting column list. Strict mode must raise (catch and print the error).

## Hints

- Pass `schema_contract` to `pipeline.run(..., schema_contract={...})` for a per-run override.
- Use a different `dataset_name` per policy (`bronze_events_evolve`, `..._freeze`, `..._discard`) so they don't fight each other.
- `dlt.exceptions.DataValidationError` is what `freeze` raises.
