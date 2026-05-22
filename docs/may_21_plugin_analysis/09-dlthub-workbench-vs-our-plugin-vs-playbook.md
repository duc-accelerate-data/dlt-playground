# 09 — dlt-hub's Workbench vs Our Toolkit vs Our Playbook

A three-way comparison between:

- **A. dlt-hub's official AI Workbench** — the upstream maintainer's opinion on how an AI coding assistant should help build dlt pipelines (the `dlt-hub/dlthub-ai-workbench` repository, default branch `master`).
- **B. Our data-engineering toolkit** — the ingestion track inside Studio (`accelerate-data/vd-data-engineering@main`, under `plugins/vibedata-data-engineering/`).
- **C. Our vendor-agnostic ingestion playbook** — the recommendations distilled in file 08 of this analysis folder.

All claims about A and B are verified against the live repository contents at the time of writing. The goal of this file is to figure out where our toolkit (B) can borrow from the upstream (A) and where it already aligns with the playbook (C).

---

## 1. What we're comparing and why

dlt-hub recently published an opinionated, fully-public AI assistant workflow for their own tool. It is shaped by the people who write dlt for a living. Our toolkit is an internal assistant workflow that targets a narrower problem — landing bronze inside a specific medallion architecture for Studio domains. Our playbook is the principle-level guide we use to judge both. Comparing all three forces us to be honest about whether our toolkit is improving on the upstream's design or just reinventing it badly.

---

## 2. What's in dlt-hub's official workbench

The workbench is organised as a collection of **toolkits**, each one a Claude-compatible plugin. Every toolkit is small, single-purpose, and connected to the next one via explicit handoffs. A shared `init` toolkit provides the foundation: workspace verification, secrets handling, and a workspace MCP server.

The toolkits, with a one-line summary of what each automated step does:

**`init` toolkit — shared foundation**
- Verify a uv-managed Python virtual environment, dlt CLI, and workspace status before any other work begins.
- Set up dlt secrets safely by writing only placeholders into the right `.dlt/*.toml` file via an MCP server. The agent is forbidden from reading secret files directly or echoing secret values.
- Dispatch into a specific toolkit based on what the user is trying to do.
- Capture session learnings back into the skills themselves at the end of a working session.

**`bootstrap` toolkit — one-shot workspace creation**
- A single slash command that builds an entire dlthub workspace from scratch (uv venv, `.dlt/`, requirements, etc.).

**`rest-api-pipeline` toolkit — REST/HTTP source pipelines**
- Find the right dlt source for the user's API by classifying request type, searching verified sources, querying dlt-hub's 9,700-source context, then a web search — and refuse to continue if a verified source already exists or if the request is actually a SQL or filesystem source.
- Scaffold the simplest working pipeline against one endpoint with `dev_mode=True`, `.add_limit(1)`, and `replace` write disposition.
- Debug a freshly-run pipeline by raising log level, surfacing HTTP error bodies, capping retries, and walking the user through `dlt pipeline trace`, `load-package`, and `failed-jobs` CLI commands; a checklist requires the agent to revert every debugging tweak it made.
- Validate the loaded data by rendering the schema as a Mermaid diagram, opening the dlt workspace dashboard for a human, and using an MCP tool for the agent itself.
- Add new endpoints, adjust an endpoint's pagination or hints, view loaded data through `dlt pipeline show` or the dlt dataset API.

**`sql-database-pipeline` toolkit — relational source pipelines**
- Find the source by classifying database type, mapping to the right SQLAlchemy driver, checking whether the use case actually needs change-data-capture instead of `sql_database`, exploring tables, then asking the user five gate questions before scaffolding (which tables, destination, normalisation on or off, transform on or off, reflection level).
- Scaffold the pipeline starting with one table, `dev_mode=True`, `.add_limit(1)`; ask up front how much data is involved, and pick a backend (`sqlalchemy` / `pyarrow` / `connectorx`) based on that.
- Adjust the pipeline for production: only remove `.add_limit(1)` after validating the schema; add incremental loading with a cursor column, `merge` write disposition, and an `initial_value`; remove `dev_mode` because it breaks state tracking.
- Add tables, debug runs, validate data, view data — the same shape as the REST API toolkit but specialised for SQL.

