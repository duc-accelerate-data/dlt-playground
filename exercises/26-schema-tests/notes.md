# Notes — Schema tests

- **One master assertion.** `info.has_failed_jobs is False` is the single most valuable check — if it's True, *everything downstream is suspect*. Every CI run should fail loudly on this.
- **Don't hard-code row counts.** A test that says `assert n == 10000` breaks the day someone backfills. Assert ranges (`1 <= n <= 1e6`), not exact integers (anti-pattern 3.16). Hard counts belong in business recon (exercise 27), not schema tests.
- **Schema hash = drift detector.** `pipeline.default_schema.stored_version_hash` is deterministic for a given schema. Persist it after a successful production run and assert future runs match — any drift trips CI before the data lands.
- **`schema_contract="freeze"` is the strongest CI gate.** A failing build because a vendor added a column is *good* — you want a human to look at it. Forensic pipelines that must tolerate dirty data use `discard_row` instead.
- **Use dedicated pipeline names per test scenario.** `pipeline_name="schema_freeze_demo"` won't fight your happy-path `pipeline_name="chess_bronze"` for state. Mixing them produces flaky tests.
- **Pydantic at the boundary** (pattern 3.9) is the typed alternative — declare `columns=MyPydanticModel`, set `schema_contract={"columns": "freeze"}`, get extra-field rejection for free. Best when downstream consumers depend on exact shape.
- **Schema tests vs business checks.** Schema tests = "the data has the right shape." Business checks = "the numbers make sense." They live in separate suites with different ownership — schema in eng CI, business in DQ ownership.
