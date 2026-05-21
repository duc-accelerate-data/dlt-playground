# Studio `source-connection-setup` vs vibedata-data-engineering Plugin

> **Rewritten 2026-05-21** by reading the actual plugin SKILL.md files (not prior-file summaries) and the Studio TOML writer / submit pipeline directly. Two corrections versus the previous revision:
>
> 1. **Prior claim "Plugin skills don't read `[studio.*]`" was wrong.** `plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md` frontmatter triggers on _"introspecting `[studio.sources.*]` in `.dlt/config.toml`"_. The `[studio.*]` overlay is the read-side contract; what's missing from it is a different (and narrower) gap.
> 2. **KV / Key Vault credential mode is deferred.** Studio's submit handler hard-rejects any domain whose `credentialMode !== 'local'` (`helpers/connection-submit.ts:79-89` — `501 BE901 "Phase A ships local mode only; KV mode arrives in Phase B (Epic 10)"`). All KV-shaped rows in the gap matrix below are flagged `KV mode: deferred` and re-derived only against the `local` credential path.

---

## 1. Inputs read

### Plugin SKILL.md (read raw via `gh api` against `accelerate-data/vd-data-engineering@main`)

Path prefix `plugins/vibedata-data-engineering/skills/<name>/SKILL.md`:

- `classifying-data-intents`
- `discovering-source-schema`
- `profiling-source-data`
- `generating-dlt-pipeline`
- `pinning-dlt-schema`
- `running-dlt-in-sandbox`
- `running-dlt-in-duckdb-sandbox`
- `running-dlt-in-fabric-sandbox`
- `ingestion-data-testing`
- `dlt-unit-testing`
- `documenting-dlt-pipelines`
- `evaluating-dlt-pipeline`
- `scaffolding-duckdb-workspace`
- `scaffolding-fabric-workspace`
- `validating-fixture-replay`
- `validating-golden-data`
- `managing-intent-design-docs`

### Plugin shared references

- `_shared/references/patterns/dlt-patterns.md` (118 generated patterns)
- `_shared/references/playbooks/dlt-resource-conventions.md`
- `_shared/references/playbooks/ingestion-test-tiers.md`
- `_shared/references/playbooks/medallion-guardrails.md`
- `_shared/references/playbooks/multi-session-resume.md`
- `agents/data-engineer.md` (coordinator)

### Studio source (absolute paths)

- `docs/functional/source-connection-setup/README.md`
- `docs/design/source-connection-setup/README.md` (TOML shape, harness command, schema introspection sections)
- `src/server/modules/source-connections/source-connections.router.ts`
- `src/server/modules/source-connections/source-connections.schemas.ts`
- `src/server/modules/source-connections/helpers/dlt-config-toml.ts`
- `src/server/modules/source-connections/helpers/connection-submit.ts`
- `src/server/modules/source-connections/helpers/sandbox-test-runner.ts`
- `src/server/modules/source-connections/helpers/parse-connections.ts`
- `src/server/modules/intents/helpers/copy-master-secrets.ts`
- `src/server/modules/intents/helpers/dlt-init.ts`
- `src/features/source-connections/api.ts`, `types.ts`

---

## 2. Studio `source-connection-setup` overview

### Wizard

Three-step modal (`/add-source` slash-command intercept in the chat composer):

1. **Connector pick** — `GET /api/v1/source-connections/connectors`. Returns one row per `(connector, entryPoint)` pair across all registered connector sources.
2. **Auth method** — `GET /api/v1/source-connections/connectors/:connectorSource/:connector/:entryPoint/schema` → `loadDynamicEntryPointSchema()` (`source-connections.router.ts:195-234`). Returns `authMethods[]` + connector metadata.
3. **Fields** — connection name, destination schema (defaults to `src_<connection_name>`), auth values, connector-specific non-secret config. Auth fields render plaintext (Local mode).

### API endpoints (auth-gated, `requireAuth`)