**`filesystem-pipeline` toolkit — file-based source pipelines**
- Build the first working pipeline against a glob pattern in S3, GCS, Azure Blob, SFTP, or local.
- Add file-level incremental loading on the file modification date, optionally layered with record-level cursor on a timestamp column.

**`transformations` toolkit — data modelling on top of loaded data**
- Annotate the loaded sources with dlt decorators that capture semantic meaning of columns.
- Create a glossary and an ontology from the annotated sources, scoped only to concepts actually present in the loaded data.
- Generate a Common Data Model in DBML (not SQL DDL, not images).
- Create transformations in ANSI SQL (with IBIS Python as a fallback) that read from the CDM.

**`data-quality` toolkit — runtime checks against loaded data**
- Set up the data quality environment, verifying the required `dlthub.data_quality` license scope is present and listing pipelines from the workspace MCP server.
- Define checks per table and column, auto-detecting candidates from the pipeline schema's existing hints (`primary_key`, `nullable: false`, `unique`).
- Run the checks against the loaded data and review the results, with explicit handoff to the transformations toolkit if failures point to a modelling problem.

**`data-exploration` toolkit — notebook-driven analysis**
- Explore the loaded data interactively through the dlt dataset API and marimo notebooks.

**`dlthub-platform` toolkit — production runtime**
- Set up the dlthub managed runtime once.
- Prepare the workspace for production: split secrets into `dev.secrets.toml` and `prod.secrets.toml`; configure a named production destination so the same code can run against DuckDB locally and Motherduck (or similar) in prod; create a deployment manifest that decorates pipeline runs with `@run.pipeline`.
- Deploy and debug deployments.

**Philosophy.** The workbench is a network of small, opinionated toolkits glued together by explicit incoming/outgoing handoffs. Each toolkit has one **entry skill**, declared in `toolkit.json`, and a `workflow.md` that names the sequence other skills can run in. The agent is never told to do everything; it is told *what to do next* and *who else to talk to*. The official review rubric (`REVIEW.md`) makes the philosophy explicit: don't black-box the process, prefer dlt built-ins over agent-level workarounds, file upstream issues when a skill works around a library gap, never auto-proceed past a human checkpoint, and use ANSI SQL for transformations.

---

## 3. What's in our toolkit's ingestion track

Our toolkit collapses ingestion into a single linear coordinator (the `data-engineer` agent) that owns a six-stage gated flow (Intake, Workspace, Requirements, Design, Build, Publish). The coordinator dispatches focused tasks. The ingestion-track tasks, with a one-line plain-English summary:

- Classify the user's request on two axes (action and type) and refuse out-of-scope work.
- Set up either a DuckDB sandbox workspace or a Microsoft Fabric workspace, with `dbt debug` as the gate.
- Discover what the source connector exposes by introspecting Studio's verified-source modules, then writing every resource as a row into a "Pipeline Inventory" section of the design document.
- Profile bronze data for medallion readiness — currently aimed at *transformation* intents that build silver on top of existing bronze, not pre-build ingestion checks.
- Pin a schema contract on each resource — every Inventory row must commit to a value, "TBD" is forbidden.
- Generate the dlt pipeline file and YAML, dry-run it, and halt the build if dry-run fails.
- Run the pipeline in a sandbox destination — never against the live domain — using a dispatcher that reads `vd-domain.yml` and picks the DuckDB or Fabric child task.
- Write unit tests (mocked, four canonical scenarios) and ingestion data tests (Tier 1 mandatory on every bronze table: `_dlt_id` not null, unique, row count above zero; Tier 2 and Tier 3 opt-in).
- Replay frozen fixtures and golden data with a strict mismatch threshold (default 0.01); halt if three runs against the same input produce different counts.
- Evaluate the generated pipeline against a fixed audit rule set without executing it.
- Document every field of every resource in YAML, with no "TBD" descriptions and no missing fields.
- Pin the `tables` schema knob in a second pass *only after* every resource has loaded once.

The shared references that the tasks cite:

- A patterns catalogue (`dlt-patterns.md`) covering source shape, cursor configuration, write dispositions, and schema-contract risk.
- A resource conventions playbook prescribing parent/child layout, dlt control columns, `<connection_name>_bronze` pipeline naming, and `src_<connection_name>` dataset naming.
- The ingestion test tiers playbook (Tier 1 / Tier 2 / Tier 3).
- The medallion guardrails playbook (bronze "Must" and "Must NOT" rules).
- The data-engineer coordinator agent prompt.

