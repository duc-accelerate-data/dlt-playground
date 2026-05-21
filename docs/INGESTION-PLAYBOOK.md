# Ingestion Build Playbook

A vendor-agnostic playbook for building production ingestion pipelines. The patterns below hold whether you're using dlt, Fivetran, Airbyte, or hand-rolled Python — they're shaped by what real analytics teams converged on.

Drawn from the four research reports in `docs/research/`. Where a pattern is dlt-specific, see [DLT-PATTERNS.md](./DLT-PATTERNS.md).

---

## The mental model under all the tools

Every ingestion system — managed or code-first — exposes the same four-axis surface. The terminology differs; the mental territory is identical.

| Axis | What you decide | Fivetran calls it | Airbyte calls it | dlt calls it |
|---|---|---|---|---|
| **Extract mode** | Pull everything or just changes? | implicit (engine picks) | `Full Refresh` / `Incremental` | first run vs `dlt.sources.incremental` cursor |
| **Cursor** | What field signals "this row is new since last sync"? | hidden | per-stream `cursor_field` | `dlt.sources.incremental("updated_at")` |
| **Load mode** | How does the new data interact with existing rows? | `soft delete` / `history` | `Append` / `Overwrite` / `+Deduped` | `write_disposition`: `append` / `replace` / `merge` |
| **Schema contract** | What happens when upstream changes shape? | auto-propagate (no knob) | 4-option propagation policy | `schema_contract` per `tables` / `columns` / `data_type` |

**Translate these four decisions before writing any code.** Most ingestion failures trace to a wrong choice on one of them — usually load mode (someone picked `append` when they needed `merge`) or schema contract (no contract → silent drift → broken downstream queries weeks later).

---

## The build process — eight phases

Designed to be the same whether you're integrating Fivetran or writing dlt yourself.

### 1. Scope a single source

One pipeline = one source system, not one table.

- Group resources that share auth + rate limit (everything behind one `api_key` lives in one pipeline)
- Name the pipeline by the vendor + layer: `salesforce_bronze`, not `salesforce_dlt_v3`
- Decide: verified/managed connector, or custom code? Default to managed/verified — custom only when nothing exists

### 2. Inventory entities + decide load modes

Before writing any code, fill in a table like this:

| Entity | Grain | Mutable? | Has history? | Server-side cursor available? | Load mode |
|---|---|---|---|---|---|
| `accounts` | one row per account | yes | no | `updated_at` | **merge** + PK |
| `events` | one row per event | no (immutable) | n/a | `created_at` | **append** + cursor |
| `users` | one row per user | yes | yes | `updated_at` | **merge + SCD2** |
| `countries` | one row per country | no (small reference) | no | none | **replace** |
| `orders` | one row per order | yes | yes (status history) | `updated_at` | **merge + SCD2** |

Decision rules:

- **Immutable events** (clicks, page views, logs) → `append`
- **Stateful, no history needed** → `merge` with `primary_key`
- **Stateful with history needed** → `merge` + SCD2
- **Small reference data** → `replace` (full reload every run)
- **No cursor available** → still pick a load mode, but plan for full refresh frequency

This table belongs in `design.md` or equivalent and gets reviewed before code lands. The cost of changing it later is high — schema differs per mode.

### 3. Profile the source before writing the pipeline

Real production teams burn weeks when they skip this step.

- Hit the endpoint or query the source directly. Look at 100 rows.
- Are timestamps server-side (`updated_at` from the source) or client-side (`now()` when you fetched)? Only server-side timestamps are safe for incremental.
- Does the source mutate rows *after* creation? If yes by how long? (Salesforce: minutes. Marketing platforms: 7–30 days. Ad networks: 30 days.) That window determines your `lag` setting.
- What's the type of the cursor field? ISO datetime / UNIX epoch / `pendulum.DateTime` / monotonic int? The wire shape changes the cursor wiring.
- Does the API have a server-side filter for "since X"? If not, you'll pull everything every run.
- Are there per-tenant boundaries (one row from each customer in the response)? You may need `with_args(section=...)` per tenant.