| Verb + Path | Handler | Purpose |
|---|---|---|
| `GET /connectors` | `listAllConnectors()` | Card grid feed |
| `GET /connectors/:src/:conn/:entry/schema` | `loadDynamicEntryPointSchema()` (router 195) | Step-2 + Step-3 schema |
| `POST /test-connection` | `preSubmitTestHandler` → `runSandboxTest()` | Gate-to-submit sandbox test |
| `POST /connections` | `submitConnectionHandler` → `submitConnection()` | Persist + commit |
| `GET /domains/:domainId/connections` | `readDomainConnectionsFromMain()` | Settings viewer |
| `POST /domains/:domainId/connections/:name/test` | `runSandboxTest()` | Re-test existing |
| `POST /domains/:domainId/connections/test-all` | batched re-test | Settings "Test all" |

### Data model

- `data_domains.credentialMode` (`'local' | 'keyvault'`) — Studio rejects submit for any non-`local` domain in Phase A (`connection-submit.ts:79-89`).
- `connector_sources(name PK, gitUrl, branch, ...)` — registry of dlt verified-source repos. Seeded with `dlt-verified` → `https://github.com/dlt-hub/verified-sources`.
- No DB row per *connection*. The connection identity lives only in `.dlt/config.toml` on the intent branch (Studio overlay header `[studio.sources.<name>]`).

### TOML write contract (the canonical Studio → plugin handoff)

Written by `appendConnectionToToml()` (`helpers/dlt-config-toml.ts`). For one submit, the writer appends to `<clonePath>/.dlt/config.toml`:

```toml
# dlt-native section(s) — read by dlt's TOML provider at pipeline runtime.
# Names depend on entry-point kind (VD-2071):
#   kind = 'source'    → one block under [sources.<name>.<entryPoint>]
#   kind = 'resource'  → one block under [sources.<name>.<connector>]
#   kind = undefined   → DUAL-WRITE under both (legacy fallback)
[sources.<name>.<section>]
<non-secret config key> = <value>

# Optional .credentials sub-section (VD-2041, written when credentialShape === 'dataclass'):
[sources.<name>.<section>.credentials]
<credential non-secret> = <value>     # e.g. salesforce user_name

# Studio overlay — dlt ignores; plugin discovery skill reads it.
[studio.sources.<name>]
connector = "<connector>"
connector_source = "<connectorSource>"   # registry row name (e.g. "dlt-verified")
entry_point = "<entryPoint>"             # VD-2020; optional only on legacy rows
schema = "<schema>"                      # dataset_name; default src_<name>
auth_method = "<authMethodId>"           # optional
created_at = "<ISO 8601>"
```

KV mode would additionally emit `[studio.sources.<name>.secrets]` (`dlt-config-toml.ts:129-135`). **KV mode: deferred — local credential mode only.**

### Master secrets (Local mode)

- Written by `appendSecretsForConnection()` (`helpers/master-secrets.ts`) into `DATA_DIR/domains/<slug>/.dlt/secrets.toml` (chmod 0600, never committed).
- Copied into the intent clone at submit by `copyMasterSecretsIntoClone()` (`intents/helpers/copy-master-secrets.ts:20-46`) → `<clonePath>/.dlt/secrets.toml`.

### Where the plugin enters

After submit:

1. `setImmediate()` block in `connection-submit.ts:167-176` fires `initConnectorInBackground` → `runDltInit()` materialising the connector code under `<clonePath>/<connector>/`.
2. `ensureConnectorsForIntent()` in `intents/helpers/dlt-init.ts:47` does the same idempotently at intent creation/resume, iterating every `[studio.sources.<name>]` block parsed by `parseConnectionsFromToml()`.
3. The plugin coordinator (`agents/data-engineer.md`) runs `classifying-data-intents` → `managing-intent-design-docs` → workspace scaffolder (`scaffolding-duckdb-workspace` or `scaffolding-fabric-workspace`) → ingestion ladder.

---

## 3. The contract surface — what Studio writes vs what plugin skills actually read

Quotes are verbatim from the SKILL.md frontmatter / Invariants sections.

