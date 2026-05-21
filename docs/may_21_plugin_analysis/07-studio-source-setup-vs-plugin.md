# Studio `source-connection-setup` vs vibedata-data-engineering Plugin

Comparison of Studio's source-connection-setup feature against the current (med variant, v0.1.3) vibedata-data-engineering plugin's ingestion skill cluster. The question this answers: **when an FSA finishes the Studio source-connection harness and a dlt pipeline build step runs, does the plugin get everything its ingestion skills need — and does Studio surface everything those skills expect to read?**

Inputs read:

- Spec: `docs/functional/source-connection-setup/README.md`
- Design: `docs/design/source-connection-setup/README.md`, `docs/design/source-connection-setup/implementation-approach.md` (skimmed only)
- Backend: `src/server/modules/source-connections/source-connections.router.ts`, `source-connections.service.ts`, `source-connections.schemas.ts`, `helpers/connection-submit.ts`, `helpers/dlt-config-toml.ts`, `helpers/sandbox-test-runner.ts` (head), `helpers/master-secrets.ts` (head), `helpers/connector-source-cache.ts` (grep)
- Frontend: `src/features/source-connections/{api,store,schemas}.ts`, `components/SourceConnectionHarness/` (listed), `src/features/settings/components/Settings/modals/source-wizard/` (listed)
- Plugin context: `02-new-version.md`, `05-best-practice-vs-plugin-patterns.md`, `06-plugin-gaps-and-action-items.md`

Note: the spec explicitly **excludes** non-API source types (files, databases) — Fabric Data Factory / mirroring handles those. The plugin's ingestion skills are also API-shaped, so the scope match is clean.

---

## 1. Studio `source-connection-setup` overview

### End-to-end flow

```
FSA on intent UI
   │
   │  invokes /add-source harness command (chat composer intercept)
   ▼
SourceConnectionHarness modal (src/features/source-connections/components/SourceConnectionHarness/)
   │
   ├── Step 1: Connector pick (4 pivots: Home / All / Recent / Sources)
   │     GET /api/v1/source-connections/connectors        → listAllConnectors()
   │       returns CombinedConnector[]                    (source-connections.service.ts:160)
   │       — one card per (connector, entryPoint) pair
   │
   ├── Step 2: Auth method
   │     GET /api/v1/source-connections/connectors/:src/:conn/:ep/schema
   │       → loadDynamicEntryPointSchema()                (router.ts:195-234)
   │       returns authMethods[] + connector metadata
   │
   ├── Step 3: Fields
   │     - connection name (TOML section key)
   │     - destination schema (dataset_name, defaults to src_<name>)
   │     - auth field values  (Local mode: plaintext; KV mode: secret-name picker)
   │     - connector-specific non-secret config
   │
   ├── Test Connection (gate to submit)
   │     POST /api/v1/source-connections/test-connection  (router.ts:236)
   │       → preSubmitTestHandler → runSandboxTest()      (sandbox-test-runner.ts)
   │     Stages an ephemeral dir, copies connector code from cache, writes
   │     toml + secrets + pipeline.py, runs against `dummy` destination,
   │     categorises (pass | invalid_credentials | source_unreachable |
   │     connector_error | timeout | sandbox_setup_failed).
   │     Also extracts a resource-name list from a stdout sentinel (F14).
   │     Issues a testToken = sha256 over the exact input on pass.
   │
   ▼
Submit (only with matching testToken)
   POST /api/v1/source-connections/connections           (router.ts:238)
     → submitConnectionHandler → submitConnection()      (connection-submit.ts:67)
       1. Assert intent + domain + working branch
       2. Phase-A gate: domain.credentialMode === 'local' (KV mode = 501)
       3. Verify clone is on the intent branch
       4. Reject duplicate [studio.sources.<name>] on branch OR origin/main
       5. Resolve entry-point hints (credentialShape, kind) from cached schema
       6. appendConnectionToToml(.dlt/config.toml)        (dlt-config-toml.ts:143)
            → [sources.<name>.<section(s)>]              (dlt-native, dual-write fallback)
            → [sources.<name>.<section>.credentials]     (when shape=dataclass)
            → [studio.sources.<name>]                    (Studio overlay)
       7. Commit on intent branch (atomic; restore on failure)
       8. appendSecretsForConnection() →                  (master-secrets.ts)
            DATA_DIR/domains/<slug>/.dlt/secrets.toml (mode 0600, dir 0700)
       9. copyMasterSecretsIntoClone()                   (intents/helpers/...)
       10. setImmediate: runDltInit() + installConnectorRequirements()
            — fire-and-forget connector code copy into the clone, post-commit
```

