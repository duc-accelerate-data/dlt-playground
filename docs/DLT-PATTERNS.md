# dlt Patterns — When and How to Use Them

dlt-specific patterns extracted from surveying real `verified-sources` connectors, dlt-hub blog/docs, and ~30 production dlt pipelines on GitHub. The general "what should bronze look like" lives in [INGESTION-PLAYBOOK.md](./INGESTION-PLAYBOOK.md) — this file is the dlt-specific layer.

Sources: research reports 01 and 02 in `docs/research/`.

---

## The stated-vs-observed gap

dlt-hub recommends many things that real-world users skip. Knowing the gap matters because copying production patterns blindly will steer you away from the safe defaults.

| Feature | Recommended | Actual adoption (GitHub) |
|---|---|---|
| `schema_contract` | "lock columns, freeze types" | ~8% of pipelines |
| Pydantic `is_authoritative_model` | use for validation | ~0% in non-dlt-hub repos |
| `row_order` on incremental | declare for short-circuit | rarely set |
| `_dlt_loads` join for freshness audit | recommended in blog | almost nobody does this |
| `allow_external_schedulers=True` with Airflow | recommended | rare; most just call `pipeline.run()` |
| SCD2 for stateful + history | recommended | almost zero adoption |
| `.dlt/secrets.toml` | recommended | loses to raw `os.environ` once in CI |
| `dev_mode=True` for iteration | recommended | ~7% — most don't know about it |

**Implication:** the dlt-hub recommendations are mostly right. Real-world skipping is laziness, not better judgment. Defaults to copy: declare a contract, use `dev_mode=True` while iterating, prefer `.dlt/secrets.toml` for local dev.

---

## The dlt mental model

dlt expresses the same four-axis ingestion model as Fivetran/Airbyte (see [INGESTION-PLAYBOOK.md](./INGESTION-PLAYBOOK.md) for the cross-vendor map). The dlt-specific surface:

| Axis | dlt mechanism |
|---|---|
| Extract | `@dlt.resource` (generator) + optional `dlt.sources.incremental` cursor |
| Cursor state | persisted in `_dlt_pipeline_state` (in the destination, per pipeline) |
| Load mode | `write_disposition`: `"append"` / `"replace"` / `"merge"` |
| Schema contract | `schema_contract` dict: `{tables, columns, data_type}` × `{evolve, freeze, discard_value, discard_row}` |
| Idempotency | guaranteed when `merge` + `primary_key`, or `replace` |

What's notable: dlt splits "load mode" and "history-keeping" into separate concerns. Fivetran's `history mode` and Airbyte's `Append + Deduped` bundle both. dlt's `merge` does dedup; SCD2 is a separate opt-in strategy.

---

## Source/resource shape

The canonical pattern from the verified-sources survey:

```python
@dlt.source(name="my_vendor")
def my_vendor_source(api_key: str = dlt.secrets.value):
    client = build_client(api_key)  # captured in closure

    @dlt.resource(name="entities", primary_key="id", write_disposition="merge")
    def entities(updated_at=dlt.sources.incremental("updated_at",
                                                     initial_value="2008-01-01T00:00:00Z")):
        yield from client.get_pages("entities", since=updated_at.start_value)

    return entities  # or [entities, other_resource, ...]
```

Five rules from the survey:

1. **`@dlt.source` returns multiple `@dlt.resource`s** — one source per auth domain, N resources per source
2. **Resources are defined inside the source** so they capture the shared client in closure
3. **Secrets are kwarg defaults** (`api_key: str = dlt.secrets.value`), never `os.environ[...]` reads
4. **Cursor is a resource kwarg default** (`updated_at=dlt.sources.incremental(...)`), not module state
5. **Transport lives in `helpers.py`** — pagination, retry, rate limit, auth. The `@dlt.source` is declarative

The closure pattern matters: if you define resources outside the source, you can't share the client without making it a global or passing it around. The closure keeps the resources tied to the auth context.

---

## Schema contract — when and how

Default to **`{tables: "evolve", columns: "freeze", data_type: "freeze"}`** for production bronze. Reasoning:

- `tables: evolve` — sources add new objects; that's normal, let them land as new tables
- `columns: freeze` — sources add new columns sometimes silently; freeze forces human review
- `data_type: freeze` — type drift creates `__v_<type>` variant columns that fragment the schema; freeze blocks them

Set at `@dlt.source` level; override at resource level only when justified.

```python
@dlt.source(name="vendor", schema_contract={
    "tables": "evolve",
    "columns": "freeze",
    "data_type": "freeze",
})
def vendor_source(): ...
```

**Critical gotcha**: do NOT set `tables: "freeze"` on the source decorator at *generation time*. dlt commits the schema after each resource extracts. Freezing tables before every resource has run once blocks subsequent resources from registering their tables and raises:

```
DataValidationError: Can't add table X because tables are frozen
```

The right sequence: ship with `tables: evolve` for the first load, let dlt create all the tables, *then* tighten to `tables: freeze` in a follow-up commit once everything has loaded successfully at least once.

### When a schema change happens

```
upstream adds column → schema_contract:freeze blocks the load → alert fires →
engineer opens PR adding column to allow-list → CI runs against staging →
merge → next prod run unblocks
```

The schema change becomes a reviewed git artifact, not a Slack thread.

### Variant columns — the foot-gun

When `data_type: evolve` and a type drift happens, dlt creates `<col>__v_<new_type>` (e.g. `amount__v_text`) and writes the conflicting value there. The original column stays its original type.

Variant columns are **load-time safety nets**. They prevent crashes; they don't solve the problem. Downstream consumers now have to coalesce `amount` and `amount__v_text`. Production rule: `data_type: freeze` in bronze + alerting on the failed load. Never silently accept variants.

---

## Credentials

Three patterns, in priority order:

### 1. Local dev: `.dlt/secrets.toml`

```toml
[sources.salesforce]
credentials.client_id = "..."
credentials.client_secret = "..."

[sources.salesforce.production]
credentials.client_id = "..."  # different instance

[sources.salesforce.sandbox]
credentials.client_id = "..."
```

Multi-instance via section namespacing. The connection name (`production` / `sandbox`) becomes part of the section path.

### 2. Production: env vars

```bash
SOURCES__SALESFORCE__CREDENTIALS__CLIENT_ID=...
SOURCES__SALESFORCE__CREDENTIALS__CLIENT_SECRET=...
```

dlt's config provider walks env → TOML → vault. Production: set env vars in your orchestrator's secret manager; the local TOML file isn't deployed.

### 3. Multi-auth: typed `@configspec` Union

When a source supports multiple auth flows (basic / token / OAuth), wrap them:

```python
@configspec
class BasicAuth(CredentialsConfiguration):
    email: str
    password: str

@configspec
class TokenAuth(CredentialsConfiguration):
    access_token: str

TVendorCredentials = Union[BasicAuth, TokenAuth]

@dlt.source
def vendor_source(credentials: TVendorCredentials = dlt.secrets.value):
    ...
```

Zendesk's `TZendeskCredentials` and Salesforce's `SalesforceAuth` are the references to copy.

### What real production code does

From the GitHub survey: most teams mirror secrets into env vars early. `.dlt/secrets.toml` works in dev but loses to env once code runs in CI/cloud. Plan for both — make sure env vars also resolve (they do by default).

**Anti-pattern**: hardcoding tokens in pipeline files. One leak away from a security incident. Always read from the config provider.

---

## Incremental cursors

```python
@dlt.resource(primary_key="id", write_disposition="merge")
def entities(updated_at=dlt.sources.incremental(
    "updated_at",
    initial_value="2008-01-01T00:00:00Z",  # safe pre-source-existence sentinel
    lag=3600,                               # 1h attribution window
    allow_external_schedulers=True,         # let Airflow pass start/end
)):
    yield from client.get_pages(since=updated_at.start_value)
```

Five rules:

1. **Server-side `updated_at`, not `created_at`** — captures backfills upstream did
2. **`initial_value` = a far-past sentinel** — but not `1970-01-01` blindly. Some APIs (GitHub) reject epoch. Use `2008-01-01` for modern SaaS
3. **`lag` matches the source's "mutation window"** — 1h OLTP, 7d marketing/CRM, 30d ad networks. This is the leakage that breaks bronze if not modeled
4. **`allow_external_schedulers=True` on production resources** — costs nothing, unlocks Airflow's date intervals
5. **`row_order="asc"` only when the source is genuinely ordered** — tempting optimization, easy to misuse on unordered sources (silently drops records)