| TOML key (written by Studio) | Skill that explicitly reads it | Proof quote |
|---|---|---|
| `[studio.sources.<name>]` block (header itself, enumeration) | `discovering-source-schema` | *"introspecting `[studio.sources.*]` in `.dlt/config.toml`, listing dlt resources/fields, or filling ingestion inventory rows"* (frontmatter description) |
| `[studio.sources.<name>]` block (presence as gate) | `scaffolding-duckdb-workspace` | *"for every `[studio.sources.<name>]` entry in `.dlt/config.toml`, the matching `[sources.<name>.<connector>]` block exists and the secret keys the connector declares are present (key presence only — do not read values). Any gap halts the scaffold; the user must complete `/add-source` and re-run."* (Invariants) |
| `[studio.sources.<name>].schema` | dlt resource conventions (consumed by `generating-dlt-pipeline`) | *"Dataset name (DuckDB schema): whatever `[studio.sources.<connection_name>].schema` declares in `.dlt/config.toml` — default `src_<connection_name>` when the overlay omits it. Read this value; never invent a schema name."* (`dlt-resource-conventions.md`) |
| `[studio.sources.<name>].connector`, `.connector_source` | (read implicitly by Studio's parser + dlt-init hook; **no skill cites them by name**) | — |
| `[studio.sources.<name>].entry_point` | (no SKILL.md mentions this key; written for Studio's own re-test path; plugin pipeline code does not need it because `@dlt.source` resolves by Python symbol) | — |
| `[studio.sources.<name>].auth_method` | (no SKILL.md mentions this key; rendering hint for Studio Settings re-pick) | — |
| `[sources.<name>.<section>]` (dlt-native non-secret block) | dlt runtime (not a skill); presence asserted by `scaffolding-duckdb-workspace` | see row 2 |
| `[sources.<name>.<section>.credentials]` non-secret members | dlt runtime, indirectly via *"Credentials resolve through dlt's stock provider chain (`.dlt/secrets.toml`, env, KV). Do not read env files or arbitrary credential keys yourself"* (`discovering-source-schema` Invariants) | quoted |

What no SKILL.md mentions (in any frontmatter or Invariants block):

- `connector_source` registry name.
- `entry_point` value.
- `auth_method` value.
- An incremental-cursor hint.
- A profiling-results hint.
- Any in-scope-resource list.

The discovery skill is expected to walk every `[studio.sources.*]` and *introspect* the connector to derive resources + fields + types. Studio writes nothing about resources, fields, or cursors into the TOML.

---

## 4. Per-skill review (ingestion cluster, 12 skills)

Order follows the data-engineer coordinator's natural flow.

### 4.1 `classifying-data-intents`
- **Entry expectation:** the user's latest request only. No TOML, no workspace.
- **Produces:** classification payload (`action`, `type`) consumed by the coordinator; commits verdict to `intent.md`.
- **Studio gap:** none. Runs before workspace touches.

### 4.2 `managing-intent-design-docs`
- **Entry:** prior `intent.md` / `design.md` if any.
- **Produces:** `intents/<slug>/intent.md`, `design.md`, `implementation-plan.md`. For ingestion intents `design.md` MUST contain a `Pipeline Inventory` section (per `agents/data-engineer.md`).
- **Studio gap:** Studio submits no row template into Pipeline Inventory. The agent has to materialize rows from scratch by re-running discovery for every `[studio.sources.*]` block, even though Studio already enumerated connectors + auth methods + connection names at submit.

### 4.3 `scaffolding-duckdb-workspace` (or fabric variant)
- **Entry:** `vd-domain.yml`, `.dlt/config.toml`, `.dlt/secrets.toml`. SKILL.md Invariants: *"Never write or modify `.dlt/config.toml` or `.dlt/secrets.toml`. They are produced upstream by Studio's `/add-source` flow and are read-only inputs here."*
- **Gate quoted in §3 row 2.**
- **Studio gap (caught by direct read):** the scaffold gate looks for `[sources.<name>.<connector>]` — but VD-2071 writes the section under EITHER `<connector>` OR `<entryPoint>` depending on entry-point kind (`dlt-config-toml.ts:60-70`). For `kind = 'source'` with `entryPoint !== connector` (e.g. `github_reactions` entry point under the `github` folder), the gate's literal-string check could miss a valid block. SKILL wording does not handle the `<section>` axis VD-2071 introduced.

### 4.4 `discovering-source-schema`
- **Entry:** enumerates every `[studio.sources.*]` in `.dlt/config.toml` and imports the connector's verified-source module to introspect resources.
- **Produces:** Pipeline Inventory rows with *"target table name, write disposition, incremental cursor, and a draft `schema_contract`"* (Invariants).
- **Error contract:** `OBJECT_NOT_FOUND` on import failure, `SOURCE_AUTH_FAIL` on auth failure. SKILL.md is emphatic: *"Credentials resolve through dlt's stock provider chain (`.dlt/secrets.toml`, env, KV). Do not read env files or arbitrary credential keys yourself."*
- **Studio gap:** Studio's submit-time sandbox test **already discovers** resources (`SandboxRunResult.resources?`, `sandbox-test-runner.ts:84-94`). That list is not persisted into the TOML overlay; the discovery skill re-introspects from scratch. Studio also writes no cursor or write-disposition hint, but the SKILL invariant requires the Inventory row to carry one — the agent must invent within the patterns guidance in `dlt-resource-conventions.md`.

### 4.5 `pinning-dlt-schema`
- **Entry:** approved Pipeline Inventory rows.
- **Produces:** `schema_contract` on each resource skeleton (`evolve|freeze|discard_value|discard_row` × 3 axes). Must not write `"tables": "freeze"` at pin time.
- **Studio gap:** none — schema_contract is a downstream decision.

### 4.6 `generating-dlt-pipeline`
- **Entry:** pinned Inventory rows + `dlt-resource-conventions.md` (which reads `[studio.sources.<name>].schema` for the dataset name — see §3 row 3).
- **Hard invariants:** *"Do not author a custom `@dlt.source` wrapper for a verified source. Do not create per-resource `dlt/<object>.py` files when the verified source already defines them."* and *"Do not commit the pipeline file without a successful dry-run first."*
- **Studio gap:** the conventions playbook names `pipeline_name = <connection_name>_bronze`. Studio's connection_name is the TOML section subkey, so this lines up. But: the skill assumes a *single* `dlt.pipeline(...)` per workspace; Studio supports N connections per domain → N pipelines per intent. There is no skill guidance for the multi-connection case, and `dlt-patterns.md` flags *"anti-pattern-running-two-pipelines-with-the-same-name-working-dir-in-parallel"* without resolving it.

### 4.7 `running-dlt-in-sandbox` (dispatcher)
- **Entry:** `vd-domain.yml` `destination.type`. Dispatches to duckdb or fabric child.
- **Studio gap:** Studio populates `vd-domain.yml` at domain create time; aligned.

### 4.8 `running-dlt-in-duckdb-sandbox`
- **Entry expectation:** `.dlt/secrets.toml` already populated. SKILL: *"confirm `.dlt/secrets.toml` is populated for the source. Do not edit it yourself — re-run `/add-source` if the keys are missing."*
- **Studio guarantees this via `copyMasterSecretsIntoClone()`.** Aligned.

### 4.9 `running-dlt-in-fabric-sandbox`
- **Entry expectation:** harness pre-hook injects `FAB_TOKEN*`, `VD_STUDIO_USER_ID`, `EPHEMERAL_*` env vars. SKILL: *"Never inspect or set `FAB_TOKEN*` / `VD_STUDIO_USER_ID`. They are injected at command time by the harness pre-hook."*
- **Studio gap:** not verified in this rewrite (Fabric harness pairing belongs to KV phase). Flagged as follow-up.

### 4.10 `dlt-unit-testing`
- **Entry:** approved resource Python; mocks the connector.
- **Studio gap:** none direct.

### 4.11 `ingestion-data-testing`
- **Entry:** landed bronze tables in the configured warehouse.
- **Invariant:** Tier 1 = `_dlt_id` non-null + unique on every bronze table; always included.
- **Studio gap:** none — tier selection is the agent's call.

### 4.12 `documenting-dlt-pipelines` / `evaluating-dlt-pipeline`
- **Entry:** generated artifacts.
- **Studio gap:** none.

---

## 5. Gap matrix (local credential mode)

Severity: **B(locker)** = pipeline build halts or wrong output; **F(unctional)** = manual workaround needed; **N(it)** = avoidable duplicate work.

| # | Capability | Studio behavior | Plugin skill expectation | Gap | Severity |
|---|---|---|---|---|---|
| 1 | Connection enumeration | Writes `[studio.sources.<name>]` overlay per submit (`dlt-config-toml.ts:111`) | `discovering-source-schema` introspects every `[studio.sources.*]` (frontmatter, §3) | None — contract honored | — |
| 2 | Destination schema (dataset_name) | Writes `schema = "..."` under overlay (`dlt-config-toml.ts:123`) | `dlt-resource-conventions.md` mandates reading this verbatim | None — explicit read | — |
| 3 | Connector module path | Writes `connector`, `connector_source` | No SKILL cites these by name; Studio's own `parseConnectionsFromToml` + `dlt-init.ts` consume them | None — Studio's harness is the consumer | — |
| 4 | Entry-point identity | Writes `entry_point` (VD-2020) | No SKILL.md reads `entry_point`; dlt resolves by Python symbol at runtime | None for plugin; Studio keeps it for re-test path | — |
| 5 | Section header axis (`<connector>` vs `<entryPoint>`) | VD-2071 writes ONE section per `kind`; legacy callers dual-write | `scaffolding-duckdb-workspace` invariant only checks literal `[sources.<name>.<connector>]` | Scaffold gate may mis-report missing block when `kind='source'` writes under `<entryPoint>` ≠ `<connector>` | **F** |
| 6 | Credentials sub-section | VD-2041 emits `[sources.<name>.<section>.credentials]` only for `credentialShape='dataclass'`; legacy dual-write otherwise | dlt runtime resolves via stock provider chain; no SKILL cares about the shape axis | None for plugin | — |
| 7 | Secret values | Local: master `secrets.toml` written then copied into clone (`copy-master-secrets.ts`) | `running-dlt-in-duckdb-sandbox` requires `.dlt/secrets.toml` populated | None — covered | — |
| 8 | Discovered-resource list reuse | `runSandboxTest` returns `resources?: string[]` (`sandbox-test-runner.ts:84-94`) but Studio does NOT persist it | `discovering-source-schema` re-introspects from scratch every time | Duplicate work: same resource list discovered twice; first list is thrown away | **N** |
| 9 | Pipeline Inventory seeding | Studio does not seed any Inventory row stub | `managing-intent-design-docs` requires Inventory rows before `discovering-source-schema` can fill them | Agent has to bootstrap rows from raw TOML on every fresh intent | **N** |
| 10 | Incremental cursor declaration | None — wizard has no cursor field | SKILL Invariant requires every Inventory row carry `incremental cursor` | Agent must derive cursor from connector metadata / source docs | **F** |
| 11 | Write disposition default | None | Inventory row must carry write_disposition | Agent picks per resource (per `dlt-resource-conventions.md` defaults) | **F** |
| 12 | Schema contract default | None | `pinning-dlt-schema` must commit a value (never `TBD`) | Agent picks; aligned | — |
| 13 | Test-Connection verdict surfaced to skill | Submit-gate sandbox produces `category`, `message`, `resources`, `resourcesError`; only `category=pass` allows submit | Discovery skill's halt vocabulary is `OBJECT_NOT_FOUND` / `SOURCE_AUTH_FAIL` — disjoint from Studio's category enum | No deterministic translation between Studio re-test failure and SKILL error code | **N** |
| 14 | Multi-connection pipeline strategy | N connections → N entries in TOML; no convention written | `generating-dlt-pipeline` assumes single-pipeline workspace; `dlt-patterns.md` warns against same-name parallel runs | No Studio or skill guidance on workspace layout for N connections | **F** |
| 15 | KV mode end-to-end | — | — | **KV mode: deferred — local credential mode only** | — |
| 16 | KV secret-name mapping (`[studio.sources.<name>.secrets]`) | — | — | **KV mode: deferred — local credential mode only** | — |
| 17 | KV reachability gate | — | — | **KV mode: deferred — local credential mode only** | — |
| 18 | Bronze-adequacy handoff | — | `profiling-source-data` runs AFTER bronze lands, not against Studio's pre-landing introspection | None — handoff path is filesystem, not TOML | — |
| 19 | Fabric harness env injection | Not verified in this rewrite | `running-dlt-in-fabric-sandbox` requires `FAB_TOKEN*` injected by harness pre-hook | Follow-up — Fabric pairing belongs with Phase B | — |
| 20 | Connector source registry → skill awareness | `connector_sources` table in Studio DB; not visible to plugin | Skills assume the connector is `dlt init`'d already; Studio's `dlt-init.ts` enforces this | None — handover via filesystem | — |

---

## 6. Cross-cutting issues (local mode only)

### Secret passthrough
Local mode is clean. The master file is the source of truth; `copyMasterSecretsIntoClone()` is idempotent and chmod-tight. The skill invariant *"Do not read env files or arbitrary credential keys yourself"* is honored because the plugin reads via `dlt.secrets.value` resolution, never directly. **No gap.**

### Source-type coverage
Studio's functional spec scopes to API connectors; files / databases route through Fabric Data Factory. The plugin's ingestion cluster is API-shaped (dlt verified sources). Match is clean.

### Incremental config handover
Studio captures none of: cursor field, cursor start value, write disposition. The plugin SKILL invariant requires all three on every Inventory row. Severity **F** — covered by the agent re-deriving from connector docs, but it is repeated work per intent.

### Profiling handoff
`profiling-source-data` is a transformation-side skill; runs after bronze lands, against landed tables, not against Studio's pre-landing introspection. No handoff exists, none is needed.

### Error-surface mismatch
- Studio's `SandboxResultCategory` enum: `pass | invalid_credentials | source_unreachable | connector_error | timeout | sandbox_setup_failed`.
- `discovering-source-schema` error vocabulary: `OBJECT_NOT_FOUND` (import fail), `SOURCE_AUTH_FAIL` (auth fail).
These are disjoint label spaces for the same underlying failure modes. The agent cannot deterministically translate a Studio re-test failure into a SKILL error code without a mapping table.

---

## 7. Action items

Priority: **P1** = blocks a green path; **P2** = removes duplicate work; **P3** = polish.

### P1 — Fix scaffold gate for VD-2071 section axis
- **Side:** plugin
- **File / skill:** `plugins/vibedata-data-engineering/skills/scaffolding-duckdb-workspace/SKILL.md` (and fabric sibling)
- **What:** loosen the gate to accept either `[sources.<name>.<connector>]` OR `[sources.<name>.<entryPoint>]`. Or: parse the overlay's `entry_point` and check exactly the section Studio wrote.
- **Why:** Studio's `sectionsForWrite()` (`dlt-config-toml.ts:60-70`) emits one section per `kind`; the literal-`<connector>` check in SKILL Invariants assumes legacy dual-write. With `kind='source'` and `entryPoint !== connector`, a valid connection will fail the gate.

### P2 — Persist sandbox-test resource list into `[studio.sources.<name>]`
- **Side:** Studio
- **File:** `src/server/modules/source-connections/helpers/dlt-config-toml.ts` (writer); `helpers/sandbox-test-runner.ts` (already produces the data)
- **What:** add `discovered_resources = ["…", "…"]` to the overlay when the sandbox test returned them.
- **Why:** `discovering-source-schema` SKILL.md frontmatter explicitly walks every `[studio.sources.*]` and produces resource rows. The list is already discovered at submit and discarded (`SandboxRunResult.resources?`, `sandbox-test-runner.ts:84-94`). Persisting it lets the discovery skill skip a full re-introspection.

### P2 — Pre-seed Pipeline Inventory stub at intent-create time
- **Side:** both
- **File / skill:** Studio's `intents/helpers/dlt-init.ts` could emit a stub; `managing-intent-design-docs` SKILL.md procedure step 4 ("Write bite-sized steps") could read the stub.
- **What:** when `ensureConnectorsForIntent()` runs, append a placeholder Pipeline Inventory row per connection (`name`, `schema`, `connector`, `entry_point`) into `design.md` if it exists.
- **Why:** the data-engineer agent (`agents/data-engineer.md`) requires `design.md` to have a `Pipeline Inventory` section before any build phase. Studio knows the connections at intent creation; the agent re-discovers them on first ingestion step.

### P3 — Document multi-connection workspace layout
- **Side:** plugin
- **File:** `_shared/references/playbooks/dlt-resource-conventions.md`
- **What:** add a "Multi-connection workspaces" subsection: one `dlt.pipeline()` per `connection_name`, distinct `pipeline_name`, shared `pipelines_dir`, naming convention `<connection>_bronze`.
- **Why:** `dlt-patterns.md` flags the same-name parallel-run anti-pattern but never reconciles it with Studio's N-connection-per-domain model.

### P3 — Cursor + write-disposition discovery hint (optional)
- **Side:** Studio
- **File:** `helpers/dlt-config-toml.ts`
- **What:** allow the writer to record agent-supplied cursor field + write disposition once the discovery skill picks them, e.g. `[studio.sources.<name>.discovered]`.
- **Why:** lets the next session resume `discovering-source-schema` without redoing inference. Gain is small unless N connections is large; the multi-session-resume playbook already covers basic resume via Inventory Status flips.

### P3 — Error-code mapping table
- **Side:** both
- **File:** Studio's `source-connections.types.ts`; plugin's `discovering-source-schema/SKILL.md` Invariants
- **What:** publish a one-way mapping `SandboxResultCategory` → SKILL error code (`invalid_credentials` → `SOURCE_AUTH_FAIL`; `connector_error` → `OBJECT_NOT_FOUND`; etc.).
- **Why:** makes the re-test surface (`POST /domains/.../connections/:name/test`) actionable inside the discovery skill's halt conditions.

### Follow-up — Verify Fabric harness env injection
- **Side:** Studio
- **What:** confirm intent harness pre-hook for OpenHands runs in Fabric domains injects `FAB_TOKEN*`, `VD_STUDIO_USER_ID`, `EPHEMERAL_*` as `running-dlt-in-fabric-sandbox/SKILL.md` requires.
- **Why:** not verified by this read; KV mode + Fabric are paired in Phase B (Epic 10).

---

## 8. Honest uncertainty

- The `entry_point` key in `[studio.sources.<name>]` is **not mentioned by any SKILL.md** I read. Studio's writer comment (`dlt-config-toml.ts:114-118`) claims it "drives downstream consumers — sandbox-test-runner re-tests, the discovering-source-schema and generating-dlt-pipeline skills". I could not find this read in either skill's frontmatter or Invariants. It is plausible the discovery skill *does* read it (it has to know which `@dlt.source` to import) but the SKILL.md does not say so.
- The `auth_method` key is similarly unreferenced by any SKILL.md — it appears to be a display hint for Studio's Settings viewer "re-pick" path (per the VD-1886 comment in `dlt-config-toml.ts:100`), not a pipeline runtime input.
- I did not read every action-item-relevant file end-to-end (e.g. `master-secrets.ts` was only partially examined; `sandbox-test-runner.ts` only the first 200 lines). Conclusions about secret-file behavior rely on `copy-master-secrets.ts` and SKILL invariants, not a full audit of the writer.
- The plugin version on `main` may have advanced since this read; tag/commit hash was not pinned.