### Data model

There is no per-connection DB row. The source-of-truth for a connection is the **TOML file** in the intent branch. The DB holds only:

- `connector_sources` (system-level registry, `src/server/db/schema/connector-sources.ts`)
- `data_domains.credentialMode` (`'local' | 'keyvault'`)
- standard `intents` + `domain_git_config` rows (already present)

This is a deliberate departure from any DB-backed connection state — the spec calls it out as an invariant ("No Studio-side connector registry … Connection definition lands in the intent's PR"). Plug-in invocation later is "read the committed file."

### Handoff to the plugin

The plugin enters the picture at **intent build**, after the harness commit lands. The handoff surface is purely files-on-disk inside the intent clone:

- `.dlt/config.toml` with `[sources.<name>.*]` (dlt-native) + `[studio.sources.<name>]` (Studio overlay including `connector`, `connector_source`, `entry_point`, `schema`, `auth_method`).
- `.dlt/secrets.toml` copied in from `DATA_DIR/domains/<slug>/.dlt/secrets.toml` at execution time (Local mode); never committed.
- The connector source folder under `sources/<connector>/` after `dlt init --location <cache-path>` runs (fire-and-forget on submit, or at intent build for the deferred path).

The plugin skill that consumes this is **`generating-dlt-pipeline`** (with `discovering-source-schema` running first). Neither has a Studio adapter; they assume the standard dlt OSS layout.

---

## 2. Plugin's expected contract on the source side

From `02-new-version.md` flow + `05-best-practice-vs-plugin-patterns.md` + `06-plugin-gaps-and-action-items.md`:

### What plugin skills assume about a source connection

| Skill | What it expects on disk / in inventory |
|---|---|
| `scaffolding-duckdb-workspace` / `scaffolding-fabric-workspace` | A clean workspace where `dbt debug` is green; `.dlt/config.toml` and `.dlt/secrets.toml` are present but **not edited by the skill**. |
| `discovering-source-schema` | A working connector + creds. Output: per-resource **Pipeline Inventory** rows capturing primary key, columns, write disposition, cursor field, schema_contract decision. Per plugin gap audit (P0 in `06`), it does **not** today profile server-side-vs-client-side timestamps, mutation window, cursor type, or rate limits. |
| `generating-dlt-pipeline` | Reads the Inventory + connector source code. Generates `<source>_pipeline.py` plus per-resource skeleton. Invariants: no transforms in bronze, never `tables:freeze` at generation time, `merge` + `primary_key` for mutables, `append` for events, `replace` for small reference tables. **Does not currently require** `allow_external_schedulers=True`, `row_order`, `max_table_nesting=2`, `lag`, or typed `@configspec Union` auth. |
| `pinning-dlt-schema` | Runs **after** first successful load. Writes per-resource YAML schemas + sets `tables:freeze`. |
| `running-dlt-in-duckdb-sandbox` / `running-dlt-in-fabric-sandbox` | Pure dispatcher of `dlt pipeline run` against the configured destination. Reads credentials via dlt's stock provider chain. |
| `ingestion-data-testing` | Tier 1 mandatory tests: `_dlt_id` non-null + unique on bronze tables. |

### What plugin skills assume about credentials

Patterns `05` documents:

- `dlt-secrets-in-ci-github-actions-env-never-secrets-toml` — secrets via env vars in CI; for dev, dlt's standard provider chain (env → `~/.dlt/secrets.toml` → workspace `.dlt/secrets.toml`).
- `dlt-anti-pattern-same-set-of-credentials-for-dev-and-prod` — per-env separation.
- The plugin has **no Studio-aware Key Vault provider** mentioned anywhere. KV-mode credential resolution is owned entirely by Studio's design (Phase B, design doc §"Studio-aware dlt KV provider").

### What plugin skills assume about destination scaffolding

- DuckDB workspace: `dlt-duckdb-for-dev-parquet-on-s3-for-prod`; the scaffolding skill provisions DuckDB path + dbt profile.
- Fabric workspace: scaffolding skill handles auth (401 → escalate) and Spark cold-start; assumes a single `[destination.*]` block already chosen at domain level.

