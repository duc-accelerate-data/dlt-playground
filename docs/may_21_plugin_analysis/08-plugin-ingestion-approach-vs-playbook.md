# 08 — The Plugin's Ingestion Approach vs the Vendor-Agnostic Playbook

A side-by-side comparison between:

- the **vendor-agnostic ingestion playbook** in the best-practice research folder, and
- the **current ingestion approach inside the data-engineering plugin** — the coordinator's instructions, the ingestion-track tasks, and the playbooks in the plugin's shared folder.

All claims are verified against the plugin's raw files. Where a determination could not be made from the fetched files, it is called out explicitly.

---

## 1. What each source is

**The playbook is a vendor-agnostic ingestion build manual.** It frames ingestion as four decisions you have to make (how to extract, what cursor to use, how to load, what schema contract to commit to) and prescribes an **eight-step build process**: pick one source, list the entities and their load modes, profile the source, pick a schema-contract posture, pick a credential strategy, wire incremental cursors carefully, lay out the bronze tables, and test the right layer. It also covers production runtime concerns (idempotency, schema-change workflow, backfill safety, resume semantics, operational artefacts) and an anti-pattern list. Mental scope: *"what a senior data engineer needs to decide before and around code, whether the tool is dlt, Fivetran, or Airbyte."*

**The plugin's ingestion approach is an assistant-driven workflow for building dlt pipelines end-to-end under the "medium" variant.** The coordinator owns a six-stage gated flow — Intake, Workspace, Requirements, Design, Build, Publish — with a step-by-step plan file as its ledger of executable steps. Each step names a single task: classify the user's request, discover a source's schema, pin the dlt schema, generate the dlt pipeline, run it in a sandbox, run ingestion data tests, and so on. The tasks enforce the medallion guardrails, the dlt resource conventions, the ingestion test tiers, and multi-session resume discipline. Mental scope: *"how an automated assistant, gated by reviewers and marker files, builds a dlt-plus-DuckDB-or-Fabric bronze pipeline against an already-configured Studio source."*

---

## 2. The playbook's framework

The playbook's mental model is two-layered.

**The four decisions you have to make before writing any code:**

1. **How to extract** — full pull vs incremental cursor.
2. **Which cursor** — which server-side field signals "new since last sync".
3. **How to load** — append, replace, or merge (with or without slowly-changing-dimensions tracking).
4. **What schema contract to commit to** — evolve, freeze, or discard.

**The eight build steps:**

| # | Step | The playbook's name for it |
|---|---|---|
| 1 | Pick one source | *"One pipeline = one source system, not one table"* |
| 2 | List the entities and decide load modes | the accounts/events/users table with grain, cursor, and mode |
| 3 | Profile the source before writing the pipeline | *"Real production teams burn weeks when they skip this step"* |
| 4 | Pick a schema-contract posture | *"freeze columns, evolve tables, freeze data types"* default |
| 5 | Pick a credential strategy | *"Secrets file in dev, env vars in prod"* |
| 6 | Wire incremental cursors carefully | the five rules: cursor field, far-past starting value, lookback window, bounded backfill, ordering hint |
| 7 | Lay out the bronze tables | a folder per source system, a schema per source system, staging-table naming convention |
| 8 | Test the right layer | bronze gets freshness only; staging gets PK unique and not-null; marts get business rules |

Then a **production runtime layer**: an idempotency truth table, a schema-change workflow ("vendor adds column → load fails → PR adds to allow-list → CI → merge"), backfill safety ("separate pipeline + dataset, bounded windows"), partial-failure resume contract ("filter consumers on the load-package status"), and an operational-artefacts list (runbooks, freshness gate, schema-drift alert, re-sync procedure). It closes with an anti-pattern table and a 2026 recommendations list of twelve starting moves.

---

## 3. The plugin's framework

The coordinator owns six gated user-visible stages:

```
Intake → Workspace → Requirements → Design → Build → Publish
```

The stage names live only in the coordinator's prompt. Tasks neither name nor enforce stages — they consume the current step from the step-by-step plan and update its status. That plan is *"the resume source of truth"* (in the coordinator's own words).

Mapping the plugin's ingestion tasks to those stages:

| Stage | Tasks invoked (ingestion track) |
|---|---|
| **Intake** | Classify the user's request (along two axes — action and type), then write the intent notes. |
| **Workspace** | Set up the DuckDB workspace, or the Fabric variant (templated, with `dbt debug` as the gate). |
| **Requirements** | The design-docs task waits for user approval of the intent (the only required user-confirmation gate). |
| **Design** | Discover the source's schema (introspect the verified-source modules, fill in Pipeline Inventory rows), pin the schema contract on each resource, then dispatch the design reviewer. |
| **Build** | Generate the pipeline (Python and YAML, dry-run gate), write unit tests (mocked, four canonical scenarios), run it in a sandbox (DuckDB or Fabric child), run ingestion data tests (mandatory Tier 1 plus opt-in Tier 2/3 on bronze), validate fixture replay, validate golden data, run the pipeline-evaluation audit, document the pipeline. |
| **Publish** | Code reviewer dispatch, plus a final pass through the schema-pinning task that freezes the tables — but only after every resource has loaded once. |

The plugin's mental model overlays two extra disciplines the playbook does not articulate:

- **Inventory-as-contract.** The design doc must include a section literally named "Pipeline Inventory". The coordinator says: *"Do not substitute headings such as Pipeline Design, Resources, or Table Plan."* Each row carries object, destination schema and table, write disposition, cursor, schema contract, and a status field. Tasks *read* the row they're about to act on; coordinators never write to the status column.
- **A status machine for resume.** The status enum is `pending → generated → tested → pinned → reviewed`. A returning assistant reconstructs state from disk, not from memory.

---

## 4. Side-by-side step mapping

