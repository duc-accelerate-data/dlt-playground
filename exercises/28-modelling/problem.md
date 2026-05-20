# 28 — Modelling techniques (SCD2, JSON columns, key choice)

**Bucket 7 of the practitioner patterns doc.** Once your bronze tables land, you make modelling choices that downstream silver/gold inherit forever. Three of them matter most:

1. **SCD Type 2** — "I need history of what each row used to look like."
2. **JSON vs flattened** — nested objects can stay as JSON columns, or auto-flatten into child tables. Pick by query pattern.
3. **Primary key choice** — surrogate (`_dlt_id`) vs natural (source's `id`) vs composite. Wrong choice = silent duplicates.

## Goal

Load three variations of a `customers` resource:

1. `customers_replace` — naive `replace`, no history.
2. `customers_scd2` — `write_disposition={"disposition": "merge", "strategy": "scd2"}` with `primary_key="customer_id"`, capturing valid-from/valid-to.
3. `customers_json` — preserve nested `address` as a JSON column instead of flattening it into `customers__address`.

Run twice (initial + updated state). Verify:

- replace dataset has only the *latest* row count.
- scd2 dataset has TWO rows for the updated customer, with `_dlt_valid_from` / `_dlt_valid_to` set.
- json dataset has `address` as a JSON-typed column with both nested fields queryable via `address->>'city'`.

## Acceptance

`verify.py` asserts:
1. `customers_replace.customers` has exactly 2 rows (final state only).
2. `customers_scd2.customers` has 3 rows total (1 unchanged + 2 versions of the updated one). At least one row has a non-null `_dlt_valid_to` (the retired version).
3. `customers_json.customers` has an `address` column with `data_type='json'` or `'complex'`, queryable via JSON path.

## Hints

- SCD2 syntax: `write_disposition={"disposition": "merge", "strategy": "scd2"}`. Requires `primary_key`.
- JSON preservation: declare the column with `columns={"address": {"data_type": "json"}}` on the resource.
- Two yields per resource: first run loads v1, second run loads v2 with one customer changed.
- `_dlt_valid_from` and `_dlt_valid_to` columns are added by dlt automatically when scd2 strategy is used.