The Studio design matches both — destination is per-domain, not per-connection.

---

## 3. Gap matrix

| # | Capability / concern | Studio behavior | Plugin expectation | Gap | Severity |
|---|---|---|---|---|---|
| 1 | **Incremental cursor selection** | Spec never mentions cursor; harness form has no field for it; `submitConnectionSchema` carries only auth + non-secret config; `[studio.sources.<name>]` records connector, entry_point, schema, auth_method, created_at, secrets — **no cursor metadata**. | `discovering-source-schema` builds a Pipeline Inventory row that includes cursor field, write disposition, schema_contract decision per resource. Per `06` P0/P1, the plugin would *ideally* also capture mutation window for `lag`, server-vs-client timestamp, server-side filter availability. | Studio surfaces zero cursor / incremental signal. The plugin's `discovering-source-schema` skill is the one expected to figure it out — but it must do so from the live source, with no pre-population from the harness. Workable, but the harness drops introspection state (sandbox stdout sentinel produces a resource list — see §5 — that is discarded after Test Connection completes). | high |
| 2 | **Pipeline Inventory pre-population** | Test Connection sandbox parses a stdout sentinel into a resource-name list (F14 in the spec; `parseResourceSentinel` in `sandbox-test-runner.ts`). The list is rendered as an informational pane and then **discarded** — it is not committed, not persisted, not surfaced to the agent. | Plugin's `generating-dlt-pipeline` reads the Inventory authored by `discovering-source-schema`. There is no convention that lets the plugin pick up Studio's already-discovered resource list as a hint. | The plugin re-discovers what the harness already discovered — duplicate work, and the two introspections may disagree (Studio uses the verified-sources copy from cache; plugin uses the freshly-`dlt init`-ed copy in the intent clone). | med |
| 3 | **Auth method config shape (TOML credentials placement)** | `helpers/dlt-config-toml.ts:88` decides between direct-param shape and `.credentials` sub-section based on the introspected `CredentialShape`. Falls back to dual-write when the shape isn't known (VD-2017 legacy path). | Plugin skills don't read `[studio.*]` at all — they rely on dlt's resolver finding the right shape via `[sources.<name>.<section>]`. | None on the happy path. Risk: when the introspection cache is cold or the connector schema is unknown, Studio dual-writes both shapes. dlt accepts this, but `pinning-dlt-schema` may complain about unexpected `.credentials` blocks later. | low |
| 4 | **Entry-point vs connector-folder naming** | VD-2020/2071: `[studio.sources.<name>].entry_point` records the user's Step-1 pick. The TOML writer emits one `[sources.<name>.<section>]` block keyed off `entry_point` (source kind) or `connector` (resource kind). Legacy fallback dual-writes under both. | The plugin's `discovering-source-schema` skill expects to introspect the connector module on disk; the dlt-native section name must match how the `@dlt.source` / `@dlt.resource` function resolves its config. | Mostly fine — `connection-submit.ts:316` resolves the kind from the cached schema. But Studio's cache and the plugin's `dlt init`-ed copy can drift if the upstream connector source repo moves on between the two events. | low |
| 5 | **Secret persistence — Key Vault mode** | Spec includes KV mode end-to-end (KvSecretPicker, KV references in `[studio.sources.<name>.secrets]`). Implementation **is gated off** — `connection-submit.ts:79-89` returns HTTP 501 when `domain.credentialMode !== 'local'`. Phase A ships local only; KV mode = "Phase B / Epic 10" with a Studio-aware dlt KV provider. | The plugin assumes whatever provider Studio installs into the venv resolves `dlt.secrets["sources.<name>.<field>"]` correctly. The plugin has **no awareness of KV**, by design. | Spec ↔ code divergence. Anyone reading the spec will assume KV mode works; in the code it's a hard 501. The plugin side is fine — it doesn't care which provider resolves the secret as long as the value arrives. | **high (spec divergence)** |
| 6 | **Schema discovery handoff** | Test Connection runs the source against the `dummy` destination; emits a resource list via stdout sentinel; throws the list away after rendering. | `discovering-source-schema` runs its own discovery against the live destination (DuckDB sandbox or Fabric) to populate Inventory. | Two independent discovery passes against the same source. No mechanism for Studio to seed the Inventory or for the plugin to know the harness already passed. | med |
| 7 | **Profiling handoff (server-side vs client-side timestamps, mutation window, cursor type)** | Not captured by the harness at all. | Per `06` P0: this is the single most-skipped step in the plugin too — `profiling-source-data` skill is for bronze→silver readiness, not upstream-source profiling. There is no skill that owns it. | Neither side captures this. Cross-cutting gap inherited from the plugin. | high (inherited) |
| 8 | **Schema-contract decision** | Spec never mentions `schema_contract`. The harness never asks. | Plugin pattern catalogue makes `tables:evolve, columns:freeze, data_type:freeze` the must-do default; `pinning-dlt-schema` enforces it post-first-load. | Plugin owns the decision; Studio doesn't need to surface it. No gap, but worth confirming the plugin's `generating-dlt-pipeline` always writes the contract from defaults when no Inventory hint exists. | low |
| 9 | **Write-disposition decision** | Not captured by the harness. | Plugin's `discovering-source-schema` + `generating-dlt-pipeline` own it via Inventory rows. | No gap on contract; same duplication risk as #2. | low |
| 10 | **Source-type coverage mismatch** | Spec excludes file-based and database sources (handled by Fabric Data Factory copy + Fabric mirroring). | Plugin skills assume API sources, but `dlt-patterns.md` covers SQL/file ingestion patterns too. | Studio simply doesn't expose those source types through this surface. Documented out-of-scope. | low |
| 11 | **Connector source registry (multi-repo)** | `connectorSources` DB table holds the system-level list; `dlt-verified` seeded as official. Harness lists union across all registered repos; Test Connection sandbox pulls from the cache. | Plugin's `generating-dlt-pipeline` and `dlt init --location` accept any verified-sources-shaped repo URL. | No gap; aligned. | — |
| 12 | **Connector-code lifecycle** | At submit: `setImmediate` → `runDltInit` + `installConnectorRequirements` into the intent clone, fire-and-forget. | Plugin expects `sources/<connector>/__init__.py` to exist when its scaffolding skill runs. | If the fire-and-forget init silently fails, the plugin scaffolding will see a missing connector and surface a generic error. The submit response does not wait for or surface init result. | med |
| 13 | **Error-surface mismatch (Test Connection categories)** | Studio categorises: `pass`, `invalid_credentials`, `source_unreachable`, `connector_error`, `timeout`, `sandbox_setup_failed`. Spec F9-F12 maps these to user-facing messages. | Plugin skills use generic dlt errors when their own runs fail; no convention that mirrors Studio's category set. | None on the harness; an agent re-running the same source later will surface dlt's raw error, not Studio's category — minor UX inconsistency. | low |
| 14 | **Test mechanic re-use for stored connections** | `POST /domains/:domainId/connections/test-all` reads `.dlt/config.toml` on origin/main, resolves secrets from master `secrets.toml`, runs the same `runSandboxTest`. Concurrency = 4. Legacy entries without `entry_point` fall back to `conn.connector` (router.ts:167-169). | Plugin has no equivalent — its evaluating-dlt-pipeline skill audits the pipeline file, not credentials liveness. | Studio owns liveness; plugin doesn't claim it. Aligned. | — |
| 15 | **Resource-list extraction failure (F14)** | Non-blocking warning; submit stays enabled. Resource list itself isn't persisted regardless. | n/a — plugin re-discovers anyway. | Aligns. | — |
| 16 | **Connection identity** | TOML section name = connection name (spec invariant). Phase-A enforced unique on the branch AND on origin/main (`ensureNoDuplicateName`). | dlt-native, plugin happy with this. | None. | — |
| 17 | **Phase-A gate visibility** | The 501 KV gate is a runtime check at submit time, not a feature flag the frontend reads. Frontend offers the KV picker if the schema says so. | n/a | Internal — but means an FSA in a KV-mode domain can fill the form and only hit the 501 on submit. Quality-of-life issue, not a plugin-side gap. | med |

