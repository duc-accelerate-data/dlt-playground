# Vendor Lifecycle Comparison: Fivetran vs Airbyte vs dlt

How managed-ingestion vendors frame the ingestion lifecycle, and how dlt's code-first model maps onto the same mental territory.

Sources read:
- Fivetran Sync Overview — https://fivetran.com/docs/getting-started/syncoverview (redirects to `/core-concepts/syncoverview`)
- Fivetran Sync Modes — https://fivetran.com/docs/core-concepts/sync-modes
- Fivetran Product Principles — https://fivetran.com/docs/core-concepts/product-principles
- Airbyte Connections / Sync Modes — https://docs.airbyte.com/understanding-airbyte/connections/ and https://docs.airbyte.com/using-airbyte/core-concepts/sync-modes/
- Airbyte Schema Change Management — https://docs.airbyte.com/cloud/managing-airbyte-cloud/manage-schema-changes

The canonical "Connector lifecycle" stage page Fivetran used to publish (Beta → Lite → GA → Deprecated) currently 404s on the live docs site, so the stage-naming framing below is reconstructed from references inside the Sync Overview (e.g. "Lite connectors" appearing as a tier excluded from 1-minute sync) rather than from a dedicated lifecycle page.

---

## Fivetran

### Lifecycle phases

Fivetran does not expose a unified "Connector lifecycle" page anymore. The lifecycle the user actually sees is the *run-time* lifecycle of a connection:

1. **Historical sync (initial sync)** — extract all selected tables from the source, periodically loading into the destination as data is processed.
2. **Incremental sync** — after the initial sync succeeds, only modified/added rows are extracted, using cursors recorded from prior syncs.
3. **Re-sync** — operator-triggered full re-run when data integrity is suspected.
4. **Rollback sync** — for ~25 ads/marketing connectors, a daily sync that re-fetches a window of past data because upstream APIs back-date attribution.
5. **Reimport** — auto-triggered when Fivetran cannot fetch only incremental changes (e.g. source state was lost).

