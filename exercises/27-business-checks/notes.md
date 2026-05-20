# Notes — Business data checks

- **Recon = truth assertion across the boundary.** Source has 1,000 orders → destination must have 1,000 orders. Source's sum of `total_cents` = `X` → destination's sum = `X`. Anything else is silent data loss or duplication.
- **Hold expected totals in code, not in the test row count.** `expected = sum(o["total_cents"] for o in ORDERS)` is reproducible; `assert n == 24950` rots the moment someone edits the fixture.
- **`LEFT JOIN ... IS NULL` is the universal orphan detector.** Parent → child *or* child → parent — the same pattern, just swap which side gets the LEFT JOIN.
- **Distribution checks catch upstream bugs early.** A single status spiking to 100% means the source is broken or the cursor wrapped around. A percent-cap test surfaces it before downstream BI does.
- **SQL > frameworks for ~80% of recon.** `duckdb.connect().execute(SQL).fetchone()` is enough. Reach for `dbt-expectations` / `Great Expectations` / Elementary when you need cross-table dependencies, severity tiering, or test-result history — not for "this column is non-null."
- **Ownership split.** Schema tests are eng-CI (block PR merge). Business checks are DQ-team-owned (block release / fire alerts). Same suite of asserts; different lifecycle and SLA.
- **Make failure messages actionable.** `assert n == expected` is useless when it fails. `assert n == expected, f"row drift: src={expected} dst={n}"` lets the on-call read the alert and act without opening the test file.
- **Don't put checks in notebooks.** Notebooks are exploratory; tests in CI are enforced. The pattern `nb-recon → copy-into-test` is the right one-way flow.