| Playbook step | Plugin equivalent | Fit |
|---|---|---|
| 1. Pick one source | Implicit in the classification task and the intent notes; no explicit "one source per pipeline" rule in the fetched files. | **Partial** |
| 2. List entities and load modes | Schema-discovery populates the Pipeline Inventory; schema-pinning commits the write disposition and contract per row. | **Strong** |
| 3. Profile the source before code | The source-profiling task exists, but it targets bronze-readiness for medallion modelling, not pre-build ingestion. It cites dbt patterns, not dlt ones. No dedicated *pre-build* ingestion-profiling task was found. | **Partial / mis-aimed** |
| 4. Schema-contract posture | The schema-pinning task with an explicit rule: *"Even `evolve/evolve/evolve` is a committed decision"*. The resource-conventions playbook recommends `freeze` for Salesforce bronze. | **Strong** (and stricter than the playbook's "only about 8% set any contract" observation) |
| 5. Credential strategy | The plugin externalises credentials to Studio's add-source flow and the dlt secrets file; sandbox tasks *forbid* the assistant from touching Fabric tokens or the Studio user ID. No general dev-vs-prod discussion. | **Strong but narrower** — operationalised, not explained |
| 6. Wire incremental cursors | The resource-conventions playbook covers cursor pairing per disposition; the patterns catalogue has cursor-test entries; no lookback-window discipline found. | **Partial** (mechanics yes, lookback-window discipline no) |
| 7. Lay out bronze tables | The resource-conventions playbook mandates a `<connection_name>_bronze` pipeline name and `src_<connection_name>` schema, and **explicitly retires** the older `raw_<system>` naming — a direct conflict with the playbook. | **Strong but divergent** (see section 6) |
| 8. Test the right layer | The ingestion-test-tiers playbook makes Tier 1 (synthetic dlt row-ID present and unique, row count above zero) **mandatory on every bronze table**, with Tier 2/3 opt-in. The plugin also runs dlt unit tests (mocked) AND fixture-replay AND golden-data validation. | **Stronger than the playbook** |
| Runtime: idempotency | Implicit in the resource-conventions disposition table; no idempotency truth-table. | **Partial** |
| Runtime: schema-change workflow | The medallion-guardrails playbook requires explicit acknowledgement per layer; sandbox tasks surface contract violations to the user. No CI-mediated allow-list PR workflow documented. | **Partial** |
| Runtime: backfill safety | Not found in the fetched plugin files. | **Missing** |
| Runtime: partial-failure resume | The multi-session-resume playbook covers session-level resume; the load-package status semantics aren't explicit. | **Partial** (different axis: assistant resume, not pipeline resume) |
| Runtime: operational artefacts | The documentation task mandates per-field YAML; no runbooks discipline, no freshness-gate task, no schema-drift alerting. | **Partial** |
| Anti-patterns | The medallion-guardrails playbook codifies the bronze "Must NOT" list (no transforms, no joins, no business rules, no PII redaction). | **Strong** for medallion-related anti-patterns |

---

## 5. Where they agree

**A1. The schema contract is mandatory, and freeze is the default.**
Playbook: *"Default for new pipelines: freeze columns, evolve tables, freeze data types."* Plugin's schema-discovery task: *"Every Inventory row carries a committed schema_contract value — never leave 'TBD'."* The resource-conventions playbook adds: *"The default recommendation for Salesforce bronze is freeze on the first pinned run."*

**A2. Bronze is data, not code; no transforms in bronze.**
Playbook: *"Bronze is not a dbt-materialised layer."* The plugin's medallion-guardrails playbook: *"No SQL casts, no COALESCE, no CASE WHEN, no filters on is_deleted, no business-key derivation, no surrogate keys. If you find yourself writing logic in a bronze pipeline, stop."*

**A3. The bronze-to-silver contract is PK uniqueness at staging.**
Playbook: *"The first test that ships should be: PK uniqueness on staging."* Plugin: Tier 1 (synthetic dlt row-ID present and unique) is mandatory on every bronze table. Different *layer* (bronze vs staging), but the same *function* — the dedup contract.

**A4. One folder per source system; don't mix systems.**
Playbook: *"One folder per source system. Mixing systems in one staging folder is universally avoided."* Plugin: pipeline naming is `<connection_name>_bronze`; sandbox tasks route per source — connection-scoped isolation throughout.

**A5. A custom "bronze framework" is an anti-pattern.**
Playbook anti-pattern table: *"Custom 'bronze framework' wrapping the ingestion tool"*. Plugin's pipeline-generation rule: *"Do not author a custom `@dlt.source` wrapper for a verified source. Do not create per-resource `dlt/<object>.py` files when the verified source already defines them."*

**A6. Hardcoded secrets are forbidden.**
Playbook: in the credential-strategy step. Plugin's medallion-guardrails playbook: *"No hardcoded secrets. Credentials resolve through dlt's stock provider chain (TOML / env / KV), never inline strings in Python."*

---

## 6. Where they disagree

**C1. Bronze schema naming: a per-system convention vs a per-connection convention.**
Playbook (step 7): *"Schema naming: raw_<system> (one schema per source system). `raw_hubspot.contact` beats `raw.hubspot_contact`."* The plugin's resource-conventions playbook is explicit and *named in opposition* to that convention: *"The legacy `raw_<source_system>` convention is retired — it predates per-connection schemas and collides on multi-connection setups (e.g. two Notion connections both writing to `raw_notion`). … `dataset_name = 'src_notion_4'`."* This is a substantive disagreement, not a vocabulary mismatch.

**C2. Where bronze tests live.**
Playbook: bronze gets *freshness only*; *"Bronze is whatever the vendor gave us — testing it is testing the vendor."* Plugin's ingestion-data-testing task mandates Tier 1 *on every bronze table* (the synthetic dlt row-ID present and unique, plus row count above zero) and **forbids dbt bronze tests**: *"Do not write bronze-layer tests in dbt — bronze is the ingestion layer's concern."* Both are defensible — the plugin treats dlt's own control columns as the ingestion layer's *own* invariants, which the playbook's "testing the vendor" claim doesn't anticipate. Not a real conflict on intent, but a clear conflict on **where the tests run and what counts as bronze coverage**.

**C3. What the source-profiling step is for.**
Playbook step 3 is **pre-build**: *"Hit the endpoint or query the source directly. Look at 100 rows… Are timestamps server-side?"* The plugin's source-profiling task is **post-bronze, pre-transformation**: *"for transformation intents after design skeleton when profiling existing bronze/source data readiness before medallion modelling."* The plugin has no *pre-build* ingestion-profiling task — the playbook's most-emphasised step ("real production teams burn weeks when they skip this step") has no direct counterpart in the plugin.

**C4. The schema-change workflow.**
Playbook prescribes: *"vendor adds column → load fails (freeze) → engineer opens PR adding column to allow-list → CI runs against staging → merge → prod unblocks."* The plugin's sandbox tasks *halt and surface to the user* on a contract violation but do not describe an allow-list PR workflow or a CI gate guarding the contract. The plugin sees this as an in-session correction; the playbook sees it as a versioned-config commit.

---

## 7. Things only the plugin does

- **Inventory-as-contract.** A Pipeline Inventory in the design doc with a literal-string heading requirement and a per-row status enum. The playbook has the equivalent decision table but doesn't make it a *durable, status-tracked artefact* the tasks read on resume.
- **Reviewer gates with strict structured verdicts.** The coordinator's rule: *"Never paraphrase reviewer verdict JSON; paste the exact JSON in a fenced json block before prose,"* and *"Treat reviewer BLOCK as a required correction path, not a suggestion."*
- **Marker files as proof a task actually ran.** In evaluation workspaces, the coordinator drops a small marker file every time it loads a task, so a downstream evaluator can prove the real task fired.
- **The step-by-step plan ledger** with status enum (pending → generated → tested → pinned → reviewed) and a hard rule against producing a final response while any step is pending or in-progress.
- **Two-stage schema-contract pinning.** The plugin's "freeze tables" knob is only added by the schema-pinning task *after every resource has loaded once*, because freezing tables at generation time raises a validation error. This is a dlt-version-specific gotcha the playbook does not describe.
- **Sandbox-vs-domain write isolation.** Every dlt pipeline run targets an ephemeral sandbox destination; the domain itself is read-only during interactive runs. The pipeline file must run identically in CI against the domain — no target-conditional code allowed. This is a deployment model the playbook doesn't address.
- **Fixture-replay plus golden-data validation as deterministic gates.** Default mismatch threshold of 0.01, halt on three non-deterministic re-runs, and no in-task threshold waivers (waivers belong in the design doc).
- **Medallion guardrails as enforced policy.** The plugin's medallion-guardrails playbook codifies bronze, silver, and gold "Must" and "Must NOT" lists that tasks are required to cite and respect. The playbook describes medallion vocabulary in passing but doesn't operationalise it as a guardrail document.
- **Connection-scoped pipeline and dataset naming.** Every Studio source connection is the unit of work, not the vendor system — solves a real multi-instance collision the playbook doesn't flag (see C1).
- **A multi-session resume contract.** The multi-session-resume playbook defines the on-disk state-reconstruction protocol: branch and worktree → intent directory → workspace artefacts → recent runs, with the rule *"trust disk over context."*

---

## 8. Things only the playbook does

- **Lookback-window discipline** (the playbook's step 6, rule 3): *"Add a lookback window when upstream mutates after creation. 1 hour for OLTP, 7 days for marketing/CRM, 30 days for ad networks."* No fetched plugin task or playbook mentions a lookback window.
- **Backfill-as-separate-pipeline pattern** (the playbook's backfill-safety section): *"Separate pipeline + dataset. Production keeps its cursor; backfill runs into its own namespace. Don't share pipeline_name."* No plugin task names a backfill workflow.
- **Partial-failure load-package contract** (the playbook's partial-failure resume section): *"A row appears in the loads table only when all jobs in a package succeed. Downstream consumers filter on status=0."* The plugin's resume discipline is session-level, not load-package-level — the consumer-side filter on the loads table is not surfaced anywhere fetched.
- **Operational artefacts inventory** (the playbook's operational-artefacts section): a runbooks directory with one Markdown per failure mode, a freshness-gate query, schema-drift alerting, a written re-sync procedure. The plugin produces YAML documentation but has no task that authors runbooks or freshness gates.
- **Pre-build source profiling** (see C3 above). The action — *"hit the endpoint, look at 100 rows, classify cursor type, identify mutation window"* — has no ingestion-track task.
- **Surface the dlt loads table as a queryable staging model** (the playbook's step 8): *"wrap the loads table as `stg_<system>__load_outcomes` so analysts can query ingestion health in SQL."* No fetched plugin asset does this.
- **A safe far-past sentinel for the cursor's initial value** (the playbook's step 6, rule 2): *"Use a value safely before any source data: 2008-01-01 for modern SaaS, 1990-01-01 if you have to go further. Don't pick 1970-01-01 blindly — some APIs reject it (GitHub does)."* Not in plugin guidance.
- **The ordering-hint warning** (the playbook's step 6, rule 5): *"Tempting optimisation (saves API quota by stopping early); easy to misuse on unordered sources (silently drops records)."* Not in plugin guidance.

---

## 9. Verdict

The plugin and the playbook **agree on the substance of medallion-bronze discipline** — schema contracts are mandatory, freeze is the default, bronze carries no transforms, custom wrappers are anti-patterns, and the dedup invariant is the first thing that must ship. Where they diverge is in scope: the **plugin is deeper on assistant-execution mechanics** (the Pipeline Inventory as a contract, the structured-verdict gates, the marker files and step-by-step plan ledger, sandbox-vs-domain isolation, fixture and golden replay) while the **playbook is deeper on pre-build judgement and production runtime discipline** (source profiling *before* code, the lookback window, backfill-as-separate-pipeline, runbooks, freshness gates, the consumer-side load-package filter). The plugin's coverage of the eight-step build is **mature on steps 2, 4, 7, 8**, **partial on steps 5 and 6**, and **weak on step 3** (pre-build profiling). The plugin's operationalisation of medallion guardrails and Tier 1 bronze tests is in places **stricter than the playbook** and should not be considered a gap. Net: alignment is high on principle, divergent on naming (`src_*` vs `raw_*`) and on what counts as "ingestion runtime".

---

## 10. Action items

### Highest priority — worth doing before the next ingestion-task refresh

| # | Title | Target | What to add or change | Why |
|---|---|---|---|---|
| 1 | Add a pre-build source-profiling task | A new ingestion-focused profiling task (or rename the existing source-profiling task to be ingestion-aware). | A task that probes the verified source for: (a) server-side vs client-side timestamps, (b) post-creation mutation window, (c) cursor wire-format, (d) server-side filter availability, (e) per-tenant boundaries. Writes findings into the design doc *before* schema pinning. | The playbook's most-emphasised step. The plugin currently jumps from static schema discovery straight to schema pinning with no live-source profiling. |
| 2 | Add the lookback-window decision to the Pipeline Inventory | The resource-conventions playbook plus the schema-discovery task's invariants. | Add a `attribution_window` column to the Pipeline Inventory; require a value (none / 1h / 7d / 30d / custom) for every merge and append resource. | The playbook calls this out as the most common silent-loss bug — marketing and CRM data mutate up to 30 days post-creation. |
| 3 | Resolve the `raw_*` vs `src_*` naming conflict in writing | Either update the playbook to note the multi-connection collision and prefer the per-connection name, or have the plugin's convention file cross-reference and rebut the playbook's per-system recommendation. Pick one source of truth. | Today an assistant reading both will get contradictory instructions. |

### Important — worth doing in the next planning cycle

| # | Title | Target | What to add or change | Why |
|---|---|---|---|---|
| 4 | Backfill task plus naming convention | A new dlt backfill task and the resource-conventions playbook. | Require a distinct pipeline name and dataset name for backfills; bounded start-and-end window; document the parallel-month-window pattern. | The playbook's backfill-safety section; absent in the plugin. |
| 5 | A load-outcome staging model | Extend the documentation task or add a small new task. | A standard recipe to expose the dlt loads table as `stg_<source>__load_outcomes` so analysts can query ingestion health. | The playbook's closing recommendation; also closes the "freshness gate" gap. |
| 6 | An operational-artefacts checklist | A new playbook in the shared folder, referenced by the documentation task. | Require a runbook per source with sections for auth-expiry, schema-drift, and re-sync; a freshness-gate query; a schema-drift alert hook. | The playbook's operational-artefacts section — none of these exist as plugin output today. |
| 7 | Make the load-package status a consumer contract | Add a "Must" rule to the medallion-guardrails playbook's silver section. | Any silver model reading bronze must filter on the load-outcome staging model (or on the load-package status directly if reading the loads table). | The playbook's partial-failure resume section — partial load packages silently leak into silver today. |

### Nice-to-have — worth surfacing back to the playbook

| # | Title | Target | What to add or change | Why |
|---|---|---|---|---|
| 8 | The inventory-as-contract pattern | A new section in the playbook (between steps 2 and 3). | Promote the plugin's Pipeline Inventory (object × schema × disposition × cursor × contract × status) from "implicit table" to "durable contract artefact reviewed before code". | The plugin operationalises this playbook step better than the playbook describes it. |
| 9 | The two-stage schema-contract pinning gotcha | The playbook's step 4 or the patterns doc. | Document that freezing tables at generation time fails with a validation error; freeze tables only after the first successful load of every resource. | A version-specific dlt fact worth porting upstream. |
| 10 | Fixture-replay plus golden-data as a deterministic gate | The playbook's step 8, or a new section. | Add the "row-exact replay with 0.01 mismatch threshold, halt on three-run variance" pattern as the recommended ingestion regression test, alongside the bronze freshness gate. | The plugin already runs this; the playbook's testing chapter currently stops at "PK unique on staging". |
| 11 | Sandbox-vs-domain write isolation | The playbook (a new section in production-runtime patterns). | Cover the pattern of routing every interactive pipeline run to an ephemeral destination while keeping the pipeline file CI-compatible against prod — no target-conditional code. | The plugin's sandbox discipline is a real production pattern (PR-time validation against sandbox, CI-time apply to domain) that the playbook doesn't cover. |