**Philosophy.** The toolkit is a single linear pipeline with a strict reviewer-gated build phase. Every step is a row in an "Inventory" contract; status moves through `pending → generated → tested → pinned → reviewed`; reviewers return structured JSON verdicts that the coordinator pastes verbatim before any prose; and a step-by-step plan file is the resume source of truth across sessions. Sandbox writes are isolated from domain data; CI is expected to run the same file against the live domain without target-conditional branching.

---

## 4. What our playbook recommends

The playbook (file 08 distillation) names twelve principles for any ingestion build. The highest-priority ones:

- Commit to a **schema contract posture** before code; default is freeze columns, evolve tables, freeze data types.
- **Profile the source live before writing the pipeline** — hit the endpoint, look at 100 rows, check whether timestamps are server-side, whether records mutate post-creation, whether server-side filters exist.
- **One pipeline = one source system**, not one table.
- For each entity, decide **grain, cursor, and write disposition** before code.
- **Lookback windows** on incremental cursors — 1 hour for OLTP, 7 days for marketing or CRM, 30 days for ad networks — because data mutates after creation.
- **Backfill is a separate pipeline and a separate dataset**, never share `pipeline_name` with production.
- Test the right layer: bronze gets freshness only; staging gets primary-key uniqueness; marts get business rules.
- Operational artefacts are required output: a runbook per failure mode, a freshness gate query, a schema-drift alert hook, a written re-sync procedure.
- Downstream consumers of bronze must **filter on load-package status** so partial-failure loads don't leak.
- Surface the dlt loads table as `stg_<source>__load_outcomes` so analysts can see ingestion health in SQL.
- **No "custom bronze framework"** wrapping the ingestion tool — that is an anti-pattern.
- **No hardcoded secrets** — credentials come from dlt's stock provider chain.

---

## 5. Three-way agreement map

