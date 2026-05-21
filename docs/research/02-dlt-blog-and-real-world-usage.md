# dlt-hub Stated Best Practices vs. Real-World Usage

Research date: 2026-05-21. Sources read directly via `mcp__read-website-fast__read_website` and `raw.githubusercontent.com`. The canonical `docs/general-usage/best-practices` URL 404s — best-practices guidance is scattered across topical docs and the blog.

---

## Best practices per dlt-hub

### Write disposition decision tree
dlt's incremental docs frame the first design question as "stateful vs. stateless": stateless events → `append`; stateful with history → `merge` with SCD2; stateful without history → `merge` (when source supports incremental filtering) or `replace` (full refresh). Source: [incremental-loading docs](https://dlthub.com/docs/general-usage/incremental-loading).

### Cursor-based incremental loading
Use `dlt.sources.incremental("updated_at", initial_value=...)` as a resource argument; dlt persists `last_value` in state, deduplicates by `primary_key`, and supports `end_value` for stateless backfills that can run in parallel with regular incremental loads. Declare `row_order="asc"|"desc"` so dlt can stop pagination when the cursor exits the range — only safe when the source returns ordered results. Backfills should load one small partition first to avoid races on dataset creation. Source: [cursor docs](https://dlthub.com/docs/general-usage/incremental/cursor).

### Schema contracts
Three entities (`tables`, `columns`, `data_type`) × four modes (`evolve`, `freeze`, `discard_row`, `discard_value`). Default is fully permissive `evolve` — type mismatches become variant columns. Recommended pattern: `{"tables": "evolve", "columns": "freeze"}` to lock column shape but allow new nested tables; pair with Pydantic models for authoritative typing (`DltConfig: {"is_authoritative_model": True}`). New tables (first load) always behave as `evolve` regardless of setting. Source: [schema-contracts docs](https://dlthub.com/docs/general-usage/schema-contracts).

### Operational health
dlt's own blog pushes two operational practices: (1) read `_dlt_loads` and join on `load_id` to audit data freshness instead of relying on exit codes; (2) read schema deltas from dlt metadata to detect silent schema evolution. Sources: [auditing-data-freshness-with-dlt](https://dlthub.com/blog/auditing-data-freshness-with-dlt) and [schema-monitoring-with-metadata](https://dlthub.com/blog/schema-monitoring-with-metadata) (both linked from the blog index; full bodies are JS-rendered and partially gated).

### Deployment
Officially recommended first deploy: GitHub Actions (generous free tier). The deploy docs are now an index pointing at GitHub Actions, Airflow Composer, Dagster, and "run inside Snowflake/Databricks". Source: [deploy overview](https://dlthub.com/docs/walkthroughs/deploy-a-pipeline).

### Dev-loop hygiene
`dev_mode=True` on `dlt.pipeline(...)` is the recommended iteration flag — it resets pipeline schema and state between runs so the inner loop is reproducible. Cited in a community-authored Cursor rule but echoed in the official tutorials.

### Agent-era guidance (dltHub blog, Apr–May 2026)
dltHub's recent positioning: "91% of new dlt pipelines are AI-written", and the blog now emphasizes ontology engineering, agent guardrails, and the AI Workbench. Practical takeaway: write declarative `rest_api_source` configs (LLM-friendly) instead of imperative resources. Sources: [introducing-dlthub-pro](https://dlthub.com/blog/introducing-dlthub-pro), [llm-ontology-schema-evolution](https://dlthub.com/blog/llm-ontology-schema-evolution).

---

## What the wild actually does

GitHub code-search totals (excluding `org:dlt-hub`, Python only):

| Pattern | Hits |
|---|---|
| `dlt.pipeline(` | 2,640 |
| `rest_api_source` | 380 |
| `dlt.sources.incremental` | 373 |
| `schema_contract` | 217 |
| `dev_mode=True` | 183 |

So schema contracts appear in roughly **8%** of `dlt.pipeline(...)` files, and incremental cursors in **~14%**. Most pipelines are dispositions-only.

### Observed patterns from sampled files

**Naming.** Pipeline name almost always equals the source domain: `nba_pipeline`, `chess_pipeline`, `meta_backfill`, `github_extraction`, `nve_magasin`, `jaffle_shop`, `etl_benchmark`. Dataset names trend toward layer or schema: `raw`, `bronze_raw`, `raw_nve`, `nike_campaigns`. Repos: [matsonj/nba-monte-carlo](https://github.com/matsonj/nba-monte-carlo/blob/HEAD/dlt/nba_pipeline.py), [hnawaz007/pythondataanalysis](https://github.com/hnawaz007/pythondataanalysis/blob/HEAD/ETL%20Pipeline/dltproject/chess_pipeline.py), [suwa-sh/open-process-mining](https://github.com/suwa-sh/open-process-mining/blob/HEAD/dlt/pipelines/github_pipeline.py).

**Sources: declarative wins for REST.** Recent (2025–2026) pipelines overwhelmingly use the declarative `rest_api_source` / `rest_api_resources` config — see [billwallis/billiam-data-stack/src/ingestion/oura.py](https://github.com/billwallis/billiam-data-stack/blob/HEAD/src/ingestion/oura.py), [EmilLindfors/demo_warehouse/nve.py](https://github.com/EmilLindfors/demo_warehouse/blob/HEAD/nve.py), [chocholous/bohemian-hackathon/pipelines/sources/meta_ads.py](https://github.com/chocholous/bohemian-hackathon/blob/HEAD/pipelines/sources/meta_ads.py). Older pipelines still hand-roll `@dlt.resource` generators with `requests`. SQL ingestion always uses `sql_database` ([carlospadron/etl/dlt/main.py](https://github.com/carlospadron/etl/blob/HEAD/dlt/main.py)).

**Verified sources vs. custom.** Mixed. `chess` and `jira` use verified sources; Facebook Ads, custom REST APIs, and proprietary SaaS uniformly hand-roll resources with raw SDK calls ([MartNguyen/marketing-data-pipeline/backfill.py](https://github.com/MartNguyen/marketing-data-pipeline/blob/HEAD/backfill.py)).

**schema_contract in the wild.** Of 217 hits, most are inside `venv/` or vendored copies of dlt itself. Genuine application usage is rare. One clean example: [rachemelendres/dlt-dbt-dagster/spacex_pipeline.py](https://github.com/rachemelendres/dlt-dbt-dagster/blob/HEAD/dlt_dbt_dagster/dlt/spacex_pipeline.py) — uses `{"tables": "evolve", "columns": "discard_value", "data_type": "freeze"}` on the source decorator, exactly the docs' recommended shape.

**Credentials.** Three patterns dominate, in this order:
1. `os.environ[...]` then assigning to `DESTINATION__BIGQUERY__CREDENTIALS__*` env vars (MartNguyen).
2. `.dlt/secrets.toml` + `dlt.secrets.value` / `dlt.config.value` (suwa-sh, ZhDmitriy).
3. Connection strings built inline and passed to `dlt.destinations.postgres(url)` (carlospadron).
Almost nobody uses Airflow/Dagster secret backends with dlt directly; secrets get mirrored into env vars first.

**Incremental cursors.** When used, the canonical `updated_at` / `created_at` ISO-timestamp pattern with `initial_value="1970-01-01T00:00:00Z"` dominates. `end_value` backfills exist but only in mature pipelines ([rstover-fo/cfb-database](https://github.com/rstover-fo/cfb-database/blob/HEAD/src/pipelines/run.py) has explicit `--mode backfill --years` CLI). `row_order` is almost never set.

**Deployment shapes.**
- Standalone `python pipeline.py` driven by **GitHub Actions** cron — most common for hobby/personal.
- **Dagster asset** wrapping the pipeline ([mazino2d/jaffle-shop](https://github.com/mazino2d/jaffle-shop/blob/HEAD/dag/assets/ingestion.py), [rachemelendres/dlt-dbt-dagster](https://github.com/rachemelendres/dlt-dbt-dagster)).
- **Airflow** via `PipelineTasksGroup` from dlt's airflow helper (less common in samples; heavily documented).
- AWS Lambda ([codingcyclist/dlt-aws-lambda](https://github.com/codingcyclist/dlt-aws-lambda)).

---

## Gaps between recommended and observed

| Recommendation | Reality |
|---|---|
| Use `schema_contract` to lock columns / freeze types | ~8% adoption. Most pipelines run with default `evolve` and discover schema drift downstream. |
| Use Pydantic `is_authoritative_model` for validation | Effectively zero adoption in non-dlt-hub repos — the feature is too new and still "work in progress" per the docs. |
| Declare `row_order` to short-circuit pagination | Rarely set. Pipelines re-fetch full result sets and rely on dlt's dedup. |
| Use `_dlt_loads` join for freshness audit | Not present in any sampled pipeline. Repos check `load_info.has_failed_jobs` and stop. |
| Use the airflow scheduler integration (`allow_external_schedulers=True`) | Rare. Most Airflow/Dagster wrappers just call `pipeline.run()` with no interval handoff — duplicating the state mechanism unnecessarily. |
| Use SCD2 for stateful data with history | Almost nobody — only spotted in the spacex sample. Default `merge` upsert is treated as good enough. |
| Use `.dlt/secrets.toml` | Loses to raw `os.environ` once code runs in CI/cloud. |
| `dev_mode=True` during iteration | ~7% of files. Many devs hit "why is my schema not refreshing" instead. |

---

## Most-cited foot-guns

1. **Silent schema evolution.** dlt evolves by default and creates variant columns on type drift; downstream consumers don't notice until queries break. The reason the entire "Operational Health" blog series exists.
2. **`IncrementalUnboundError` from passing a generator instead of a function** when creating resources dynamically. Called out as "the typical mistake" in the cursor docs.
3. **Backfill races on dataset creation.** Running multiple parallel `end_value` partitions on a brand-new dataset causes race conditions on schema/dataset creation; docs explicitly say "load one small partition first".
4. **`row_order` mis-used on unordered sources.** Docs warn: silently drops records that arrive out of order. Tempting to set, easy to misuse.
5. **Cursor field `None` / missing.** Default behavior raises; `on_cursor_value_missing` exists but is unknown to most users — they end up adding `add_map` workarounds instead.
6. **Manual Airflow runs with `allow_external_schedulers=True`** get a `(now, now)` interval and load nothing. Fix is to use "Run with Config" and pick a past logical date.
7. **`stage` / dataset name collision** when running parallel backfill DAG + incremental DAG against the same `dataset_name` — docs recommend renaming the pipeline (e.g. `..._new`) but the same `dataset_name`.
8. **Snapshot drift in parallel branches** (general orchestration foot-gun): committing schema changes from two branches simultaneously produces duplicate migrations — analogous warnings in dlt's verified-source patterns.
9. **Credential env var naming.** Dotted env vars (`DESTINATION__BIGQUERY__CREDENTIALS__PRIVATE_KEY`) with `\n`-escaped private keys are a recurring CI break — sample code in [MartNguyen/marketing-data-pipeline](https://github.com/MartNguyen/marketing-data-pipeline/blob/HEAD/backfill.py) literally has a `replace("\\n", "\n")` workaround.

---

## Cited sources

- https://dlthub.com/docs/general-usage/incremental-loading
- https://dlthub.com/docs/general-usage/incremental/cursor
- https://dlthub.com/docs/general-usage/schema-contracts
- https://dlthub.com/docs/walkthroughs/deploy-a-pipeline
- https://dlthub.com/blog (index; auditing-data-freshness and schema-monitoring-with-metadata article bodies were JS-gated, only blog index metadata read)
- https://dlthub.com/blog/introducing-dlthub-pro (title/lead only via index)
- Sampled repos: matsonj/nba-monte-carlo, hnawaz007/pythondataanalysis, billwallis/billiam-data-stack, EmilLindfors/demo_warehouse, mazino2d/jaffle-shop, chocholous/bohemian-hackathon, rstover-fo/cfb-database, suwa-sh/open-process-mining, rachemelendres/dlt-dbt-dagster, MartNguyen/marketing-data-pipeline, carlospadron/etl.

The canonical `https://dlthub.com/docs/general-usage/best-practices` URL returns 404 and is not cited.