### Backfill mode

Setting **both** `initial_value` and `end_value` on `incremental` flips the resource into backfill mode:

```python
backfill = dlt.pipeline(
    pipeline_name="vendor_backfill_2025_03",      # SEPARATE pipeline name
    destination=dlt.destinations.duckdb(WH),
    dataset_name="bronze_vendor_2025_03",         # SEPARATE dataset
)

backfill.run(vendor_source().entities.apply_hints(
    incremental=dlt.sources.incremental(
        "updated_at",
        initial_value="2025-03-01T00:00:00Z",
        end_value="2025-04-01T00:00:00Z",
    )
))
```

Key property: **backfill mode doesn't persist the cursor.** Re-running the same backfill pulls the same window — production's cursor never moves.

**Critical**: use a separate `pipeline_name` AND `dataset_name`. Sharing either with production causes cursor collisions and data confusion.

---

## Write disposition decision

Direct map from the analysis-table in [INGESTION-PLAYBOOK.md](./INGESTION-PLAYBOOK.md):

| Source shape | Disposition | Notes |
|---|---|---|
| Mutable entity, no history needed | `merge` + `primary_key` | The default. ~80% of resources |
| Mutable entity, history needed | `merge` + `primary_key` + SCD2 strategy | `write_disposition={"disposition": "merge", "strategy": "scd2"}` |
| Immutable events | `append` + cursor | No PK needed for dedup; cursor handles it |
| Small reference table | `replace` | Full reload each run |
| Append-only with explicit dedup | `append` + `primary_key` + `dedup_sort` | Within-package dedup |

### SCD2 — when and why

```python
@dlt.resource(
    primary_key="customer_id",
    write_disposition={"disposition": "merge", "strategy": "scd2"},
)
def customers(): ...
```

Effect: when a row changes, the old version's `_dlt_valid_to` gets set, a new row inserts with `_dlt_valid_to=NULL`. Query "where did Duc live on March 1?":

```sql
SELECT country FROM customers
WHERE id = 42 AND '2026-03-01' BETWEEN _dlt_valid_from AND COALESCE(_dlt_valid_to, '9999-12-31')
```

**SCD2 foot-gun**: dlt hashes all non-PK columns to detect changes. If you add a column later, the hash changes for *every existing row* → fake "change" event → spurious history rows for everybody on the next run. Lock the schema before turning on SCD2.

Use only for dimensions where history genuinely matters — customer addresses, prices, employee titles. Don't use for events (already immutable, history is built in) or rapidly-changing fields (last_login → new row every second).

---

## Idempotency

The four-layer model:

| Layer | Mechanism | Failure if missing |
|---|---|---|
| Extract | incremental cursor | re-pulls everything every run |
| Normalize | `_dlt_id` row identity | n/a — dlt generates it |
| Load | `primary_key` + `merge` | rows duplicate on re-run |
| Load (recovery) | per-job resume | failed run = full re-do |

Without a declared `primary_key`, `_dlt_id` is generated per-yield (not content-hashed). Two identical rows yielded twice → two `_dlt_id`s → both land. People often assume otherwise; declare a real PK to actually dedupe.

### When idempotency leaks (subtle)

- **`append` with PK does not dedupe.** PK is informational for append; only `merge` uses it
- **`dev_mode=True` is fake idempotency.** Each run targets a new timestamped dataset
- **Schema drift breaks "same input → same schema."** Adding columns under `evolve` mints new schema on the second run
- **Wall-clock cursors.** `incremental("updated_at")` where source emits `updated_at = NOW()` never settles

---

## Common idioms from production code

From the verified-sources survey:

| Idiom | Use when |
|---|---|
| `client.get_pages(endpoint, params)` returning a generator | Pagination + retry + rate-limit — encapsulate in `helpers/` |
| `@dlt.transformer` for parent→child relationships | When you need explicit FK linking; child gets parent's row via `data_from=...` |
| `apply_hints(write_disposition=..., schema_contract=...)` on verified sources | Override vendor source defaults without forking |
| `with_args(section="prod")` before invocation | Multi-tenant sources with separate credential sections |
| `selected=False` on helper resources | Resources used internally but not loaded to destination |
| `max_table_nesting=2` on the source | Most APIs have one level of nested objects; deeper auto-fanout creates schema sprawl |
| `add_map(lambda r: {**r, "computed_field": f(r)})` | In-flight row transformation (defaults, computed fields, PII redaction) |
| `add_filter(lambda r: r["status"] != "deleted")` | Drop rows pre-load |
| Yielding `_dlt_loads` rows as a queryable bronze table | Ingestion health as data, not as logs |

---

## Pipeline deployment shapes

Survey of real production deployments (research report 2):

| Shape | When | Notes |
|---|---|---|
| **GitHub Actions cron** | hobby/personal pipelines, simple SaaS-to-warehouse | Most common; generous free tier |
| **Dagster asset** wrapping `pipeline.run()` | mid-size analytics teams | Asset lineage benefits |
| **Airflow `PipelineTasksGroup`** | enterprise data platforms | Use `allow_external_schedulers=True` to pass dates |
| **AWS Lambda** | event-triggered, small payloads | Cold-start matters; pin dependencies |
| **`run inside Snowflake/Databricks`** | warehouse-native deployments | Newer; uses the warehouse's compute |

Anti-pattern: wrapping Airflow/Dagster around dlt and *not* using `allow_external_schedulers=True`. You end up duplicating state mechanisms — dlt's incremental cursor + Airflow's run state diverge over time.

---

## When `verified-sources` doesn't have your connector

Decision tree:

1. **Can you use `rest_api_source` (declarative)?** It's an LLM-friendly YAML-ish config that handles auth, pagination, and cursor for most REST APIs. Real-world adoption is high (~380 GitHub hits) and growing.
2. **If not, can you adapt an existing verified source?** Notion's pattern for dynamic resources, GitHub's for ETag/pagination, Stripe's for replace-vs-incremental variants — copy the closest one.
3. **If genuinely custom, follow the verified-source conventions**:
   - Transport in `helpers/`
   - `@dlt.source` returning N `@dlt.resource`s
   - Secrets as kwarg defaults
   - Cursor as kwarg default
   - One pipeline per source system

Never copy patterns from random GitHub repos — most don't match dlt-hub's conventions and you'll regret the divergence later.

---

## What dlt does NOT give you

The "no free lunch" list — things Fivetran/Airbyte handle that you do yourself in dlt:

- **Managed OAuth refresh.** Tokens expire; you wire refresh logic.
- **Scheduled schema-change probing.** dlt detects changes *during* a load, not on a 15-minute interval like Airbyte.
- **Rollback sync / re-fetch attribution window.** Express as an `incremental` cursor with `lag`, or a periodic `replace` of recent data.
- **Connector lifecycle tiers (Beta / GA).** Pin `pip` versions in `pyproject.toml`; that's your version control.
- **Sync history dashboard.** Use `pipeline.last_trace` or your orchestrator's logs.
- **Connection-broken auto-escalation.** Build your own alerting.

These are the trades for code-review-able pipelines, cheaper compute, and unlimited customization.

---

## Further reading

| Topic | File |
|---|---|
| The exercise playground itself | [../README.md](../README.md) |
| Vendor-agnostic ingestion playbook | [INGESTION-PLAYBOOK.md](./INGESTION-PLAYBOOK.md) |
| Verified-source detail survey | [research/01-dlt-verified-sources-survey.md](./research/01-dlt-verified-sources-survey.md) |
| Stated vs observed practices | [research/02-dlt-blog-and-real-world-usage.md](./research/02-dlt-blog-and-real-world-usage.md) |
| Fivetran/Airbyte/dlt comparison | [research/03-vendor-lifecycle-comparison.md](./research/03-vendor-lifecycle-comparison.md) |
| Analytics-team conventions | [research/04-analytics-team-templates.md](./research/04-analytics-team-templates.md) |