| Practice or principle | dlt-hub's workbench | Our toolkit | Our playbook | Notes |
|---|---|---|---|---|
| Schema contract is mandatory and freeze is the safe default | Implicit. Schema is captured but the agent doesn't force a contract. Data-quality toolkit later adds checks. | Explicit. Every Inventory row must commit to a contract; "TBD" halts the build. | Explicit. Freeze columns and data types by default. | Our toolkit is the strictest. |
| Bronze is data, not code; no transforms in bronze | Implicit. SQL toolkit has `query_adapter_callback` for filters and `add_map` for masking, and the boundary note tells the agent to hand off to the transformations toolkit for anything else. | Explicit policy in the medallion-guardrails playbook (no casts, no `CASE`, no business keys). | Explicit. | All three agree. |
| Profile the source *before* writing the pipeline | Partial. `find-source` does endpoint research and asks gate questions. SQL `find-source` lists tables. No "look at 100 rows of real data" step. | Missing for ingestion. The profiling task exists but is aimed at silver-readiness over existing bronze. | Most-emphasised step in the playbook. | This is the playbook's biggest gap in our toolkit. |
| One source per pipeline, separate folders per source | Implicit by construction. Each toolkit run scaffolds one source via `dlt init`. | Implicit. The naming convention is `<connection_name>_bronze`. | Explicit. | All three converge in practice. |
| Choose write disposition + cursor up front | Explicit. Adjust-table walks the user through cursor column and `initial_value`; filesystem adds incremental in a dedicated step. | Explicit. Every Inventory row carries write disposition and cursor before code. | Explicit, with a five-rule cursor discipline. | Our toolkit captures the decision but not the discipline. |
| Lookback window on incremental cursors | Missing. | Missing. | Explicit (1h / 7d / 30d). | Both toolkits silently ship the common bug the playbook warns about. |
| Sample-and-cap on first run | Explicit. `dev_mode=True`, `.add_limit(1)`, `write_disposition="replace"`, expect-to-fail-then-fix loop. | Implicit through the sandbox dispatcher; not as foregrounded as the upstream's loop. | Mentioned via the four playbook decisions. | Upstream is more explicit; we should make ours louder. |
| Sandbox versus production write isolation | Partial. Dev mode and `dataset_name` discipline; the platform toolkit splits `dev` and `prod` profile secrets and named destinations. | Strong. Every interactive run writes to a sandbox; the same file runs against the live domain in CI without target-conditional code. | Not covered explicitly. | Our toolkit is stronger and prescribes a real production pattern. |
| Testing tiers | Partial. The separate `data-quality` toolkit defines checks per table and column, but only after a paid license scope is verified. No mandatory bronze-test floor. | Strong. Tier 1 is mandatory on every bronze table; Tier 2 and Tier 3 are explicit opt-ins. | Recommends PK-unique on staging and freshness on bronze. | Our toolkit is the strictest. |
| Naming conventions | Light. `dlt init` picks the dataset name from the source name; no global rule. | Strict. Pipeline = `<connection>_bronze`; dataset = `src_<connection>` (the legacy `raw_<system>` is deliberately retired). | Recommends `raw_<system>` — direct conflict with us; see section 8. | Pick one and document. |
| Documentation | Implicit. Skills embed authoritative doc links and tell the agent to keep them current. | Strong. Per-field YAML; halt if any field is undocumented. | Calls for runbooks plus a schema-drift alert. | Our YAML is the deepest; the playbook's runbooks are missing from both toolkits. |
| Evaluation gate | Missing in upstream — there is a review rubric for PRs but no per-pipeline audit. | Strong. The evaluating task runs deterministic audit checks before judgement findings, returns structured findings to the coordinator. | Not explicit. | Our toolkit is unique here. |
| Reviewer / human checkpoint | Explicit in product principles ("agents don't auto-proceed past human review"); each skill stops before destructive steps. | Explicit. Reviewer sub-agents return structured JSON verdicts; coordinator pastes the verbatim JSON; user-approval gates required at intent and design. | Implicit. | Both toolkits agree on the principle; ours is more structured. |
| Recovery and resume | Light. Each skill's "incoming context check" assumes pipeline name is known on re-entry. | Strong. The implementation-plan file is the resume source of truth across sessions; status enum is enforced. | Calls for a load-package filter so partial failures don't leak. | Different axes: assistant resume vs pipeline-run resume. |
| Secrets handling | Strong and deterministic. MCP tools (`secrets_list`, `secrets_view_redacted`, `secrets_update_fragment`); the agent is forbidden from reading secrets files or printing secret values. Placeholders only. | Strong. Credentials go through dlt's provider chain; the bronze guardrail forbids hardcoded secrets. | Brief — mostly says "no hardcoded secrets". | Upstream is the most operationally detailed. |
| Production destination strategy | Strong. Named destinations let the same code resolve to DuckDB locally and Motherduck in prod; dev and prod secrets profiles separate cleanly. | Partial. Sandbox-vs-domain isolation covers part of this but not the dev/prod profile concept directly. | Not covered. | Worth borrowing. |

---

## 6. Where dlt-hub does something we don't

Items we should consider importing into our toolkit:

1. **Mandatory upfront source-shape research.** dlt-hub's REST `find-source` skill instructs the agent to search the verified-source list, the dlt-hub context (9,700 source definitions), and the web in parallel before recommending anything. Quote: *"Avoid 3rd party providers, integrators and proxies. Prefer authoritative answers."* Our schema-discovery task introspects the configured Studio source but does not do the upstream search. **Adopt selectively** — Studio sources are pre-vetted, so a full search is not always needed, but the *check whether a better connector exists* step is healthy.
2. **Sample-and-cap first run as the default loop.** dlt-hub's create-pipeline skills make `dev_mode=True`, `.add_limit(1)`, and `replace` the explicit starting point, then expect a 401 / `ConfigFieldMissingException` to flush out credentials. Our pipeline-generation task dry-runs the file but does not foreground this small-sample loop. **Adopt** — it's cheap, deterministic, and matches our playbook's "sample before full load" principle.
3. **A debugging discipline that revertes its own changes.** dlt-hub's `debug-pipeline` skill ends with a checklist: restore `log_level`, remove `http_show_error_body`, remove `request_timeout`, remove `progress="log"`. Quote: *"Do NOT remove settings the user had before you started debugging."* We have nothing equivalent. **Adopt** as a new shared playbook.
4. **A live workspace dashboard handoff.** dlt-hub points the human to `dlt pipeline <name> show` after every successful load. We rely on YAML docs and the design doc. **Adopt** — at minimum, surface the command in our validation task.
5. **Named destinations for the same code in dev vs prod.** The `dlthub-platform` toolkit prescribes named destinations so the pipeline runs against DuckDB locally and Motherduck (or similar) in prod with no code change. We achieve some of this through sandbox-vs-domain, but the *named destination* abstraction is cleaner and orthogonal. **Adopt** — pairs naturally with our existing sandbox isolation.
6. **A "find a better connector first" gate.** Both REST and SQL `find-source` skills make the agent stop and hand off if a verified source already exists or if the user's data is actually CDC. **Adopt selectively** — for Studio sources we have pre-built connectors, but if a user adds a new source by hand we should still run this check.
7. **Bidirectional symmetric handoffs between toolkits.** The official review rubric requires every outgoing handover to have a matching incoming entry in the target toolkit. We do not have this discipline because everything lives in one coordinator. **Adopt the principle** — our coordinator could route to different "tracks" (ingestion, transformation, data quality) with explicit incoming context skips.
8. **Backfill as a separate task.** dlt-hub's `adjust-table` skill is not specifically a backfill skill, but its discipline of "remove dev limits only after validation" and "incremental on `updated_at` with `initial_value`" is closer to the playbook's backfill discipline than anything we have. **Adopt** as a new dedicated backfill task (see playbook gap).
9. **Stop and verify before destructive moves.** dlt-hub's prepare-deployment skill literally says *"STOP before making changes. Show your plan and get approval from the user."* We have the equivalent via reviewer gates but the slogan is healthier — every destructive moment deserves an explicit pause. **Adopt** as boilerplate in any task that mutates user files.
10. **Surface upstream library gaps as TODOs.** The official review rubric demands every skill-level workaround be tagged `TODO: remove when dlt#<issue> is resolved` and tracked in the right repo. We do not enforce this. **Adopt** — discipline that prevents workarounds from calcifying.
11. **Modular toolkits with their own entry skill.** dlt-hub composes via small toolkits, each with one entry skill declared in `toolkit.json`. Our coordinator owns everything. **Consider** — over time this lets new tracks (e.g. data quality, exploration) layer in without modifying the coordinator.

Items not worth adopting:

- The Mermaid schema export. Useful for humans, but our YAML field-level docs serve the same purpose and are testable.
- The `dlt-hub` paid context (9,700 sources). Studio sources are pre-vetted.
- The dlthub managed runtime deployment. Our sandbox-versus-domain model is already a different production pattern.

---

## 7. Where we do something dlt-hub doesn't

Items that are real strengths and worth keeping:

1. **The Pipeline Inventory as a durable contract.** Our design.md must include a heading named exactly "Pipeline Inventory" with rows for every resource, status enum included. dlt-hub captures the same decisions but never persists them as a contract artefact that downstream tasks read on resume. **Keep.**
2. **A linear coordinator with structured reviewer verdicts.** The reviewer JSON contract and the rule *"Treat reviewer BLOCK as a required correction path, not a suggestion"* are stronger than dlt-hub's per-skill checkpoints. **Keep.**
3. **A two-stage schema-contract pinning that avoids the `tables: freeze` validation error.** This is a version-specific dlt fact we have learned and codified; dlt-hub does not surface it anywhere. **Keep**, and consider proposing upstream.
4. **Sandbox versus domain write isolation with CI symmetry.** Every interactive `dlt.pipeline(...)` writes to the sandbox; the same file runs identically against the live domain under CI; no target-conditional branching is allowed in pipeline code. dlt-hub uses `dev_mode=True` + named destinations which is close but not identical. **Keep.**
5. **Mandatory Tier 1 data tests on every bronze table.** `_dlt_id` not-null and unique, plus row count above zero — non-negotiable. dlt-hub's data-quality toolkit is opt-in, license-gated, and discovers candidates from schema hints instead of mandating a floor. **Keep.**
6. **Fixture replay plus golden data validation as deterministic gates.** Row-exact comparison, 0.01 mismatch threshold by default, three-run variance halt for non-determinism. No upstream equivalent. **Keep.**
7. **Per-field YAML documentation as a halt condition.** Every field in every resource must have a description; "TBD" or empty halts the build. dlt-hub embeds doc links but does not enforce field-level docs. **Keep.**
8. **Refusal protocol at intake.** Out-of-scope work is refused with no tool calls. dlt-hub's individual `find-source` skills do partial versions of this; ours is uniform. **Keep.**
9. **Marker files (`.skill-ran/<name>`) in eval workspaces** that prove the right skill was actually loaded. dlt-hub has no equivalent — their workbench is for interactive use, not evaluation harnesses. **Keep.**
10. **A status-enum step ledger across sessions.** Our implementation-plan.md ledger plus the rule *"never send a final response while any step is pending"* is more rigorous than dlt-hub's per-skill incoming-context checks. **Keep.**

