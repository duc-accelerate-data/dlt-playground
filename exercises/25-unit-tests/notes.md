# Notes — Unit tests for dlt resources

- **Test the generator, not the pipeline.** A resource is just a function that yields. `list(resource())` is the unit-test API. If your test calls `pipeline.run()`, it's an integration test and belongs elsewhere.
- **Mock at the HTTP layer, not the function layer.** `responses.add(GET, url, json=...)` is more realistic than `mocker.patch("api.fetch")` — it also catches off-by-one URL bugs and assertion-mode `responses` fails the test if any un-stubbed URL is hit. Belt + braces against accidental live network in CI.
- **Pagination tests need ≥2 stubbed pages.** One page is happy-path; two pages catches "did we follow the `next` link?". An empty-trailing-page test catches "did we stop?".
- **Incremental cursor tests don't need a destination.** Instantiate `dlt.sources.incremental("updated_at", initial_value=...)` directly and pass it into the resource. Inspect `resource.incremental._incremental` to confirm wiring.
- **`add_map`, `add_filter`, `add_yield_map`** are all pure-function decorators on a resource — test them by iterating the resulting resource and asserting on rows. Zero dlt internals required.
- **Pin time** when you have `pendulum.now()` defaults in source params: `from freezegun import freeze_time; with freeze_time("2026-05-20"): ...`.
- **Fast = under 1 second total.** Real source unit-test suites for ~20 resources should finish in under 5 seconds. Anything slower means you've crossed into integration territory.
- **CI lane:** unit tests run on every PR, no secrets, no DB. Integration tests (the `verify.py` files in the rest of the playground) run separately, slower, with destination access.