---

## 4. Cross-cutting issues

### 4.1 Secret passthrough

Local mode is clean: values flow form → server → master `secrets.toml` (0600) → copy into clone at runtime → dlt's standard provider chain → plugin reads via `dlt.secrets.value`. No plugin awareness needed.

KV mode is **specified but not implemented** (`connection-submit.ts:79-89` rejects with 501). The design references a "Studio-aware dlt KV provider (Python) — its contract, where it sits in dlt's provider chain, and how it maps `dlt.secrets[...]` to operator-picked KV secret names via the overlay" but that provider is not on disk under `src/server/modules/source-connections/` or in any plugin reference. Anyone implementing KV mode will need to ship that provider with the plugin venv. **The plugin does not currently include such a provider.**

### 4.2 Source-type coverage mismatch

Studio explicitly excludes file-based and database sources from this flow. The plugin's `dlt-patterns.md` includes SQL/file ingestion patterns, but the corresponding skills (`generating-dlt-pipeline`) still assume the inventory drives the resource generation. As long as the Studio flow only produces API-source connections, the boundary is clean. If Studio later extends to file/DB through this same harness, the plugin's API-shaped invariants will need re-examination.

### 4.3 Incremental config handover

There is **no handover at all** for incremental config. The harness captures connector identity, auth, and non-secret config — nothing else. The plugin's `discovering-source-schema` must rediscover from scratch:

- which field to cursor on
- whether the source emits server-side or client-side timestamps
- the mutation window for `lag`
- write-disposition appropriate to the resource

Per `06` P0/P1, the plugin doesn't even capture all of that today — so there is no Studio→plugin gap *yet*, but when the plugin closes its own P0 gap (a pre-ingestion profiling skill), Studio has nowhere to put the answer. The `[studio.sources.<name>]` overlay would be the natural carrier.

### 4.4 Profiling handoff

Same shape: Studio has no slot for upstream-source profile output, and the plugin has no skill that produces it. Joint gap.

### 4.5 Error-surface mismatch

Studio's pre-submit Test Connection has a six-way result categorisation. Once the connection is committed and a plugin skill drives a real dlt run, errors come back as raw dlt exceptions through the agent's tool output. The vocabulary is different — there's no symmetry that lets an FSA say "this is the same error category the harness showed me."

### 4.6 Resource-list discard

Studio's sandbox already returns a resource list; it lights up an informational panel and disappears. A trivial improvement would be persisting it into the Studio overlay (or a sibling file) for `discovering-source-schema` to consume as a hint. The plugin would have to opt in.

### 4.7 Spec-to-code divergence flags

- **KV mode is in the spec, gated off in code.** Spec reads as if KV mode is shipped; code returns 501 (`connection-submit.ts:79`). Either the spec should mark Phase-B-only sections, or KV mode should be wired through.
- **`Domain Settings → Source Connections` page is in the spec** as a read-only viewer with Test / Test All. Backend endpoints exist (`router.ts:120-193`); frontend `DomainSourceConnectionsPage` directory exists (`src/features/sources/components/`) but **wasn't enumerated by `ls` earlier** — needs investigation to confirm it's wired up end-to-end.
- **Spec says "harness command in the intent UI" via slash entry.** That's now `/add-source` (the chat composer intercept, per commit `3270ce60`). Confirms alignment.

---

## 5. Action items

### P0

#### A1. Decide KV mode posture — close the spec/code gap