Items where we should re-examine whether scope is right:

- The dbt and medallion modelling rules currently live alongside ingestion-track tasks. dlt-hub keeps ingestion, transformation, and data quality in separate toolkits with explicit handoffs. **Re-examine** — over time, splitting our coordinator into ingestion, transformation, and data-quality tracks (each with its own reviewer set) may scale better.
- Our profiling task is aimed at transformation work, not ingestion. **Re-aim** (and see action items).

---

## 8. Conflicts

Places where dlt-hub, our toolkit, and our playbook genuinely disagree on substance:

**Conflict 1 — Bronze dataset naming.**
- Our toolkit: `src_<connection_name>` (e.g. `src_notion_4`). The legacy `raw_<system>` convention is deliberately retired because two Notion connections both writing to `raw_notion` collide.
- dlt-hub: lets `dlt init` pick the dataset name from the source name (effectively `<source>_data` by default; the user names it).
- Our playbook: recommends `raw_<system>`.
- **Right side:** our toolkit is right *for our context* (multi-connection Studio domains). The playbook should be updated to flag the multi-connection collision. dlt-hub's default is fine for the single-connection case.

**Conflict 2 — Where bronze tests live.**
- Our toolkit: ingestion-data-testing writes Tier 1 tests as pytest functions querying DuckDB directly. dbt bronze tests are forbidden — *"bronze is the ingestion layer's concern."*
- dlt-hub: the `data-quality` toolkit puts checks on a paid scope, discovers candidates from schema hints rather than mandating a floor, and is opt-in.
- Our playbook: bronze gets freshness only; *"testing bronze is testing the vendor."*
- **Right side:** our toolkit's mandatory Tier 1 floor is right — `_dlt_id` not-null and unique is *not* testing the vendor, it's testing dlt itself. The playbook should be updated. dlt-hub's data quality is complementary, not contradictory; it just runs at a different layer.

**Conflict 3 — Where source profiling happens.**
- Our toolkit: profiling targets existing bronze before silver design (a *transformation-time* check).
- dlt-hub: `find-source` does research-time profiling (read the API docs, ask the user gate questions) but does not do live-data profiling either.
- Our playbook: profiling is **pre-build** — hit the endpoint, look at 100 rows, classify cursor type, identify mutation window. Most-emphasised step.
- **Right side:** the playbook. Neither toolkit does pre-build live-data profiling. Both should add it.

**Conflict 4 — Mandatory contract vs opt-in.**
- Our toolkit: every Inventory row must commit to a contract; "TBD" halts the build.
- dlt-hub: the agent captures a schema but does not force a contract commitment up front.
- Our playbook: freeze columns and data types by default; even evolve is a committed decision.
- **Right side:** our toolkit and the playbook agree, and dlt-hub should adopt the discipline.

**Conflict 5 — One coordinator vs many toolkits.**
- Our toolkit: one coordinator runs the linear flow.
- dlt-hub: many small toolkits glued by explicit handoffs.
- Playbook: not opinionated on this axis.
- **Context-dependent.** dlt-hub's structure is better for a public marketplace where users mix and match; our coordinator is better for a single internal Studio workflow with strict gates. As our scope grows, theirs may scale better.

---

## 9. Action items for our toolkit

Each item lists what to add or change, where it lives in our toolkit, why, and a priority.