The *connector-tier* lifecycle is implicit: connectors are tagged **Standard** or **Lite** (e.g. Lite connectors can't use 1-minute sync frequency), and individual connectors carry Beta / GA badges on their detail pages.

### Sync modes

Only two, named after destination behaviour, not source behaviour:

- **Soft delete mode** (default) — one source row → one destination row. Deletes flip a `_fivetran_deleted` flag.
- **History mode** — every version of a source row becomes a separate destination row (SCD2-ish). Available on selected connectors only; sometimes per-table selectable, sometimes locked on.

The extract strategy (cursor vs CDC vs full reimport) is hidden — Fivetran picks it per connector and surfaces it only as a sync *type* on the sync history chart, not as a user knob.

### Schema migrations

Hands-off by design. Fivetran auto-propagates source schema changes:
- New columns / tables appear automatically.
- Removed source columns are typically retained as nullable in the destination (consistent with the soft-delete pattern).
- Renames are usually surfaced as drop+add.
- Type changes are widened where possible.

The only user-facing schema control is the **Schema settings** page: enable/disable tables and columns, choose sync mode per table.

### Idempotency

A core product principle ("Connectors just work"): "Idempotent data loading so data is always correct." Re-runs converge — the cursor state and primary-key dedup guarantee that a re-sync produces the same destination state regardless of how many times it ran or where it was interrupted.

### Credential refresh

Fully managed. OAuth refresh tokens, key rotation reminders, and service-account credentials are handled by Fivetran's connector code. When a credential expires the connection moves to a *broken* status and Fivetran auto-escalates a support ticket (per product principles). The user re-authenticates via the dashboard.

### Knobs the user actually turns

- Sync frequency (1 min – 24 h, plan-gated).
- Sync start time / daily run time.
- Per-table enable, per-column enable.
- Sync mode (soft delete vs history) where supported.
- Destination schema name and naming overrides.

That's it. Everything else is a Fivetran decision.

---

## Airbyte

### Lifecycle phases

Airbyte's lifecycle is split across two axes:

1. **Connector certification tier** — Certified / Community / Custom. Major version upgrades have an explicit user-approved cutover (the docs call out "Major Connector Version Upgrades" with a cutoff window).
2. **Connection run lifecycle** — Discover schema → Configure streams → Sync (job) → Schema check (every 15 min Cloud / 24 h OSS) → Repeat. Jobs can also be `clear` (drop dest data, keep config) or `refresh` (re-pull all source data into dest).

### Sync modes

Airbyte names modes by `<source-read>` × `<dest-write>`:

- **Full Refresh | Overwrite**
- **Full Refresh | Append**
- **Full Refresh | Overwrite + Deduped**
- **Incremental | Append**
- **Incremental | Append + Deduped** (Airbyte's SCD2 equivalent)

Incremental supports two extraction strategies: cursor-based or CDC, exposed as a per-stream choice when the source supports both.

### Schema migrations

Explicit, user-configured. Each connection picks one of four behaviours:

- **Propagate field changes only**
- **Propagate all field and stream changes**
- **Approve all changes myself** (default-ish — detect but don't apply)
- **Stop future syncs** (pause on any change)

Non-breaking changes (new column, removed column, new stream, removed stream, type changes) flow according to that setting. **Breaking changes** — removal of a cursor or primary key — *always* pause the connection regardless of policy. There's also an opt-in **Backfill new or renamed columns** flag that re-pulls history on schema additions.

### Idempotency

Provided by the destination-write modes that include `Deduped` (uses primary key to collapse to one row per key). `Append`-only modes are *not* idempotent — re-running produces duplicates. The user explicitly chooses.

### Credential refresh

Source/destination credentials are configured per connector. OAuth-based sources auto-refresh tokens. Key rotation is a user action — Airbyte will surface auth failures as a connection error but does not auto-rotate. Self-managed deployments handle secret stores via integrations (Vault, AWS Secrets Manager) configured at the platform level.

### Knobs the user actually turns

- Per-stream sync mode (the 5-mode matrix above).
- Per-stream cursor field, primary key.
- Schema change propagation policy (4 options).
- Backfill-on-add toggle.
- Sync schedule (cron or interval).
- Major connector version upgrades (manual approval window).

---

## Cross-vendor mental model

| Concern               | Fivetran                                       | Airbyte                                                | dlt                                                  |
| --------------------- | ---------------------------------------------- | ------------------------------------------------------ | ---------------------------------------------------- |
| Sync naming axis      | By dest behaviour (soft-delete / history)      | By source × dest (`Incremental \| Append + Deduped`)   | By dest behaviour (`write_disposition`)              |
| Initial vs incremental| Implicit; engine decides                       | Explicit; "first incremental == full refresh"          | Explicit; via `dlt.sources.incremental` cursor       |
| CDC vs cursor         | Hidden                                         | Per-stream choice                                      | Source-author choice; pipeline-author sees cursor    |
| Schema additions      | Auto-propagate (no knob)                       | Policy: propagate / approve / stop                     | `schema_contract` per column/table: evolve/freeze/discard |
| Schema breaks (PK/cursor drop) | Auto-handled / re-cursor              | Always pause for review                                | `schema_contract="freeze"` raises; otherwise applied |
| Idempotency           | Promised by product principle                  | Only in `*Deduped` modes                               | Promised when `merge` or `replace` + PK              |
| Credential refresh    | Fully managed                                  | Auto-refresh OAuth; manual rotation                    | User code — config provider + `dlt.secrets`          |
| Lifecycle stages      | Beta/GA badges + Standard/Lite tiers           | Certified / Community / Custom + major-version cutover | None — sources are just Python; version is your repo|
| Operator knobs        | ~5 (frequency, table select, mode, time)       | ~6 + propagation policy                                | Unlimited; it's code                                 |

---

## dlt's place in this landscape

dlt's vocabulary maps cleanly onto the vendor mental model — it's the same lifecycle expressed as Python:

- **`write_disposition`** = Airbyte's dest-write half (`append`, `replace`, `merge` ≈ Append-Deduped).
- **`dlt.sources.incremental`** = Airbyte's "Incremental — cursor" extraction half. CDC is left to the source author.
- **`schema_contract`** = Airbyte's schema-change policy, but at finer granularity (`tables` / `columns` / `data_type`), each with `evolve` / `freeze` / `discard_value` / `discard_row`.
- **State/cursor persistence** = same idea as Fivetran's "cursors" and Airbyte's per-stream state; dlt persists state in the destination so re-runs resume cleanly.
- **Idempotency** = guaranteed when you pick `merge` + primary key, or `replace`. With `append` you get the same non-idempotent behaviour Airbyte's Append modes do.

Where dlt diverges:

- **No managed lifecycle.** There is no "Beta → GA" tier and no major-version cutover gate. The "connector" is whatever Python you import. Versioning is `pip` versioning.
- **No managed credential refresh.** dlt reads from a config provider; OAuth refresh, key rotation, and secret stores are bring-your-own.
- **No automatic schema-change detection between runs at the platform level.** dlt evolves the schema *during* a run, governed by `schema_contract`. There is no separate "discover changes every 15 minutes" probe.
- **No equivalent of Fivetran's rollback sync.** If your upstream back-dates data, you express that yourself (e.g. an `incremental` cursor with a look-back window, or a periodic `replace` of the recent window).
- **The destination write modes are sharper.** Fivetran's "soft delete" and Airbyte's "Append + Deduped" both bundle history + dedup decisions. dlt splits them: `merge` does dedup; SCD2 is its own opt-in feature.

The vendor whose framing maps best onto dlt's `write_disposition` × `schema_contract` matrix is **Airbyte**. The two-axis sync mode naming (`<source-read>` × `<dest-write>`) and the per-connection schema-propagation policy are conceptually the same product surface, just configured in YAML/UI instead of Python.

---

## Migrating from Fivetran/Airbyte to dlt — cheat sheet

| You had (Fivetran)                          | You had (Airbyte)                          | In dlt                                                                              |
| ------------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------- |
| Soft delete mode (default)                  | Incremental \| Append + Deduped            | `write_disposition="merge"` with `primary_key=...`                                  |
| History mode                                | Incremental \| Append                      | `write_disposition="append"`; for SCD2 use the SCD2 helper                          |
| Re-sync                                     | `clear` + sync, or `refresh` job           | `pipeline.run(..., write_disposition="replace")` or `pipeline.drop()` then re-run   |
| Initial sync                                | First Incremental run                      | First `pipeline.run()` — state is empty so cursor pulls everything                  |
| Cursor (Fivetran picks it)                  | Cursor field (you pick it)                 | `@dlt.resource` with `dlt.sources.incremental("updated_at")`                        |
| CDC (Fivetran picks if available)           | "Incremental — CDC" sync mode              | Source-specific (e.g. `sql_database` source supports CDC adapters)                  |
| Schema settings: enable/disable column      | Stream/field selection in UI               | `@dlt.resource(columns={...})` or `select_tables()` on the source                   |
| "Propagate field changes only"              | "Propagate field changes only"             | `schema_contract={"tables": "freeze", "columns": "evolve"}`                         |
| "Approve all changes myself"                | "Approve all changes myself"               | `schema_contract="freeze"` — fails the run; you bump schema in code and re-run      |
| "Stop future syncs"                         | "Stop future syncs"                        | `schema_contract="freeze"` at the top level                                         |
| Backfill new column                         | Backfill new or renamed columns            | `pipeline.run(..., refresh="drop_resources")` on the affected resource              |
| Sync frequency (UI slider)                  | Cron / interval schedule                   | Your scheduler (Airflow / Dagster / cron); dlt has no built-in scheduler           |
| Managed OAuth refresh                       | Auto-refresh OAuth                         | You wire token refresh into the source's auth code                                  |
| Sync history dashboard                      | Job logs UI                                | `pipeline.last_trace`, `dlt.trace` API, or your orchestrator's logs                 |
| Auto rollback sync (ads connectors)         | Stream-specific config                     | An `incremental` cursor with `initial_value` set to "now − N days" each run         |
| Connector Beta / GA tier                    | Certified / Community / Custom             | Pin the source package version in `pyproject.toml`                                  |

The net trade: you give up the managed lifecycle (credential rotation, schema-change probing, support escalation, "set and forget") and you get cheaper compute, code review on pipelines, and the ability to express anything Python can express. The mental model — extract phase × load disposition × schema contract × cursor state — is the same in all three systems. Only the surface area changes.
