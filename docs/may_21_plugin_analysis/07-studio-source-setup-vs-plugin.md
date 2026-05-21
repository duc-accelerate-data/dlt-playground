# Studio's Source-Connection Setup vs the Data-Engineering Toolkit

> **Rewritten on 2026-05-21** by reading the toolkit's actual instruction files (not earlier summaries) and Studio's config writer and submit pipeline directly. Two corrections versus the previous draft:
>
> 1. **The earlier claim that the toolkit's tasks "don't read Studio's overlay section" was wrong.** The task that discovers a source's schema explicitly describes itself as introspecting the section that Studio writes into the configuration file (`[studio.sources.*]` in `.dlt/config.toml`). That section is the agreed handoff point between Studio and the toolkit — Studio writes it, the toolkit reads it. The actual gap is different (and narrower).
> 2. **Credential storage in a secrets vault is deferred.** Studio's submit handler hard-rejects any domain that isn't on the "local credentials" mode (the relevant file is `helpers/connection-submit.ts`, lines 79–89; it returns a 501 with the message "Phase A ships local mode only; the vault mode arrives later"). Every vault-mode row in the gap matrix below is marked **deferred** and the analysis only covers the local credential path.

---

## 1. What this analysis reads

### From the toolkit's instruction files

Pulled raw via the GitHub API against the toolkit's main branch. The files are inside `plugins/vibedata-data-engineering/skills/<name>/SKILL.md`. The tasks read:

- Classifying the user's request
- Discovering a source's schema
- Profiling a source's data
- Generating a dlt pipeline
- Pinning the dlt schema
- Running dlt in a sandbox (dispatcher and DuckDB/Fabric runners)
- Running ingestion data tests
- Running dlt unit tests
- Documenting dlt pipelines
- Evaluating a dlt pipeline
- Setting up DuckDB and Fabric workspaces
- Validating fixture replay and golden data
- Managing intent design docs

### From the toolkit's shared folder

- The dlt patterns catalogue (118 entries).
- Three playbooks: dlt resource conventions, ingestion test tiers, medallion guardrails.
- The multi-session resume playbook.
- The coordinator's instructions (`agents/data-engineer.md`).

### From the Studio codebase

The relevant Studio files (absolute paths shown for engineers who need to act on them):

- The functional spec (`docs/functional/source-connection-setup/README.md`).
- The design doc (`docs/design/source-connection-setup/README.md`).
- The router (`src/server/modules/source-connections/source-connections.router.ts`).
- The schemas (`source-connections.schemas.ts`).
- The config-file writer (`helpers/dlt-config-toml.ts`).
- The submit handler (`helpers/connection-submit.ts`).
- The sandbox test runner (`helpers/sandbox-test-runner.ts`).
- The TOML parser (`helpers/parse-connections.ts`).
- The master-secrets copy helper (`intents/helpers/copy-master-secrets.ts`).
- The dlt-init helper (`intents/helpers/dlt-init.ts`).
- Frontend API and types under `src/features/source-connections/`.

---

## 2. What Studio's source-connection setup does

### The wizard

A three-step modal opened from the chat composer (the user types `/add-source`):

1. **Pick a connector.** The frontend calls a "list connectors" endpoint, which returns one row per connector-and-entry-point combination across all registered sources.
2. **Pick an authentication method.** The frontend calls a schema endpoint that returns the available auth methods and the connector's metadata.
3. **Fill in the fields.** Connection name, destination schema (defaults to a `src_<connection_name>` prefix), auth values, and connector-specific non-secret config. In local credential mode, auth fields render as plain text.

### The API endpoints (all behind authentication)