| # | Title | What to add or change | Where it lives in our toolkit | Source we're borrowing from | Priority |
|---|---|---|---|---|---|
| 1 | Add a pre-build source-profiling task | A new task (or a redirected version of the existing profiling task) that probes the live source for: server-side vs client-side timestamps, mutation window after creation, cursor wire-format, presence of server-side filters, per-tenant boundaries. Writes findings into design.md before schema pinning. | New ingestion-track task; called from the design phase before pinning-dlt-schema. | Our playbook (most-emphasised gap). dlt-hub's `find-source` style of upfront research informs the format. | Highest priority |
| 2 | Make the small-sample first-run loop explicit | A "first run is `dev_mode=True` + `.add_limit(1)` + `replace`; expect a failure that reveals credential gaps; do not progress until the small sample lands successfully" pattern, codified in our generating-dlt-pipeline task and reflected in the medallion-guardrails playbook. | generating-dlt-pipeline task + a new sub-section in medallion-guardrails. | dlt-hub. | Highest priority |
| 3 | Add lookback-window discipline to the Pipeline Inventory | Add an `attribution_window` column to the Inventory; require a value (none / 1h / 7d / 30d / custom) for every merge and append resource. | dlt-resource-conventions playbook + discovering-source-schema task invariants. | Our playbook. | Highest priority |
| 4 | Add a debugging-discipline playbook with a revert checklist | A new shared playbook prescribing: increase log level, surface HTTP error bodies, cap retries, but record every change and revert it before reporting. | A new playbook plus an invariant in running-dlt-in-sandbox. | dlt-hub's `debug-pipeline`. | Important |
| 5 | Add a backfill task with separate pipeline_name + dataset | A new ingestion task that explicitly scopes backfills to a distinct `pipeline_name` and `dataset_name`, with bounded start-and-end windows. Cross-reference our resource-conventions. | New backfill task. | Our playbook. | Important |
| 6 | Surface a load-outcome staging model | A small new task or an extension of documenting-dlt-pipelines that exposes the dlt `_dlt_loads` table as a `stg_<source>__load_outcomes` model so analysts can see ingestion health in SQL. | New documentation/test task; reference from medallion-guardrails. | Our playbook. | Important |
| 7 | Add named-destination dev/prod profile pattern | A new task or extension to scaffolding-duckdb-workspace / scaffolding-fabric-workspace that sets up `dev.secrets.toml` and `prod.secrets.toml` with a named destination so the same pipeline file runs against DuckDB in dev and the domain destination in prod. | scaffolding-* tasks; resource-conventions update. | dlt-hub's prepare-deployment skill. | Important |
| 8 | Workspace dashboard handoff after every successful load | Add a "tell the user to run `dlt pipeline <name> show`" step to running-dlt-in-sandbox and to the success notification surface. | running-dlt-in-sandbox + coordinator success report. | dlt-hub's `validate-data` skill. | Nice-to-have |
| 9 | Upstream-gap TODO discipline | When a task carries a workaround for a dlt or Studio-source bug, require a `TODO: remove when <repo>#<issue>` comment and a linked issue. Reviewer should reject workarounds without one. | A new invariant in the evaluating-dlt-pipeline task; an addition to the code reviewer's checklist. | dlt-hub's review rubric. | Nice-to-have |
| 10 | Resolve the bronze-naming conflict in writing | Update our playbook (file 08, then the source-of-truth playbook in best-practice research) to note the multi-connection collision and prefer the per-connection name. Cross-reference our resource-conventions explicitly. | The playbook itself, plus a cross-reference in resource-conventions. | This three-way comparison. | Nice-to-have |

---

## 10. Verdict

Overall, our toolkit is **more rigorous on the assistant-execution mechanics** than dlt-hub's official workbench: structured reviewer verdicts, durable Inventory contracts, mandatory Tier 1 bronze tests, deterministic fixture and golden replay, sandbox-vs-domain isolation. dlt-hub's workbench is **broader on the surface area** (REST, SQL, filesystem, transformations, data quality, exploration, platform deployment) and **softer on the gates**, leaning instead on small toolkits, explicit handoffs, and per-skill checkpoints. The two designs have different shapes for different scopes — dlt-hub is a public marketplace; ours is one internal track. Where we are clearly behind is **pre-build live source profiling**, **lookback-window discipline on cursors**, and **a couple of operational hygiene patterns** (named dev/prod destinations, workspace-dashboard handoff, debug-revert checklist) that the upstream's working assistants have already learned the hard way and codified. None of those gaps is structural; all are takeable in a single planning cycle.
