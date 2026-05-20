# 27 — Business data checks (recon + rules)

**Bucket 4 of the practitioner patterns doc.** Schema tests say "the table exists with the right columns." Business checks say "the numbers make sense and the rules hold." These are SQL assertions that gate releases by *truth value*, not shape.

## What you'll cover

| Check class | This exercise |
|---|---|
| **Recon** — source vs destination row count | `test_source_destination_rowcount_recon` |
| **Recon** — sum of a monetary column matches input fixture | `test_total_amount_sums_match` |
| **Rule** — no negative monetary values | `test_no_negative_totals` |
| **Rule** — every parent has at least one child | `test_every_order_has_a_line_item` |
| **Rule** — referential integrity (`_dlt_parent_id` joins back) | `test_no_orphan_children` |
| **Rule** — required fields are populated | `test_required_fields_not_null` |
| **Distribution** — no single value dominates a categorical | `test_status_distribution_is_balanced` |

## Goal

Load the synthetic events + a small in-line orders fixture, then write a `pytest` suite that asserts the **truth** of the loaded data, not just its shape. Use `duckdb` directly for SQL — that's the production pattern (you don't need extra frameworks for ~80% of recon).

## Acceptance

`verify.py` runs `pytest exercises/27-business-checks/solution/test_business.py -q` and expects:
1. Exit code 0.
2. At least 7 business checks pass.
3. Each check carries a meaningful failure message — assertion text mentions the offending value.

## Hints

- `duckdb.connect(WH).execute("SELECT ... FROM dataset.table").fetchone()[0]` is your assertion primitive.
- The chess data in `bronze_chess` is already loaded by other verifiers — pick one of those datasets to recon against.
- For "every order has a line item": `LEFT JOIN ... WHERE child.order_id IS NULL` → must return 0.
- For sum recon, hold the expected total in Python so the test fails loudly when source data changes.
- Anti-pattern 4.x: don't bury checks inside notebooks. Test files in CI = enforceable; notebooks = aspirational.
