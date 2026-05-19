# dlt Playground — Beginner → Intermediate

A realistic, industry-shaped playground for learning [dlt](https://dlthub.com) (data load tool) end-to-end.
You will build a production-style ingestion layer (bronze) over four sources, hit real schema-drift, credential, and incremental-cursor problems, and graduate with the muscle memory to ship a `dlt.pipeline()` in your real job.

## Why this exists

dlt tutorials show you `dlt.pipeline(...).run([{"id": 1}])`. Real life shows you a flaky REST API, a Postgres source with bad timezones, three teams arguing about merge strategy, and a Slack thread asking why bronze re-loaded 80M rows last night. This playground stages the second scenario.

## Sources

| Source             | Auth      | Shape           | Why it's here                                |
| ------------------ | --------- | --------------- | -------------------------------------------- |
| **Chess.com REST** | none      | nested JSON     | canonical dlt example — verified-source feel |
| **GitHub REST**    | PAT       | paginated, rate-limited | real auth + cursor + 304 handling     |
| **Synthetic CSV/JSONL** | none | controlled drift | drives schema-contract + dedup exercises    |
| **Postgres**       | user/pwd  | SQL incremental | CDC-style `updated_at` cursor + merge       |

All destinations are **DuckDB** (`data/warehouse.duckdb`) — single dev-friendly target so the brain stays on dlt, not infra.

## Quick start

```bash
# 1. Python 3.11+
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. Optional Postgres source (only needed for ex 13+)
docker compose up -d postgres
# seeds data/postgres-seed/*.sql automatically

# 3. Copy env template and fill in GITHUB_TOKEN if you want exercises 04, 06
cp .env.example .env

# 4. Run any exercise
python exercises/01-pipeline/starter.py     # follow problem.md, edit starter.py
python exercises/01-pipeline/solution.py    # peek if stuck
```

## How to use this repo

Each `exercises/NN-concept/` folder contains:

- `problem.md` — the scenario, learning goal, acceptance criteria
- `starter.py` — minimal skeleton, fill in the TODOs
- `solution.py` — annotated reference solution (read after attempting)
- `notes.md` — "what you should remember" — industry conventions, gotchas

Go in order — concepts build on each other. Each exercise should take 15–30 minutes.

## Concept index

| # | Concept | Skill level | dlt primitive |
|---|---------|-------------|---------------|
| 01 | [Pipeline](exercises/01-pipeline) | beginner | `dlt.pipeline()` |
| 02 | [Resource](exercises/02-resource) | beginner | `@dlt.resource` |
| 03 | [Source](exercises/03-source) | beginner | `@dlt.source` |
| 04 | [Schema contract](exercises/04-schema-contract) | intermediate | `schema_contract` |
| 05 | [Write disposition](exercises/05-write-disposition) | beginner | `write_disposition` |
| 06 | [Incremental cursor](exercises/06-incremental) | intermediate | `dlt.sources.incremental` |
| 07 | [Normalize + control columns](exercises/07-normalize) | intermediate | `_dlt_id`, `_dlt_parent_id`, `_dlt_load_id` |
| 08 | [Parent / child transformer](exercises/08-parent-child) | intermediate | `@dlt.transformer` |
| 09 | [Dataset name](exercises/09-dataset-name) | beginner | `dataset_name`, env switching |
| 10 | [Verified source + `.with_resources` / `.apply_hints`](exercises/10-verified-source) | intermediate | `.with_resources()`, `.apply_hints()` |
| 11 | [State](exercises/11-state) | intermediate | `dlt.current.resource_state()` |
| 12 | [Load packages](exercises/12-load-packages) | intermediate | `_dlt_loads`, `load_id` |
| 13 | [Naming convention](exercises/13-naming) | intermediate | `[schema] naming = ...` |
| 14 | [Merge keys / dedup](exercises/14-merge-keys) | intermediate | `primary_key`, `merge_key`, `dedup_sort` |
| 15 | [Destination capabilities](exercises/15-destination-caps) | intermediate | destination-specific behavior |
| 16 | [Config providers + secrets](exercises/16-config-secrets) | intermediate | `dlt.secrets.value`, `section=` |
| 20 | [Multi-version schema drift](exercises/20-drift-timeline) | intermediate | 4-version timeline + 3 contract policies |
| 21 | [Retries + 429 / backoff](exercises/21-retries) | intermediate | `dlt.sources.helpers.requests.Client` |
| 22 | [Partial failure + resume](exercises/22-partial-failure) | intermediate | atomic load packages, `_dlt_loads.status` |
| 23 | [Streaming pagination + memory](exercises/23-streaming) | intermediate | generators, `chunk_size` |
| 24 | [Data quality + PII redaction](exercises/24-data-quality) | intermediate | `add_filter`, `add_map`, Pydantic `columns=` |

## Verifying your solutions

Each exercise ships a `verify.py` that runs the solution and asserts the resulting state:

```bash
# verify one
python exercises/01-pipeline/verify.py

# verify everything
python verify_all.py

# verify a subset
python verify_all.py 04 05 14 20
```

Exercises that need a GitHub PAT (06, 10, 11, 16) print `SKIP` when the token is missing.

## Industry best-practice cheat sheet

Sources: dlt-hub docs (1.26+), dlt-hub `verified-sources` repo, Fivetran connector lifecycle, dlt-hub blog (schema-evolution, data-quality-lifecycle), real `dlt.pipeline()` GitHub usage.

### Scope
- One pipeline ≈ one **vendor / system**, not one table. Group resources that share auth + rate limit.
- Pipeline name encodes purpose, not implementation: `salesforce_bronze`, not `salesforce_dlt_v3`.

### Schema-contract policy (prod default)
- `tables: evolve, columns: freeze, data_type: freeze` for **bronze** — new tables OK (sources add objects), new columns require a deliberate human decision.
- `discard_row` for forensic / audit pipelines where one bad row should not block the load.
- Set at `@dlt.source` level, override at resource level only when justified.

### Credentials
- Never inline. Always `.dlt/secrets.toml` for local, env vars (`SOURCES__GITHUB__ACCESS_TOKEN`) for CI/prod.
- One section per *connection*, not per *vendor* — multi-tenant sources (`salesforce_prod`, `salesforce_sandbox`) need separate sections.
- Use `dlt.secrets.value` as the default in the resource signature so the resolver knows it's required.

### Incremental cursor wiring
- Prefer a **server-side updated_at** over `created_at` — captures backfills.
- `initial_value` = epoch (`"1970-01-01T00:00:00Z"`) for first run; production overrides via env.
- Add `lag` (a.k.a. attribution window) when the upstream system can mutate records after creation — 1h for OLTP, 7d for marketing/CRM, 30d for ad networks.
- For backfills, `end_value` plus `write_disposition="append"` on a date-partitioned target.

### Bronze table layout
- `dataset_name` = `bronze_<vendor>` (or `src_<vendor>` if you prefer dbt's `sources` mental model).
- One table per logical entity. Child arrays get auto-extracted by dlt's normalizer — don't pre-flatten.
- Control columns (`_dlt_id`, `_dlt_load_id`) are bronze's source of truth for lineage; downstream silver/gold should reference them, not the source PK.

### Write disposition decision tree
- Stateless events (page views, clicks) → `append`.
- Stateful, no history needed → `merge` with `primary_key`.
- Stateful with history → `merge` + `strategy="scd2"`.
- Full reload acceptable (small reference data) → `replace`.

### Normalize / control columns
- `_dlt_id` is content-addressable when no PK is declared — duplicate input row → same `_dlt_id`.
- `_dlt_parent_id` is FK from child → parent's `_dlt_id`. Never override it.
- Freezing `tables` on first run is a foot-gun — let dlt create child tables once, *then* tighten.

## Repo layout

```
dlt-playground/
├── README.md                  ← you are here
├── pyproject.toml             ← deps
├── .env.example
├── docker-compose.yml         ← optional Postgres source
├── .dlt/
│   ├── config.toml            ← non-secret defaults
│   └── secrets.toml.example
├── data/
│   ├── synthetic/             ← CSV / JSONL fixtures with controlled drift
│   ├── postgres-seed/         ← SQL seed for docker postgres
│   └── warehouse.duckdb       ← created at runtime (gitignored)
├── shared/
│   ├── chess_source.py
│   ├── github_source.py
│   └── synthetic_source.py
└── exercises/
    ├── 01-pipeline/
    │   ├── problem.md
    │   ├── starter.py
    │   ├── solution.py
    │   └── notes.md
    ├── 02-resource/
    │   └── ...
    └── ...
```

## Verifying your solutions

Each exercise's `solution.py` is runnable. After running, inspect with:

```bash
python -m dlt pipeline <pipeline_name> info
python -m dlt pipeline <pipeline_name> show           # opens Streamlit
# Or query DuckDB directly:
duckdb data/warehouse.duckdb -c "SELECT * FROM <dataset>.<table> LIMIT 10"
```

## License

MIT. Fork freely.