| Verb + path | What it does |
|---|---|
| `GET /connectors` | The card grid feed for the first step. |
| `GET /connectors/:src/:conn/:entry/schema` | Returns the schema and auth methods for steps two and three. |
| `POST /test-connection` | A pre-submit sandbox test. The submit button is gated on this passing. |
| `POST /connections` | Persists the connection and commits it. |
| `GET /domains/:domainId/connections` | Lists connections for the settings viewer. |
| `POST /domains/:domainId/connections/:name/test` | Re-tests an existing connection. |
| `POST /domains/:domainId/connections/test-all` | "Test all" in settings. |

### The data model

- Every domain row has a credential mode: either `local` or `keyvault`. Studio refuses to submit anything in vault mode in this phase.
- The connector registry table holds one row per supported source repo. It is seeded with the dlt verified-sources repo.
- **There is no database row per individual connection.** A connection's identity lives only in the dlt config file on the intent branch — specifically, in the Studio-written section header.

### The config-file handoff (the canonical Studio-to-toolkit contract)

When the user submits, the config-writer appends to the intent clone's dlt config file. The shape it appends:

```toml
# Sections dlt itself reads at pipeline runtime.
# Which section gets written depends on the connector kind:
#   kind = 'source'    → one block under [sources.<name>.<entryPoint>]
#   kind = 'resource'  → one block under [sources.<name>.<connector>]
#   kind = undefined   → dual-write under both (legacy fallback)
[sources.<name>.<section>]
<non-secret config key> = <value>

# Optional credentials sub-section, written only when the connector exposes
# a dataclass-shaped credential set (e.g. Salesforce user_name):
[sources.<name>.<section>.credentials]
<credential non-secret> = <value>

# The Studio overlay section — dlt ignores it; the toolkit's discovery task reads it.
[studio.sources.<name>]
connector = "<connector>"
connector_source = "<connectorSource>"   # the registry row name, e.g. "dlt-verified"
entry_point = "<entryPoint>"             # optional only on legacy rows
schema = "<schema>"                      # dataset_name; default src_<name>
auth_method = "<authMethodId>"           # optional
created_at = "<ISO 8601>"
```

In vault mode the writer would also emit a `[studio.sources.<name>.secrets]` block. **Vault mode is deferred** — this analysis is local mode only.

### Master secrets (local mode)

- The master secrets writer appends each connection's secrets to a domain-scoped secrets file (mode 0600, never committed to git).
- At submit time, the master-secrets copy helper copies that file into the intent clone, where dlt reads it at runtime.

### Where the toolkit enters the picture

After submit:

1. The submit handler fires a deferred call to a background helper that materialises the connector code under the intent clone.
2. An idempotent helper repeats the same materialisation at intent creation or resume, iterating every Studio overlay block it finds in the config file.
3. The toolkit's coordinator runs through: classify the user's request → manage design docs → set up the workspace (DuckDB or Fabric) → walk the ingestion steps.

---

## 3. The handoff — what Studio writes vs what the toolkit's tasks actually read

Quotes are verbatim from each task's description or invariants.

| Config key written by Studio | Task that reads it explicitly | Proof quote |
|---|---|---|
| The Studio overlay block (header and enumeration) | The schema-discovery task | *"introspecting `[studio.sources.*]` in `.dlt/config.toml`, listing dlt resources/fields, or filling ingestion inventory rows"* (description) |
| The Studio overlay block (as a gate) | The DuckDB workspace setup task | *"for every `[studio.sources.<name>]` entry in `.dlt/config.toml`, the matching `[sources.<name>.<connector>]` block exists and the secret keys the connector declares are present (key presence only — do not read values). Any gap halts the scaffold; the user must complete `/add-source` and re-run."* (invariants) |
| The schema (dataset name) field on the overlay | The resource-conventions playbook (used by pipeline generation) | *"Dataset name (DuckDB schema): whatever `[studio.sources.<connection_name>].schema` declares in `.dlt/config.toml` — default `src_<connection_name>` when the overlay omits it. Read this value; never invent a schema name."* |
| The connector and connector_source fields | Read by Studio's own parser and dlt-init helper. **No task cites them by name.** | — |
| The entry_point field | **No task mentions this key.** Studio keeps it for its own re-test path; the toolkit's pipeline code doesn't need it because dlt resolves resources by Python symbol. | — |
| The auth_method field | **No task mentions this key.** A display hint for Studio's settings viewer "re-pick" path. | — |
| The dlt-native non-secret block | Read by dlt at runtime, not by any task; the workspace-setup task asserts its presence (see row 2). | — |
| The non-secret members of the credentials sub-section | Read by dlt at runtime, indirectly. The schema-discovery task's invariant says: *"Credentials resolve through dlt's stock provider chain (.dlt/secrets.toml, env, KV). Do not read env files or arbitrary credential keys yourself."* | — |

