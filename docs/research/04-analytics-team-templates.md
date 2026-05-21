# Analytics-Team Templates — Bronze / Ingestion Layer Conventions

Survey of how production analytics teams structure the bronze / ingestion layer
in modern data-stack repos. Conventions extracted apply regardless of
ingestion tool (dlt, Fivetran, Airbyte, custom Python).

## Repos read

| Repo | Type | What it shows |
|---|---|---|
| [dbt-labs/jaffle-shop](https://github.com/dbt-labs/jaffle-shop) | Canonical dbt template | Modern staging conventions, sources, WAP branching |
| [dbt-labs/jaffle-shop-classic](https://github.com/dbt-labs/jaffle-shop-classic) | Original dbt template | Minimal staging layout still copied today |
| [cal-itp/data-infra](https://github.com/cal-itp/data-infra) (`warehouse/`) | Real production analytics repo (open-data team) | End-to-end: external tables → staging → intermediate → mart, runbooks, BigQuery |
| [fivetran/dbt_hubspot_source](https://github.com/fivetran/dbt_hubspot_source) | Packaged ingestion-pair dbt project | Convention for declaring Fivetran-loaded tables as dbt sources |
| [fivetran/dbt_fivetran_log](https://github.com/fivetran/dbt_fivetran_log) | Fivetran's own log pipeline | `staging/` sub-package pattern |

## Comparison table

| Dimension | jaffle-shop | jaffle-shop-classic | cal-itp/data-infra | fivetran/hubspot_source | fivetran/fivetran_log |
|---|---|---|---|---|---|
| Bronze name | "sources" → `raw_*` tables in schema `raw` | `raw_*` seeds | "external tables" in schema `external_<system>` | "sources" in schema `hubspot` | sources `fivetran_log` |
| Staging name | `models/staging/stg_<entity>.sql` | `models/staging/stg_<entity>.sql` | `models/staging/<domain>/stg_<system>__<table>.sql` | `models/stg_hubspot__<table>.sql` | `models/staging/` sub-package |
| Schema naming | `raw` → `staging` → `analytics` (marts) | seeds → staging → marts | `external_*` → `staging` → `mart_*` (per-domain BigQuery datasets via `+labels`) | `hubspot` (Fivetran-written) → `<target>_stg_hubspot` | same |
| Source declared in dbt? | Yes — `__sources.yml` per folder | No (seeds only) | Yes — `_src_<system>_external_tables.yml` per system | Yes — `src_hubspot.yml` | Yes |
| Bronze tests | freshness via `loaded_at_field` only | None | Parse-outcome rows tested separately; raw sources untested | None on source | None |
| Staging tests | `unique`/`not_null` on PKs, expression checks | None | `unique_combination_of_columns` on staging, broad column descriptions | `unique`/`not_null` on PKs in stg `.yml` | minimal |
| Doc discipline | One `.yml` per `.sql` (stg_orders.sql + stg_orders.yml) with column descriptions | Single `schema.yml` for all of staging | One `_stg_<system>.yml` per system folder + shared `docs.md` via `{{ doc() }}` blocks | Per-table `.yml` + `docs.md` block library | per-table |
| Folder grouping | flat `staging/` | flat `staging/` | nested `staging/<domain>/<system>/` (e.g. `staging/payments/littlepay/`) | flat | nested by package |
| Ingestion co-located? | No (separate `jafgen` seed) | Seeds in repo | Yes — `airflow/`, `jobs/`, `services/`, `kubernetes/` siblings to `warehouse/` | No (Fivetran external) | No |
| CI on PR rebuilds bronze? | No — staging+marts only against cloned prod | No | No — bronze (`external_*`) untouched, staging+ rebuilt with personal schema prefix | n/a (package) | n/a |
| Runbooks | None | None | `runbooks/data/*.ipynb` (backfills, partition fixes) | None | None |

## Canonical bronze layout (median of what real teams do)

```
warehouse/                          # or repo root
├── models/
│   ├── staging/
│   │   ├── <system>/               # one folder per source system
│   │   │   ├── _src_<system>.yml   # dbt sources block — declares bronze tables
│   │   │   ├── _stg_<system>.yml   # column docs + tests for stg_* models
│   │   │   ├── stg_<system>__<table>.sql
│   │   │   └── ...
│   ├── intermediate/
│   └── marts/
├── macros/
├── seeds/
└── tests/
```

Key choices:

1. **Bronze is *not* a dbt-materialised layer.** It's whatever the ingestion
   tool wrote into a `raw_*` / `external_*` / `<vendor>` schema, declared to
   dbt as a `source:` block. Nobody materialises a "bronze" model.
2. **Source files live next to their staging models**, prefixed with
   `_src_` so they sort to the top of the folder.
3. **Staging model naming**: `stg_<source-system>__<table>` (double
   underscore separator). Examples: `stg_hubspot__contact`,
   `stg_littlepay__settlements`, `stg_gtfs_schedule__agency`.
4. **One `.yml` per model** (or one shared `_stg_<system>.yml`) carrying
   column descriptions and PK tests. Bronze itself usually only carries
   freshness checks via `loaded_at_field`.
5. **First real tests run at the staging layer**, not bronze. Bronze is
   considered "whatever the vendor gave us"; staging is the first contract.

## Where everyone agrees

- **Bronze = a dbt `source:`**, never a model. Even Fivetran/Airbyte-written
  tables are wrapped this way so downstream models depend on `{{ source() }}`
  and the lineage graph is complete.
- **One source system per folder.** Mixing HubSpot and Stripe tables in
  the same `staging/` directory is universally avoided once a repo has more
  than one system.
- **Staging is one-to-one with bronze.** `stg_X` reads exactly one
  `source('system', 'X')`, renames columns, casts types, parses timestamps,
  and does nothing else. No joins.
- **PK uniqueness + not-null is the bronze↔silver contract.** Every team
  puts `unique` + `not_null` on the surrogate or natural key at the staging
  layer; downstream silver/marts assume this.
- **`raw_*` / `_external_*` schemas are CI-immutable.** No PR builds bronze.
  PRs only rebuild staging-and-above into a developer-prefixed schema.
- **Freshness is declared at the source, not staging.** `loaded_at_field:`
  on the source table is the universal signal for ingestion health.
- **SQL-only at staging.** Renames, casts, light cleaning. Business logic
  is forbidden — that's intermediate's job.

## Where teams diverge

- **Bronze schema naming.** `raw` (jaffle-shop, most Fivetran templates) vs
  `external_<system>` (cal-itp, common when bronze is GCS/S3 external
  tables) vs vendor-named `hubspot` / `stripe` (Fivetran default when the
  connector picks the schema). No consensus, but the trend is
  source-system-namespaced (`raw_hubspot.contact` rather than
  `raw.hubspot_contact`).
- **Folder depth.** jaffle-shop keeps `staging/` flat because there's one
  e-commerce source. cal-itp nests two levels (`staging/payments/littlepay/`)
  because they have ~15 systems across 8 domains. Threshold seems to be
  ~3 source systems.
- **Whether ingestion lives in the same repo.** cal-itp co-locates
  Airflow, Kubernetes manifests, Python jobs, and the dbt project in one
  monorepo (`airflow/`, `jobs/`, `services/`, `warehouse/`). Most other
  teams split: ingestion in one repo, dbt in another. Co-location wins
  when the same team owns both; split wins when data-platform and analytics
  are separate teams.
- **Doc verbosity.** jaffle-shop writes a `.yml` per `.sql`. cal-itp uses
  a single `_stg_<system>.yml` per folder plus shared `docs.md` blocks
  referenced via `{{ doc('column_x') }}`. The shared-block pattern scales
  better past ~30 staging models.
- **Whether staging adds anything beyond renames.** Most teams: pure
  rename+cast. cal-itp adds parse-outcome staging models
  (`stg_gtfs_schedule__download_outcomes`) that surface ingestion failures
  as queryable rows — a pattern worth stealing.
- **Operator hand-off.** cal-itp keeps Jupyter runbooks
  (`runbooks/data/*.ipynb`) for backfills and partition surgery. Most
  templates have nothing. Real production teams *always* have something,
  even if just a `RUNBOOK.md` next to the ingestion code.
- **WAP / branching.** jaffle-shop documents a `staging` long-lived branch
  cloned from prod. cal-itp uses developer schema prefixes (`andrew_mart_gtfs`)
  on a shared dev BigQuery project instead. Both work; the schema-prefix
  pattern needs less infra.

## Recommendations for a fresh team (2026)

If starting today:

1. **Treat bronze as data, not code.** Whatever lands from dlt / Fivetran /
   Airbyte is bronze. Don't write dbt models for it. Declare it as a
   `source:` and move on.
2. **Schema name: `raw_<system>`** (one schema per source system). Avoids
   the cal-itp problem of mixing `external_gtfs_schedule` + `external_littlepay`
   + ad-hoc `raw_` in the same warehouse.
3. **Folder layout from day one**: `models/staging/<system>/`. Even with
   one source, the structure scales. Add `_src_<system>.yml` and
   `_stg_<system>.yml` siblings.
4. **Staging naming**: `stg_<system>__<table>`. The double-underscore is
   the de-facto standard since the 2020 dbt blog post that codified it.
5. **Tests**: bronze gets `loaded_at_field` for freshness; staging gets
   `unique` + `not_null` on the PK. Nothing more until something breaks.
6. **Steal cal-itp's outcomes pattern**: alongside `stg_<system>__<table>`,
   emit `stg_<system>__<table>_outcomes` rows from the ingestion tool itself
   (success, exception, response code). dlt emits this in `_dlt_loads` —
   wrap it as a staging model so analysts can query ingestion health in SQL.
7. **CI**: PRs rebuild staging-and-above against a developer-prefixed
   schema. Never rebuild bronze on a PR. Use Slim CI (`--defer
   --state`) to only rebuild changed models.
8. **Co-locate ingestion + dbt** in one repo if one team owns both;
   otherwise split and have the ingestion repo publish a stable
   `sources.yml` snippet the dbt repo imports.
9. **Runbook discipline**: a `runbooks/` directory in the same repo as the
   ingestion code, one `.md` per failure mode (auth expired, schema drift,
   backfill, partition rebuild). Cal-itp's Jupyter approach is overkill
   for most teams; plain Markdown is fine.
10. **Avoid premature abstraction**: no "bronze framework", no custom
    materialisation, no generic ingestion macro. Use the vendor tool's
    conventions and write the staging SQL by hand. Every team that built
    a bronze framework regretted it within 18 months.