### 4. Pick your schema-contract posture

The "official" recommendation across all vendors and dlt: **bronze should freeze columns, evolve tables.**

Concretely: new tables OK (sources add objects), new columns require a deliberate human decision, type changes require an explicit migration.

The "observed reality" in real-world dlt usage (from research report 2): **only ~8% of pipelines set any schema contract.** Most ship without one and discover drift downstream.

The honest tradeoff:

| Posture | What happens when source changes | Operational cost |
|---|---|---|
| **No contract (default `evolve`)** | Silent — variant columns appear, downstream queries break later | Low setup cost, high incident cost |
| **`columns: freeze`** | Load fails loudly when source adds a column | Need a human to review + bump the contract per change |
| **`columns: discard_value`** (forensic) | Load succeeds, drift logged but not surfaced | For audit pipelines where one bad row shouldn't block load |

Default for new pipelines: `freeze` columns, `evolve` tables, `freeze` data types. Pair with alerting on the failed load. Worth the human-in-the-loop cost for any pipeline downstream consumers depend on.

### 5. Pick your credential strategy

Three patterns dominate, in priority order:

1. **Secrets file in dev, env vars in prod.** Local: `.dlt/secrets.toml` or `~/.airbyte/config`. Prod: env vars or vault-injected secrets. The dev-prod boundary is a hard handoff — don't try to make the prod tool read the dev file.
2. **OAuth tokens: managed if available.** Fivetran auto-refreshes; Airbyte auto-refreshes. With dlt or custom code, you wire refresh logic yourself — and you *will* forget about it until a token expires at 3 AM.
3. **Multi-tenant sources need per-instance sections.** When the same source has multiple instances (prod Salesforce + sandbox Salesforce, US Stripe + EU Stripe), declare them as separate connection sections, not flags inside one. Wrap multi-auth in a typed union when more than one auth method is supported.

What real production code does (from research report 2): most teams mirror secrets into env vars early. Even when the platform supports a secret store, code reads from env. Plan accordingly.

### 6. Wire incremental cursors carefully

Five rules, distilled from research reports 1 and 2:

1. **Prefer server-side `updated_at` over `created_at`.** Captures backfills upstream did.
2. **`initial_value` = a far-past sentinel** for "from the beginning." Don't pick `1970-01-01` blindly — some APIs reject it (GitHub does). Use a value safely before any source data: `2008-01-01` for modern SaaS, `1990-01-01` if you have to go further.
3. **Add `lag` (attribution window) when upstream mutates after creation.** 1 hour for OLTP, 7 days for marketing/CRM, 30 days for ad networks. This is the leakage that breaks bronze if you don't model it.
4. **For backfills, use bounded `end_value` + a separate pipeline.** Same code, separate `pipeline_name` and `dataset_name`. Bounded backfills don't persist their cursor — that's the feature.
5. **`row_order="asc"` only when the source genuinely returns ordered results.** Tempting optimization (saves API quota by stopping early); easy to misuse on unordered sources (silently drops records).

### 7. Lay out the bronze tables

The universal pattern (confirmed across every analytics-team repo in research report 4):

```
warehouse/
└── models/
    └── staging/
        └── <system>/                       ← one folder per source system
            ├── _src_<system>.yml            ← dbt `source:` block declaring bronze tables
            ├── _stg_<system>.yml            ← column docs + tests for staging models
            ├── stg_<system>__<table>.sql    ← one staging model per bronze table
            └── ...
```

Key rules:

- **Bronze is *not* a dbt-materialised layer.** Whatever the ingestion tool wrote becomes a dbt `source:`. No materialised "bronze" model.
- **Schema naming: `raw_<system>`** (one schema per source system). `raw_hubspot.contact` beats `raw.hubspot_contact`.
- **Staging naming: `stg_<system>__<table>`** — double underscore separator, snake_case throughout.
- **One folder per source system.** Mixing systems in one staging folder is universally avoided once a repo has > 1 system.
- **Staging is one-to-one with bronze.** `stg_X` reads exactly one `source('system', 'X')`, renames columns, casts types, parses timestamps. No joins, no business logic.

### 8. Test the right layer

Where teams converge (research report 4):

| Layer | Tests | Why |
|---|---|---|
| **Bronze** | `loaded_at_field` (freshness) only | Bronze is "whatever the vendor gave us" — testing it is testing the vendor |
| **Staging** | `unique` + `not_null` on the PK; type casts validated | First real contract; downstream models assume these |
| **Intermediate / marts** | Business rules, range checks, referential integrity | Where logic lives |

The first test that ships should be: **PK uniqueness on staging.** That's the bronze↔silver contract. Everything else is improvement on top.

A pattern worth stealing from Cal-ITP (cited in research report 4): **emit ingestion-outcome rows from the tool itself as a queryable staging model.** dlt does this via `_dlt_loads`; wrap it as `stg_<system>__load_outcomes` so analysts can query ingestion health in SQL.

---

## Production runtime patterns

Things that ship in real production pipelines but are easy to miss.

### Idempotency

Idempotency = "running the same pipeline twice with the same input gives the same destination state." It's a property you opt into via your load-mode choice — it's not free.

| Load mode | Idempotent? |
|---|---|
| `append` | **No** — duplicates on re-run |
| `merge` + PK | **Yes** |
| `replace` | **Yes** (state-wise) |
| SCD2 | **Yes** (semantically — same input → no new version row) |
| Append + Deduped (Airbyte) | Yes |

If you have `append` without an incremental cursor, you have a future incident. Either add a cursor or switch to `merge`.

### Schema-change handling

The vendor mental models converge on three responses:

1. **Auto-propagate** (Fivetran default) — accepts everything silently; downstream consumers find out via broken queries
2. **Approve before applying** (Airbyte's "Approve all changes myself"; dlt's `freeze`) — schema change requires a code/config PR; load fails until reviewed
3. **Pause sync entirely** (Airbyte's "Stop future syncs") — block all loads until human resolves; conservative but spikes incident volume

The middle option is the production sweet spot for most pipelines. Schema changes flow through PR review, get tested in CI, deploy gated.

When a schema change is approved, the workflow is:

```
vendor adds column → load fails (freeze) → engineer opens PR adding column to allow-list → CI runs against staging → merge → prod unblocks on next run
```

The schema change becomes a git artifact reviewed like code.

### Backfill safety

When you need to fill historical data alongside production:

- **Separate pipeline + dataset.** Production keeps its cursor; backfill runs into its own namespace. Don't share `pipeline_name`.
- **Bounded windows.** Set both `initial_value` and `end_value` — this is what makes backfill mode not persist a cursor.
- **Idempotent within window.** Same backfill args twice → same rows. Achieved via `merge` + PK or `replace`.
- **Parallel month-windows for long histories.** Spin 12 backfill pipelines, one per month, into 12 datasets. Then `UNION ALL` in the silver layer. Faster than one giant load and easier to retry individual months.

### Resume semantics on partial failure

Load packages aren't atomic — jobs run in parallel and one can fail while others succeed. The truthful contract:

- Successful jobs commit; the load package stays on disk in a "partial" state
- Next pipeline run **resumes the partial package** before extracting fresh data
- A row appears in the load-tracking table (`_dlt_loads` for dlt) only when *all* jobs in a package succeed
- Downstream consumers filter on `status=0` (or equivalent) to ignore partials

This is the same mental model Fivetran uses internally — they just hide it behind a "running / succeeded / failed" status pill.

### Operational artifacts

Real production teams have, in order of importance:

1. **A `runbooks/` directory.** One Markdown file per failure mode. Auth expired. Schema drift. Backfill procedure. Partition rebuild. Plain Markdown is fine — don't over-engineer with Jupyter unless you actually need code in the runbook.
2. **A freshness gate.** A query that checks "did this bronze table get loaded in the last N hours?" and pages someone if not.
3. **Schema-drift alerting.** Either via `schema_contract="freeze"` failures, or by snapshotting the schema hash and alerting on change.
4. **A re-sync procedure.** "How do I drop and reload table X" — written down, not just in someone's head.

---

## Anti-patterns to avoid

Every team that built one of these regretted it within 18 months (research report 4):

| Anti-pattern | Why it fails |
|---|---|
| Custom "bronze framework" wrapping the ingestion tool | The wrapper drifts from the tool's actual behavior; debugging requires reading two codebases |
| Custom dbt materialisation for bronze | Reinvents what the ingestion tool already does; breaks vendor upgrades |
| Generic "ingest any source" macro | Specific connectors need specific handling; the macro grows special cases and becomes a fork of the tool |
| `append` everywhere "for safety" | Creates duplication burdens downstream; defeats incremental |
| Bronze tests with business rules | Tests vendor data instead of your code; flaps on benign upstream changes |
| Rebuilding bronze on every PR | Expensive and unnecessary; bronze is what the vendor wrote, not what you author |
| Mixing all sources in one staging folder | Becomes a tangle past three systems; refactor cost is real |
| Schema changes via manual `ALTER TABLE` | The ingestion tool regenerates schema each run; manual changes get clobbered |
| Hardcoded tokens in pipeline files | One leak away from a security incident; always read from config provider |
| Same `dataset_name` for production + backfill | Cursor collisions, dedup confusion, very fun to debug |

---

## Recommendations for a fresh team (2026)

If you're starting today, from scratch:

1. **Pick one ingestion tool and don't fork it.** dlt, Fivetran, or Airbyte — all three are fine. Wrappers around them aren't.
2. **One pipeline per source system.** Decide this on day one. Refactoring later is painful.
3. **Bronze is data, not code.** Declare it as a `source:` in dbt. Don't write models for it.
4. **Schema name: `raw_<system>`.** One schema per source system. Don't mix.
5. **Folder layout from day one**: `models/staging/<system>/`. Add `_src_` and `_stg_` YAML siblings.
6. **Staging naming**: `stg_<system>__<table>`. Double-underscore is the de-facto standard.
7. **PK test on staging** is the bronze↔silver contract. Ship before anything else.
8. **Freshness gate on bronze**: `loaded_at_field` + an alert. That's your data-freshness SLO.
9. **Set a schema contract.** Even `freeze columns + evolve tables` is enough to catch the silent drift case.
10. **Runbook discipline**: a `runbooks/` directory with one `.md` per failure mode. Cal-ITP-style Jupyter is overkill for most teams.
11. **Test ingestion outcomes as a staging model**: surface load success/failure as queryable rows. Best signal for ingestion health.
12. **Avoid premature abstraction**: no custom framework, no generic ingestion macro. Use the tool's conventions and write the staging SQL by hand.

The total volume of code here is tiny. The discipline is what makes it work.

---

## Where to dig deeper

| Topic | File |
|---|---|
| dlt-specific patterns and idioms | [DLT-PATTERNS.md](./DLT-PATTERNS.md) |
| Real dlt connector survey (10 connectors compared) | [research/01-dlt-verified-sources-survey.md](./research/01-dlt-verified-sources-survey.md) |
| dlt-hub stated practice vs GitHub reality | [research/02-dlt-blog-and-real-world-usage.md](./research/02-dlt-blog-and-real-world-usage.md) |
| Fivetran / Airbyte / dlt lifecycle comparison | [research/03-vendor-lifecycle-comparison.md](./research/03-vendor-lifecycle-comparison.md) |
| Analytics team templates and conventions | [research/04-analytics-team-templates.md](./research/04-analytics-team-templates.md) |