What no task mentions anywhere in its description or invariants:

- The connector-source registry name.
- The entry-point value.
- The auth-method value.
- Any incremental-cursor hint.
- Any profiling-results hint.
- Any in-scope resource list.

The schema-discovery task is expected to walk every Studio overlay block in the config file and introspect the connector code to derive resources, fields, and types. Studio writes nothing about resources, fields, or cursors into the config file.

---

## 4. Per-task review (the ingestion cluster — 12 tasks)

The order follows the coordinator's natural flow.

### 4.1 Classify the user's request
- **What it needs:** just the user's latest request. No config file, no workspace.
- **What it produces:** a classification payload that the coordinator consumes, plus a verdict committed to the intent's notes.
- **Studio gap:** none. Runs before anything touches the workspace.

### 4.2 Manage intent design docs
- **What it needs:** any prior intent or design notes.
- **What it produces:** the intent notes, the design doc, and the step-by-step plan. For ingestion intents, the design doc must contain a section literally titled "Pipeline Inventory".
- **Studio gap:** Studio doesn't submit any row template into the Pipeline Inventory. The assistant has to materialise rows from scratch by re-running schema discovery for every overlay block — even though Studio already enumerated the connectors, auth methods, and connection names at submit.

### 4.3 Set up a DuckDB workspace (or the Fabric variant)
- **What it needs:** the domain configuration file and the dlt config and secrets files. Its invariants say: *"Never write or modify `.dlt/config.toml` or `.dlt/secrets.toml`. They are produced upstream by Studio's `/add-source` flow and are read-only inputs here."*
- **Its gate is quoted in section 3, row 2.**
- **Studio gap (caught by direct read):** the gate looks for `[sources.<name>.<connector>]` — but Studio's writer puts the section under EITHER the connector name OR the entry-point name depending on the connector kind (the file is `dlt-config-toml.ts`, lines 60–70). For a source-kind connector whose entry point differs from the connector folder name (a real example is `github_reactions` under the `github` folder), the literal-string check could miss a valid block. The task's wording doesn't handle this axis.

### 4.4 Discover a source's schema
- **What it needs:** it enumerates every Studio overlay block in the config file and imports the connector's Python module to introspect its resources.
- **What it produces:** Pipeline Inventory rows with target table name, write disposition, incremental cursor, and a draft schema contract.
- **Error contract:** named errors for import failure and auth failure. The instruction file is emphatic: *"Credentials resolve through dlt's stock provider chain (.dlt/secrets.toml, env, KV). Do not read env files or arbitrary credential keys yourself."*
- **Studio gap:** Studio's submit-time sandbox test **already discovers** the resource list. That list is not persisted into the overlay; the discovery task re-introspects from scratch. Studio also writes no cursor or write-disposition hint, but the task requires the inventory row to carry one — the assistant has to invent within the patterns guidance.

### 4.5 Pin the dlt schema
- **What it needs:** approved Pipeline Inventory rows.
- **What it produces:** a schema contract on each resource skeleton across three axes. Must not freeze tables at pin time.
- **Studio gap:** none — the schema contract is a downstream decision.