- Side: **Studio**
- File: `docs/functional/source-connection-setup/README.md` (mark KV sections as Phase B), `src/server/modules/source-connections/helpers/connection-submit.ts:79-89` (when KV ships, remove the gate and wire Epic 10's KV provider)
- What to do: Either (a) annotate the spec with `Phase A` / `Phase B` markers on every KV-mode mention so readers know the 501 is intentional, or (b) prioritise the Studio-aware dlt KV provider and ship Phase B.
- Why: The spec currently overstates capability. An FSA in a KV-mode domain hits a hard 501 only after filling the entire form. This is the clearest single divergence between Studio's own spec and its own code.

#### A2. Persist the Test Connection resource list into the Studio overlay

- Side: **Studio**
- File: `src/server/modules/source-connections/helpers/dlt-config-toml.ts` (add a `[studio.sources.<name>.discovered]` table), `helpers/connection-submit.ts` (pass the parsed sentinel through), `helpers/sandbox-test-runner.ts` (already extracts; expose via the submit pre-check)
- What to do: When Test Connection succeeds and `parseResourceSentinel` produced a list, store it under `[studio.sources.<name>.discovered]` so downstream consumers can read it without re-running discovery.
- Why: Eliminates duplicate work between Studio's Test Connection and the plugin's `discovering-source-schema`. Lays groundwork for richer pre-population (cursor field, write disposition) without changing the form.

### P1

#### A3. Add Studio→plugin Inventory bridge contract

- Side: **Both**
- Files: Studio — `src/server/modules/source-connections/helpers/dlt-config-toml.ts`; Plugin — `plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md`
- What to do: Define a stable shape for `[studio.sources.<name>.discovered]` (resources, optional cursor_hint, optional schema_contract_hint) and have `discovering-source-schema` look for it first, then fall back to live discovery. Plugin must treat the overlay as advisory, not authoritative.
- Why: Without an explicit bridge, every plugin run re-discovers what the harness already discovered, and the two answers can disagree. Also gives a future home for profiling output (`06` P0).

#### A4. Make connector init result observable instead of fire-and-forget

- Side: **Studio**
- File: `src/server/modules/source-connections/helpers/connection-submit.ts:167-176` (currently `setImmediate(...)` swallowing init failures into `logger.warn`)
- What to do: Track init status on the intent (or in the response with a follow-up endpoint) so the FSA learns within seconds if `dlt init` or `pip install` failed, rather than discovering it only when the plugin's scaffolding skill chokes on a missing `sources/<connector>/__init__.py`.
- Why: A failed background init makes the plugin's first scaffolding/run skill fail with a generic "module not found" — far from the cause. Either make the submit response carry an init job id, or queue a domain notification.

#### A5. Surface domain credential mode in the frontend before Step 1

- Side: **Studio** (frontend)
- File: `src/features/source-connections/components/SourceConnectionHarness/` (Step 1 entry)
- What to do: If the domain is in KV mode while Phase B is not shipped, block harness open with a clear banner instead of letting the FSA fill 3 steps + Test Connection.
- Why: Quality-of-life; complements A1.

### P2

#### A6. Symmetric error vocabulary between harness Test Connection and plugin dlt runs

- Side: **Both**
- File: Studio — `src/server/modules/source-connections/helpers/sandbox-test-runner.ts` (categorisation); Plugin — `plugins/vibedata-data-engineering/skills/running-dlt-in-duckdb-sandbox/SKILL.md` and `running-dlt-in-fabric-sandbox/SKILL.md`
- What to do: Document the six categories (`pass`, `invalid_credentials`, `source_unreachable`, `connector_error`, `timeout`, `sandbox_setup_failed`) in both places; have the plugin's sandbox-runner skills classify dlt exceptions into the same buckets when reporting failures.
- Why: Lets the FSA build a single mental model of "what can go wrong with this source" across the harness and the live runs.

#### A7. Cross-link `medallion-guardrails.md` from `dlt-config-toml.ts` writer

- Side: **Studio**
- File: `src/server/modules/source-connections/helpers/dlt-config-toml.ts` header comment
- What to do: Add a one-line reference to the plugin's `medallion-guardrails.md` Bronze "Must NOT" rules so the next person editing the writer sees why connection-only ≠ transform.
- Why: The writer is the entry point that defines bronze layout; current comment focuses on TOML mechanics, not bronze invariants.

#### A8. Investigate Domain Settings viewer wiring

- Side: **Studio**
- File: `src/features/sources/components/DomainSourceConnectionsPage/` (existence unverified from `ls`)
- What to do: Confirm the read-only viewer is fully wired to `GET /api/v1/source-connections/domains/:domainId/connections` and the Test / Test All buttons. **Needs investigation** — couldn't confirm in this pass.
- Why: Spec mandates it as part of the flow; broken viewer = silent regression.

---

## Notes on what I couldn't determine

- I did not read all 22 KB of `connector-source-cache.ts`, the full 23 KB of `sandbox-test-runner.ts`, or the 80 KB `docs/design/source-connection-setup/implementation-approach.md`. The action items above hold under reasonable assumptions about those files, but specifics like the exact stdout sentinel format and the dlt-venv bootstrap path are not pinned down here.
- I did not directly inspect the plugin `SKILL.md` files on GitHub; conclusions about plugin behaviour are drawn from `02-new-version.md`, `05-best-practice-vs-plugin-patterns.md`, and `06-plugin-gaps-and-action-items.md` which I authored earlier in this analysis batch.
- The `DomainSourceConnectionsPage` UI was not enumerated by my `ls` calls — flagged as "needs investigation" in A8.
- The frontend wizard step components were listed but not read line-by-line. Step-1 pivot logic and Step-3 KV picker behaviour are assumed to match the spec, not verified against `use-source-wizard.ts`.
