# 08 — Plugin Ingestion Approach vs. INGESTION-PLAYBOOK.md

Side-by-side comparison between the **generic, vendor-agnostic ingestion playbook**
(`docs/best_practice_research/INGESTION-PLAYBOOK.md`) and the **current
`vibedata-data-engineering` plugin's ingestion approach** (coordinator
`agents/data-engineer.md`, the ingestion-track skills, and the shared playbooks
under `_shared/references/`).

Claims are verified against the raw plugin files fetched from
`accelerate-data/vd-data-engineering`. Where a determination could not be made
from the fetched files, that is called out explicitly.

---

## 1. Scope of each source

**INGESTION-PLAYBOOK.md** is a vendor-agnostic ingestion build manual. It frames
ingestion as a four-axis decision surface (extract mode, cursor, load mode,
schema contract) and prescribes an **eight-phase build process**: scope a single
source → inventory entities + load modes → profile the source → pick schema
contract → pick credentials → wire incremental cursors → lay out bronze tables
→ test the right layer. It additionally covers production runtime concerns
(idempotency, schema-change workflow, backfill safety, resume semantics,
operational artifacts) and an anti-pattern list. Mental scope: "what a senior
data engineer needs to decide *before* and *around* code, whether dlt, Fivetran,
or Airbyte is the tool."

**Plugin ingestion approach** is an *agent workflow* for building dlt pipelines
end-to-end under the `med` variant. The coordinator (`agents/data-engineer.md`)
owns a six-stage gated flow — **Intake, Workspace, Requirements, Design, Build,
Publish** — with an `implementation-plan.md` ledger of executable steps. Each
step names a single skill (`classifying-data-intents`,
`discovering-source-schema`, `pinning-dlt-schema`, `generating-dlt-pipeline`,
`running-dlt-in-sandbox`, `ingestion-data-testing`, etc.). Skills enforce
medallion guardrails (`_shared/references/playbooks/medallion-guardrails.md`),
dlt resource conventions, ingestion test tiers, and multi-session resume
discipline. Mental scope: "how an autonomous agent, gated by reviewers and
sentinels, builds a *dlt + DuckDB or Fabric* bronze pipeline against an
already-configured Studio source."

---

## 2. The playbook's framework

The playbook's mental model is two-layered:

**The four-axis decision surface** (the "translate these before writing any
code" table, lines 13–18):

1. **Extract mode** — full pull vs. incremental cursor
2. **Cursor** — which server-side field signals "new since last sync"
3. **Load mode** — `append` / `replace` / `merge` (± SCD2)
4. **Schema contract** — `evolve` / `freeze` / `discard_*`

**The eight build phases** (lines 26–143):

| # | Phase | Quoted name |
|---|---|---|
| 1 | Scope a single source | "One pipeline = one source system, not one table" |
| 2 | Inventory entities + decide load modes | the `accounts/events/users/...` table with grain + cursor + mode |
| 3 | Profile the source before writing the pipeline | "Real production teams burn weeks when they skip this step" |
| 4 | Pick your schema-contract posture | "freeze columns, evolve tables, freeze data types" default |
| 5 | Pick your credential strategy | "Secrets file in dev, env vars in prod" |
| 6 | Wire incremental cursors carefully | five rules: `updated_at`, far-past sentinel, `lag`, bounded backfill, `row_order` |
| 7 | Lay out the bronze tables | `models/staging/<system>/`, `raw_<system>` schemas, `stg_<system>__<table>` |
| 8 | Test the right layer | bronze = freshness only; staging = PK unique + not_null; marts = business rules |

Then a **production runtime** layer: idempotency truth table, schema-change
workflow ("vendor adds column → load fails → PR adds to allow-list → CI →
merge"), backfill safety ("separate pipeline + dataset, bounded windows"),
partial-failure resume contract ("`_dlt_loads` filter on `status=0`"), and an
operational-artifacts list (runbooks, freshness gate, schema-drift alert,
re-sync procedure). Closes with an **anti-pattern table** and a "fresh team 2026
recommendations" list of 12 starting moves.

---

## 3. The plugin's framework

The coordinator (`agents/data-engineer.md`) owns six gated user-visible stages:

```
Intake → Workspace → Requirements → Design → Build → Publish
```

Stage names live only in the coordinator; skills neither name nor enforce
stages — they consume the current `implementation-plan.md` step and update its
`status`. The `implementation-plan.md` is "the resume source of truth"
(coordinator §Artifact Locations).

Mapping the plugin's ingestion skills to those stages:

| Stage | Skills invoked (ingestion track) |
|---|---|
| **Intake** | `classifying-data-intents` (action × type axes), `managing-intent-design-docs` (write `intent.md`) |
| **Workspace** | `scaffolding-duckdb-workspace` *or* `scaffolding-fabric-workspace` (templated, `dbt debug` gate) |
| **Requirements** | `managing-intent-design-docs` (intent approval gate — the only required user-confirmation gate per the skill's invariants) |
| **Design** | `discovering-source-schema` (introspect verified-source modules → Pipeline Inventory rows), `pinning-dlt-schema` (commit `schema_contract` per resource), design reviewer dispatch |
| **Build** | `generating-dlt-pipeline` (dlt resource Python + YAML, dry-run gate), `dlt-unit-testing` (mocked, 4 canonical scenarios), `running-dlt-in-sandbox` → `running-dlt-in-duckdb-sandbox` / `running-dlt-in-fabric-sandbox`, `ingestion-data-testing` (Tier 1 mandatory + opt-in Tier 2/3 on bronze), `validating-fixture-replay`, `validating-golden-data`, `evaluating-dlt-pipeline` (deterministic audit pass), `documenting-dlt-pipelines` |
| **Publish** | code-reviewer dispatch + `pinning-dlt-schema` finalizing `"tables": "freeze"` *after* every resource has loaded once |

The plugin's mental model overlays two extra disciplines the playbook does not
articulate:

- **Inventory-as-contract.** `design.md` must include a section literally named
  `Pipeline Inventory` (coordinator: "Do not substitute headings such as
  `Pipeline Design`, `Resources`, or `Table Plan`"). Each row carries object,
  destination schema/table, write disposition, cursor, `schema_contract`, and
  `Status`. Skills *read* the row they're about to act on; coordinators never
  write `Status`.
- **Status machine for resume.** `pending → generated → tested → pinned →
  reviewed` is the canonical enum
  (`_shared/references/playbooks/multi-session-resume.md`), and a returning
  agent reconstructs state from disk, not memory.

---

## 4. Side-by-side phase mapping

| Playbook phase | Plugin equivalent | Fit |
|---|---|---|
| 1. Scope a single source | Implicit in `classifying-data-intents` (action × type) + `intent.md`; no explicit "one source per pipeline" invariant found in fetched files | **Partial** |
| 2. Inventory entities + load modes | `discovering-source-schema` populates Pipeline Inventory; `pinning-dlt-schema` commits write disposition + `schema_contract` per row | **Strong** |
| 3. Profile the source before code | `profiling-source-data` exists, but its description and references target **transformation/bronze adequacy for medallion modelling** (it cites `dbt-patterns.md`, not dlt patterns). No dedicated *pre-build* ingestion source profile skill found | **Partial / mis-aimed** |
| 4. Schema-contract posture | `pinning-dlt-schema` with explicit invariant: "Even `evolve/evolve/evolve` is a committed decision"; `dlt-resource-conventions.md` recommends `freeze` for Salesforce bronze | **Strong** (and stricter than the playbook's "only ~8% set any contract" observation) |
| 5. Credential strategy | Plugin externalizes credentials to Studio's `/add-source` flow + `.dlt/secrets.toml`; sandbox skills *forbid* the agent from touching `FAB_TOKEN*` / `VD_STUDIO_USER_ID`. No general dev-vs-prod discussion | **Strong but narrower** — operationalized, not explained |
| 6. Wire incremental cursors | `dlt-resource-conventions.md` covers cursor pairing per disposition; `dlt-patterns.md` has cursor-test patterns; no `lag`/attribution-window guidance found | **Partial** (mechanics yes, attribution-window discipline no) |
| 7. Lay out bronze tables | `dlt-resource-conventions.md` mandates `<connection_name>_bronze` pipeline name, `src_<connection_name>` schema; **explicitly retires `raw_<source_system>`** — direct conflict with the playbook's "Schema name: `raw_<system>`" | **Strong but divergent** (see §6) |
| 8. Test the right layer | `ingestion-test-tiers.md` makes Tier 1 (`_dlt_id` non-null + unique + row-count > 0) **mandatory on every bronze table**, with Tier 2/3 opt-in; `ingestion-data-testing` enforces. Plugin also runs `dlt-unit-testing` (mocked) **and** `validating-fixture-replay` / `validating-golden-data` | **Stronger than playbook** |
| Runtime: idempotency | Implicit in `dlt-resource-conventions.md` disposition table; no idempotency truth-table | **Partial** |
| Runtime: schema-change workflow | `medallion-guardrails.md` requires explicit acknowledgement per layer; sandbox skills surface contract violations to user. No CI-mediated allow-list PR workflow documented | **Partial** |
| Runtime: backfill safety | Not found in fetched plugin files | **Missing** |
| Runtime: partial-failure resume | `multi-session-resume.md` covers session-level resume; load-package `status=0` semantics not explicit | **Partial** (different axis: agent resume, not pipeline resume) |
| Runtime: operational artifacts | `documenting-dlt-pipelines` mandates per-field YAML; no `runbooks/` discipline, no freshness gate skill, no schema-drift alerting | **Partial** |
| Anti-patterns | `medallion-guardrails.md` codifies bronze "Must NOT" list (no transforms, no joins, no business rules, no PII redaction) | **Strong** for medallion-related anti-patterns |

---

## 5. Agreements

**A1. Schema contract is mandatory, freeze is the default.**
Playbook: "Default for new pipelines: `freeze` columns, `evolve` tables, `freeze`
data types." Plugin: `discovering-source-schema` invariant — "Every Inventory
row carries a committed `schema_contract` value — never leave `'TBD'`"; and
`dlt-resource-conventions.md` — "The default recommendation for Salesforce
bronze is `freeze` on the first pinned run."

**A2. Bronze is data, not code; no transforms in bronze.**
Playbook: "Bronze is *not* a dbt-materialised layer." Plugin
`medallion-guardrails.md`: "No SQL casts, no `COALESCE`, no `CASE WHEN`, no
filters on `is_deleted`, no business-key derivation, no surrogate keys. If you
find yourself writing logic in a bronze pipeline, stop."

**A3. The bronze↔silver contract is PK uniqueness on staging.**
Playbook: "The first test that ships should be: **PK uniqueness on staging.**"
Plugin: Tier 1 `_dlt_id` non-null + unique is mandatory on every bronze table
(`ingestion-test-tiers.md`). Different *layer* (bronze vs. staging) but same
*function* — the dedup contract.

**A4. One folder per source system; don't mix systems.**
Playbook: "One folder per source system. Mixing systems in one staging folder is
universally avoided." Plugin: `dlt-resource-conventions.md` pipeline naming is
`<connection_name>_bronze`; sandbox skills route per source — connection-scoped
isolation throughout.

**A5. Custom "bronze framework" is an anti-pattern.**
Playbook anti-pattern table: "Custom 'bronze framework' wrapping the ingestion
tool". Plugin `generating-dlt-pipeline` invariant: "Do not author a custom
`@dlt.source` wrapper for a verified source. Do not create per-resource
`dlt/<object>.py` files when the verified source already defines them."

**A6. Hardcoded secrets are forbidden.**
Playbook: credential strategy phase. Plugin `medallion-guardrails.md`: "No
hardcoded secrets. Credentials resolve through dlt's stock provider chain
(TOML / env / KV), never inline strings in Python."

---

## 6. Conflicts

**C1. Bronze schema naming: `raw_<system>` vs. `src_<connection>`.**
Playbook (Phase 7): "Schema naming: `raw_<system>` (one schema per source
system). `raw_hubspot.contact` beats `raw.hubspot_contact`." Plugin
`dlt-resource-conventions.md` is explicit and *named in opposition* to that
convention: "**The legacy `raw_<source_system>` convention is retired** — it
predates per-connection schemas and collides on multi-connection setups (e.g.
two Notion connections both writing to `raw_notion`). … `dataset_name =
'src_notion_4'`." Substantive disagreement, not vocabulary.

**C2. Where bronze tests live.**
Playbook: bronze gets *freshness only* via `loaded_at_field`; "Bronze is
'whatever the vendor gave us' — testing it is testing the vendor". Plugin
`ingestion-data-testing` mandates Tier 1 *on every bronze table* (`_dlt_id`
non-null + unique + row count > 0) and *forbids dbt bronze tests*: "Do not
write bronze-layer tests in dbt — bronze is the ingestion layer's concern."
Both are defensible — the plugin treats dlt control columns as the ingestion
layer's *own* invariants, which the playbook's "testing the vendor" claim
doesn't anticipate. Not a real conflict on intent, but a *clear conflict on
where the tests run and what counts as bronze coverage*.

**C3. Profiling skill aim.**
Playbook Phase 3 profiling is **pre-build**: "Hit the endpoint or query the
source directly. Look at 100 rows … Are timestamps server-side?". Plugin's
`profiling-source-data` skill is **post-bronze, pre-transformation** ("for
transformation intents after design skeleton when profiling existing
bronze/source data readiness before medallion modelling"). The plugin has no
*ingestion-track pre-build* profiling skill — the playbook's most-emphasized
phase ("real production teams burn weeks when they skip this step") has no
direct plugin counterpart.

**C4. Schema-change workflow.**
Playbook prescribes "vendor adds column → load fails (freeze) → engineer opens
PR adding column to allow-list → CI runs against staging → merge → prod
unblocks". Plugin's sandbox skills *halt and surface to the user* on contract
violation but do not describe an allow-list PR workflow or a CI gate that
guards the contract. Plugin sees it as an in-session correction; playbook sees
it as a versioned-config commit.

---

## 7. Plugin-only (not in playbook)

- **Inventory-as-contract.** `Pipeline Inventory` in `design.md` with a
  literal-string heading requirement and per-row `Status` enum (coordinator §
  Workflow Contract). The playbook has the equivalent decision table (Phase 2)
  but doesn't make it a *durable, status-tracked artifact* skills read on
  resume.
- **Reviewer gates with exact-JSON verdicts.** Coordinator invariant: "Never
  paraphrase reviewer verdict JSON; paste the exact JSON in a fenced `json`
  block before prose"; "Treat reviewer `BLOCK` as a required correction path,
  not a suggestion."
- **Sentinel-based skill-load proof.** `.skill-ran/<skill-name>` files in eval
  workspaces (coordinator § Skill Loading) so a downstream evaluator can prove
  the real plugin skill was loaded.
- **`implementation-plan.md` ledger** with `pending / generated / tested /
  pinned / reviewed` enum and a hard rule against final-response while any
  step is pending or in-progress (coordinator Invariants).
- **Two-stage `schema_contract` pinning.** The plugin's
  `"tables": "freeze"` knob is *only* added by `pinning-dlt-schema` after every
  resource has loaded once, because freezing tables at generation time raises
  `DataValidationError` (`generating-dlt-pipeline` invariant). This is a
  dlt-version-specific gotcha the playbook does not describe.
- **Sandbox-vs-domain write isolation.** Every `dlt.pipeline(...)` run targets
  a sandbox `.duckdb` or `EPHEMERAL_*` Fabric lakehouse; the domain is
  read-only (`running-dlt-in-sandbox` invariants). The pipeline file must run
  identically in CI against the domain — *no target-conditional code*. This
  is a deployment model the playbook doesn't address.
- **Fixture-replay + golden-data validation as deterministic gates.**
  `validating-fixture-replay` and `validating-golden-data` enforce a default
  0.01 mismatch threshold, halt on three non-deterministic re-runs, and forbid
  in-skill threshold waivers (waivers belong in `design.md`).
- **Medallion guardrails as enforced policy.**
  `_shared/references/playbooks/medallion-guardrails.md` codifies bronze /
  silver / gold "Must" and "Must NOT" lists that skills are required to cite
  and respect. The playbook describes medallion vocabulary in passing but
  doesn't operationalize it as a guardrail document.
- **Connection-scoped pipeline + dataset naming.**
  `<connection_name>_bronze` pipeline and `src_<connection_name>` schema (see
  C1) treat *each Studio source connection* as the unit, not each *vendor
  system* — solves a real multi-instance collision the playbook doesn't flag.
- **Multi-session resume contract.** `_shared/references/playbooks/
  multi-session-resume.md` defines the on-disk state-reconstruction protocol
  (branch + worktree → intent dir → workspace artifacts → recent runs) with
  "trust disk over context".

---

## 8. Playbook-only (no plugin operationalization)

- **`lag` / attribution-window discipline** (playbook §6, rule 3): "Add `lag`
  (attribution window) when upstream mutates after creation. 1 hour for OLTP,
  7 days for marketing/CRM, 30 days for ad networks." No fetched plugin skill
  or playbook mentions `lag` or attribution windows.
- **Backfill-as-separate-pipeline pattern** (playbook §Backfill safety):
  "Separate pipeline + dataset. Production keeps its cursor; backfill runs
  into its own namespace. Don't share `pipeline_name`." No plugin skill names
  a backfill workflow.
- **Partial-failure load-package contract** (playbook §Resume semantics on
  partial failure): "A row appears in `_dlt_loads` only when *all* jobs in a
  package succeed. Downstream consumers filter on `status=0`." Plugin's
  resume discipline is session-level, not load-package-level — the
  `_dlt_loads` consumer-side filter is not surfaced anywhere fetched.
- **Operational artifacts inventory** (playbook §Operational artifacts): a
  `runbooks/` directory with one Markdown per failure mode, a freshness gate
  query, schema-drift alerting, a written re-sync procedure. The plugin
  produces `documenting-dlt-pipelines` YAML but has no skill that authors
  runbooks or freshness gates.
- **Pre-build source profiling** (playbook §3) — see C3. The action
  ("Hit the endpoint, look at 100 rows, classify cursor type, identify
  attribution window") has no ingestion-track skill.
- **Ingestion-outcome as queryable staging model** (playbook §8): "wrap
  [`_dlt_loads`] as `stg_<system>__load_outcomes` so analysts can query
  ingestion health in SQL." No fetched plugin asset does this.
- **Far-past sentinel for `initial_value`** (playbook §6, rule 2): "Use a value
  safely before any source data: `2008-01-01` for modern SaaS, `1990-01-01`
  if you have to go further. Don't pick `1970-01-01` blindly — some APIs
  reject it (GitHub does)." Not found in plugin guidance.
- **`row_order="asc"` warning** (playbook §6, rule 5): "Tempting optimization
  (saves API quota by stopping early); easy to misuse on unordered sources
  (silently drops records)." Not found in plugin guidance.

---

## 9. Verdict

The plugin and the playbook **agree on the substance of medallion-bronze
discipline** — schema contracts are mandatory, freeze is the default, bronze
carries no transforms, custom wrappers are anti-patterns, and the dedup
invariant is the first thing that must ship. Where they diverge is in scope:
the **plugin is deeper on agent execution mechanics** (Inventory-as-contract,
reviewer-JSON gates, sentinel/`implementation-plan.md` ledger, sandbox-vs-
domain isolation, fixture/golden replay) while the **playbook is deeper on
pre-build judgement and production runtime discipline** (source profiling
*before* code, attribution-window `lag`, backfill-as-separate-pipeline,
runbooks, freshness gates, the load-package `status=0` consumer contract).
The plugin's coverage of the eight-phase build is **mature on Phases 2, 4, 7,
8**, **partial on Phases 5, 6**, and **weak on Phase 3** (pre-build profiling).
The plugin's operationalization of medallion guardrails and Tier 1 bronze
tests is in places **stricter than the playbook** and should not be considered
a gap. Net: alignment is high on principle, divergent on naming (`src_*` vs
`raw_*`) and on what counts as "ingestion runtime".

---

## 10. Action items

### P0 — Worth doing before the next ingestion-skill refresh

| # | Title | Target | What to add / change | Why |
|---|---|---|---|---|
| P0-1 | Add a pre-build source-profiling skill | new `profiling-source-api` skill (or rename existing `profiling-source-data` to be ingestion-aware) | Skill that probes the verified source for: (a) server-side vs client-side timestamps, (b) post-creation mutation window, (c) cursor wire-format, (d) server-side `since` filter availability, (e) per-tenant boundaries. Writes findings into `design.md` *before* `pinning-dlt-schema`. | Playbook §3: "Real production teams burn weeks when they skip this step." Currently the plugin jumps from `discovering-source-schema` (static introspection) straight to `pinning-dlt-schema` with no live-source profiling. |
| P0-2 | Document `lag` / attribution-window decisions in Pipeline Inventory | `_shared/references/playbooks/dlt-resource-conventions.md` + `discovering-source-schema` invariants | Add a column `attribution_window` to the Pipeline Inventory; require a value (`none / 1h / 7d / 30d / custom`) for every `merge` and `append` resource. Cite playbook §6 rule 3. | Playbook §6 rule 3: marketing/CRM mutate up to 30 days post-creation; missing `lag` is the most common silent-loss bug. |
| P0-3 | Resolve the `raw_*` vs `src_*` naming conflict in writing | `_shared/references/playbooks/dlt-resource-conventions.md` and/or the playbook | Either upgrade the playbook to note the multi-connection collision and prefer `src_<connection>`, or have the plugin's convention file cross-reference and rebut the playbook's `raw_<system>` recommendation. Pick one source of truth. | C1: today an agent reading both will get contradictory instructions. |

### P1 — Worth doing in the next planning cycle

| # | Title | Target | What to add / change | Why |
|---|---|---|---|---|
| P1-1 | Backfill skill + naming convention | new `running-dlt-backfill` skill + `dlt-resource-conventions.md` | Require a distinct `pipeline_name` and `dataset_name` for backfills; bounded `initial_value` + `end_value`; document parallel-month-window pattern. | Playbook §Backfill safety; absent in plugin. |
| P1-2 | Load-outcome staging model | extend `documenting-dlt-pipelines` or add a small skill | Standard recipe to expose `_dlt_loads` as `stg_<source>__load_outcomes` so analysts can query ingestion health. | Playbook §8 closing recommendation; also closes the "freshness gate" gap. |
| P1-3 | Operational-artifacts checklist | new `_shared/references/playbooks/operational-artifacts.md` referenced by `documenting-dlt-pipelines` | Require a `runbooks/<source>.md` with sections for auth-expiry, schema-drift, re-sync; a freshness-gate query; a schema-drift alert hook. | Playbook §Operational artifacts — none of these exist as plugin output today. |
| P1-4 | `_dlt_loads.status=0` consumer contract | `medallion-guardrails.md` (silver section) | Add a "Must" rule: any silver model reading bronze must filter on the load-outcome staging model (or on `status=0` if reading `_dlt_loads` directly). | Playbook §Resume semantics on partial failure — partial load packages silently leak into silver today. |

### P2 — Worth surfacing back to the playbook

| # | Title | Target | What to add / change | Why |
|---|---|---|---|---|
| P2-1 | Inventory-as-contract pattern | playbook (new section between §2 and §3) | Promote the plugin's `Pipeline Inventory` (object × schema × disposition × cursor × `schema_contract` × `Status`) from "implicit table" to "durable contract artifact reviewed before code". | Plugin operationalizes playbook §2 better than playbook describes it. |
| P2-2 | `"tables": "freeze"` two-stage pinning gotcha | playbook §4 or DLT-PATTERNS.md | Document that freezing tables at generation time fails with `DataValidationError: Can't add table X because tables are frozen`; freeze tables only after the first successful load of every resource. | Plugin `generating-dlt-pipeline` invariant — version-specific dlt knowledge worth porting upstream. |
| P2-3 | Fixture-replay + golden-data as a deterministic gate | playbook §8 or new section | Add the "row-exact replay with 0.01 mismatch threshold, halt on 3-run variance" pattern as the recommended ingestion regression test alongside the bronze freshness gate. | Plugin already runs this and the playbook's testing chapter currently stops at "PK unique on staging". |
| P2-4 | Sandbox-vs-domain write isolation | playbook (new section in §Production runtime patterns) | Cover the pattern of routing every interactive `dlt.pipeline(...)` to an ephemeral destination while keeping the pipeline file CI-compatible against prod — *no target-conditional code*. | Plugin's `running-dlt-in-sandbox` discipline is a real production pattern (PR-time validation against sandbox, CI-time apply to domain) the playbook doesn't cover. |