### 4.6 Generate the dlt pipeline
- **What it needs:** the pinned inventory rows plus the resource-conventions playbook (which reads the schema field from Studio's overlay for the dataset name — see section 3 row 3).
- **Hard rules:** *"Do not author a custom `@dlt.source` wrapper for a verified source. Do not create per-resource `dlt/<object>.py` files when the verified source already defines them."* And: *"Do not commit the pipeline file without a successful dry-run first."*
- **Studio gap:** the conventions playbook names the pipeline as `<connection_name>_bronze`. Studio's connection name *is* the section subkey, so this lines up. But: the task assumes a *single* `dlt.pipeline(...)` per workspace. Studio supports N connections per domain, which means N pipelines per intent. There is no guidance for the multi-connection case, and the patterns catalogue flags the "two pipelines with the same name running in parallel" anti-pattern without resolving it.

### 4.7 Run dlt in a sandbox (dispatcher)
- **What it needs:** the domain configuration's destination type. Dispatches to the DuckDB or Fabric child.
- **Studio gap:** Studio populates the domain configuration at domain-create time; aligned.

### 4.8 Run dlt in the DuckDB sandbox
- **What it needs:** a populated secrets file. The task says: *"confirm `.dlt/secrets.toml` is populated for the source. Do not edit it yourself — re-run `/add-source` if the keys are missing."*
- **Studio guarantees this via its master-secrets copy helper.** Aligned.

### 4.9 Run dlt in the Fabric sandbox
- **What it needs:** the harness pre-hook to inject Fabric tokens, the Studio user ID, and ephemeral lakehouse env vars. The task says: *"Never inspect or set `FAB_TOKEN*` / `VD_STUDIO_USER_ID`. They are injected at command time by the harness pre-hook."*
- **Studio gap:** not verified in this rewrite (the Fabric harness pairing belongs to the vault-credentials phase). Flagged as follow-up.

### 4.10 Write dlt unit tests
- **What it needs:** approved resource Python; mocks the connector.
- **Studio gap:** none direct.

### 4.11 Run ingestion data tests
- **What it needs:** landed bronze tables in the configured warehouse.
- **Hard rule:** Tier 1 (synthetic dlt row-ID present and unique on every bronze table) is always included.
- **Studio gap:** none — tier selection is the assistant's call.

### 4.12 Document and evaluate dlt pipelines
- **What it needs:** generated artefacts.
- **Studio gap:** none.

---

## 5. The gap matrix (local credential mode only)

Severity legend: **B** = the pipeline build halts or produces wrong output; **F** = needs a manual workaround; **N** = avoidable duplicate work.

| # | Capability | What Studio does | What the toolkit task expects | Gap | Severity |
|---|---|---|---|---|---|
| 1 | Enumerate connections | Writes a Studio overlay block per submit. | The schema-discovery task introspects every overlay block. | None — contract honoured. | — |
| 2 | Destination schema (dataset name) | Writes the schema field under the overlay. | The resource-conventions playbook mandates reading it verbatim. | None — explicit read. | — |
| 3 | Connector module path | Writes the connector and connector-source fields. | No task cites these by name; Studio's own parser and dlt-init helper consume them. | None — Studio's harness is the consumer. | — |
| 4 | Entry-point identity | Writes the entry-point field. | No task reads it; dlt resolves resources by Python symbol at runtime. | None for the toolkit; Studio keeps it for re-test paths. | — |
| 5 | Which section header axis is used (connector name vs entry-point name) | One section per kind; legacy callers dual-write. | The workspace-setup task only checks the literal connector-name section. | The scaffold gate may report a missing block when a source-kind connector writes under the entry-point name and that name differs from the connector. | **F** |
| 6 | Credentials sub-section | Emitted only for dataclass-shaped credentials; legacy dual-write otherwise. | dlt runtime resolves credentials; no task cares about the shape axis. | None for the toolkit. | — |
| 7 | Secret values | Local mode: master secrets file written and copied into the clone. | The DuckDB sandbox task requires the secrets file populated. | None — covered. | — |
| 8 | Reusing the discovered resource list | The pre-submit sandbox test returns a resource list but Studio does NOT persist it. | The schema-discovery task re-introspects from scratch every time. | Duplicate work: the same resource list is discovered twice; the first list is thrown away. | **N** |
| 9 | Pre-seeding the Pipeline Inventory | Studio doesn't seed any inventory row stub. | The design-docs task requires Pipeline Inventory rows before the schema-discovery task can fill them. | The assistant has to bootstrap rows from raw config on every fresh intent. | **N** |
| 10 | Incremental cursor declaration | None — the wizard has no cursor field. | Every inventory row must carry an incremental cursor. | The assistant must derive cursor from connector metadata or source docs. | **F** |
| 11 | Write-disposition default | None. | Every inventory row must carry a write disposition. | The assistant picks per resource. | **F** |
| 12 | Schema-contract default | None. | The pinning task must commit a value (never "TBD"). | The assistant picks; aligned. | — |
| 13 | Test-connection verdict surfaced to the task | The pre-submit sandbox returns a category, message, and resource list; only "pass" allows submit. | The discovery task's halt vocabulary is a different set of named errors. | No deterministic translation between a Studio re-test failure and a task-level error code. | **N** |
| 14 | Multi-connection pipeline strategy | N connections → N entries in the config; no convention written. | Pipeline generation assumes a single pipeline per workspace; the patterns catalogue warns against same-name parallel runs but doesn't resolve it. | No Studio or task guidance on workspace layout for N connections. | **F** |
| 15 | Vault-mode end-to-end | — | — | **Vault mode is deferred — local credential mode only.** | — |
| 16 | Vault secret-name mapping | — | — | **Vault mode is deferred — local credential mode only.** | — |
| 17 | Vault reachability gate | — | — | **Vault mode is deferred — local credential mode only.** | — |
| 18 | Bronze-adequacy handoff | — | The source-profiling task runs AFTER bronze lands, not against Studio's pre-landing introspection. | None — the handoff path is the filesystem, not the config file. | — |
| 19 | Fabric harness env injection | Not verified in this rewrite. | The Fabric sandbox task requires Fabric tokens injected by the harness pre-hook. | Follow-up — Fabric pairing belongs with the vault-mode phase. | — |
| 20 | Connector-source registry visibility | Studio has a registry table; not visible to the toolkit. | Tasks assume the connector code is already materialised; Studio's dlt-init helper enforces that. | None — handover is via the filesystem. | — |

---

## 6. Cross-cutting issues (local mode only)

### Secrets passthrough
Local mode is clean. The master file is the source of truth; the copy helper is idempotent and the file permissions are tight. The task invariant *"Do not read env files or arbitrary credential keys yourself"* is honoured because the toolkit reads via dlt's resolution chain, never directly. **No gap.**

### Source-type coverage
Studio's functional spec scopes to API connectors; files and databases route through Fabric Data Factory. The toolkit's ingestion cluster is API-shaped (it targets dlt verified sources). Match is clean.

### Incremental-config handover
Studio captures none of: cursor field, cursor start value, write disposition. The toolkit requires all three on every inventory row. Severity **F** — covered by the assistant re-deriving from connector docs, but it is repeated work per intent.

### Profiling handoff
The source-profiling task is transformation-side; it runs after bronze lands, against landed tables, not against Studio's pre-landing introspection. No handoff exists; none is needed.

### Error-surface mismatch
- Studio's sandbox-test category enum: pass, invalid credentials, source unreachable, connector error, timeout, sandbox setup failed.
- The schema-discovery task's error vocabulary: one error for an import failure and one for an auth failure.
These are disjoint label spaces for the same underlying failure modes. The assistant cannot deterministically translate a Studio re-test failure into a task-level error code without a mapping table.

---

## 7. Action items

Priority legend: **important** = blocks a green path; **secondary** = removes duplicate work; **polish** = nice-to-have.

### Important — Fix the scaffold gate for the section-axis change
- **Side:** the toolkit.
- **What:** loosen the workspace-setup gate to accept the section under either the connector name OR the entry-point name. Or: parse the overlay's entry-point field and check exactly the section Studio wrote (the writer is in `dlt-config-toml.ts`, lines 60–70).
- **Why:** Studio's writer emits one section per connector kind; the literal connector-name check assumes legacy dual-write. With a source-kind connector whose entry point differs from the connector folder, a valid connection will fail the gate.

### Secondary — Persist the sandbox-test resource list into the Studio overlay
- **Side:** Studio.
- **What:** add a `discovered_resources` array to the overlay when the sandbox test returned one. The data is already produced by the sandbox test runner; it just isn't written.
- **Why:** the schema-discovery task explicitly walks every overlay block and produces resource rows. Studio already discovered the list at submit and threw it away. Persisting it lets the discovery task skip a full re-introspection.

### Secondary — Pre-seed the Pipeline Inventory at intent-create time
- **Side:** both.
- **What:** when the dlt-init helper runs at intent creation, append a placeholder Pipeline Inventory row per connection (name, schema, connector, entry-point) into the design doc if it exists.
- **Why:** the coordinator requires the design doc to have a Pipeline Inventory section before any build step. Studio knows the connections at intent creation; the assistant re-discovers them on the first ingestion step today.

### Polish — Document multi-connection workspace layout
- **Side:** the toolkit.
- **What:** add a "multi-connection workspaces" section to the resource-conventions playbook: one `dlt.pipeline()` per connection name, distinct pipeline names, shared pipelines directory, and a naming convention (`<connection>_bronze`).
- **Why:** the patterns catalogue flags the same-name parallel-run anti-pattern but never reconciles it with Studio's N-connections-per-domain model.

### Polish — Cursor and write-disposition discovery hint (optional)
- **Side:** Studio.
- **What:** let the writer record an assistant-supplied cursor field and write disposition once the discovery task picks them — for example, under a `[studio.sources.<name>.discovered]` block.
- **Why:** lets the next session resume schema discovery without redoing inference. Modest gain unless N connections is large.

### Polish — Error-code mapping table
- **Side:** both.
- **What:** publish a one-way mapping from Studio's sandbox-test categories to the schema-discovery task's error codes (invalid credentials → auth-failure error code; connector error → import-failure error code; and so on).
- **Why:** makes the re-test surface actionable inside the discovery task's halt conditions.

### Follow-up — Verify Fabric harness env injection
- **Side:** Studio.
- **What:** confirm that the intent harness pre-hook injects the Fabric tokens, the Studio user ID, and the ephemeral lakehouse env vars that the Fabric sandbox task requires.
- **Why:** not verified by this read; vault credentials and Fabric are paired in a later phase.

---

## 8. Honest uncertainty

- The entry-point field on the Studio overlay is **not mentioned by any task instruction file** I read. Studio's writer comment claims it "drives downstream consumers — the sandbox-test runner's re-tests, and the schema-discovery and pipeline-generation tasks". I could not find this read in either task's description or invariants. It is plausible the discovery task *does* read it (it has to know which `@dlt.source` to import) but the task instructions don't say so.
- The auth-method field is similarly unreferenced by any task instruction file — it appears to be a display hint for Studio's settings viewer "re-pick" path, not a pipeline runtime input.
- I did not read every action-item-relevant file end-to-end. The master-secrets writer was only partially examined, and the sandbox-test runner only its first 200 lines. Conclusions about secret-file behaviour rely on the copy helper and the task invariants, not a full audit of the writer.
- The toolkit version on the main branch may have advanced since this read; no commit hash was pinned.
