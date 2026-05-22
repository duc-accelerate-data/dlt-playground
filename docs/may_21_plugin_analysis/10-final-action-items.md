# 10 — Final Action Items for the Plugin

## Why this exists

We ran three analyses of the data-engineering plugin: file `06` measured it against the plugin's own pattern catalogue, file `08` measured it against our vendor-agnostic ingestion playbook, and file `09` measured it against dlt-hub's official AI workbench. The three lists overlap heavily. This file folds them into one prioritised to-do list. Each item cites which analyses raised it, so de-duplication is auditable.

The plugin lives at `plugins/vibedata-data-engineering/` inside the `accelerate-data/vd-data-engineering` repository. We call the Claude Code tasks inside it "skills" throughout — pick once and stick.

A few dlt-specific terms appear repeatedly. Definitions inline the first time they appear:

- **dlt** — an open-source Python library that loads data from a source (an API, a database, a file system) into a destination (a warehouse or local store). The plugin builds dlt pipelines.
- **Bronze layer** — the first landing zone for raw, untransformed source data inside the warehouse. We do not transform data here; we just record what the source said.
- **Schema contract** — the rule dlt follows when the source data's shape changes. `freeze` rejects anything new, `evolve` accepts it, `discard_value` accepts the row but drops the new field.
- **Cursor** — the column in the source that says "this row is new since last sync" (usually `updated_at`). Without one, every run pulls everything.
- **Pipeline Inventory** — a table inside the plugin's design document with one row per resource (e.g. `accounts`, `events`). Each row commits to destination table name, write disposition, cursor, and schema contract before any code is written.

## How we prioritised

**Immediate** = without this, a typical Studio user submits a source and gets a broken or quietly-wrong pipeline. These are the must-do items to make the current ingestion track reliable end-to-end.

**Soon** = quality-of-life and discipline improvements that should follow once the Immediate set has landed. Things that make the plugin more legible and catch a class of bugs nobody has tripped on yet but reasonably will.

**Deferred** = advanced patterns from the playbook or dlt-hub that don't block real users today. Worth keeping on the list, but not until the basics are solid.

---

## Immediate

### 1. Pre-build source profiling

**Priority** — Immediate

**What it is** — Before writing any pipeline code, the assistant inspects the live source for five things: are timestamps server-side (set by the source) or client-side (set by us at fetch time); can the source rewrite or back-date a record after we already loaded it, and for how long (the *attribution window* — the time range during which a source might still mutate records we've already ingested); what wire format the cursor field uses (ISO string, Unix epoch, integer); whether the source can filter "since X" server-side; where tenant boundaries lie. The findings get written into the design document before schema pinning.

**Why we need it** — The single biggest cause of broken ingestion in real teams. A user wires up a HubSpot source today, picks `created_at` as the cursor, looks fine for two weeks, and then silently misses every record HubSpot back-dates. The plugin currently jumps from static schema introspection straight to pinning the schema contract, with no live-data check in between. This is the playbook's most-emphasised step and the workbench's `find-source` pattern in different forms.

**Where it lives in the plugin** — Add a new skill at `plugins/vibedata-data-engineering/skills/profiling-source-api/SKILL.md` (sibling to the existing `discovering-source-schema/` and `profiling-source-data/`). The existing `profiling-source-data/` skill stays as-is — it targets bronze-to-silver readiness, a different step. Wire the new skill into the design phase before `pinning-dlt-schema/`. Update the data-engineer coordinator at `plugins/vibedata-data-engineering/agents/data-engineer.md` to include it in the implementation-plan template.

**What "done" looks like**
- New skill writes a "Source Profile" subsection into `design.md` covering timestamps, attribution window, cursor wire format, server-side filter availability, tenant scoping.
- Pipeline Inventory rows cannot reach `pinned` status until the Source Profile section is filled in.
- The skill calls the live source (within sandbox limits) and records at least 100 sampled rows' worth of observations.

**Source** — 06 §5 item 1; 08 §10 item 1; 09 §9 item 1.

---

### 2. Small-sample first-run loop

**Priority** — Immediate

**What it is** — The first time a new pipeline runs, it runs with three explicit safety knobs: `dev_mode=True` (so dlt creates a throwaway dataset name per run), `.add_limit(1)` on each resource (so we pull one record per endpoint), and `write_disposition="replace"` (so we overwrite, not accumulate). The assistant is told to expect this first run to fail with a credential or config error and to fix it iteratively. Only after the small sample lands cleanly does the assistant remove the limits and switch to the real write disposition.

**Why we need it** — Without this loop, the assistant tries to run a full pipeline against a real source on the first attempt, which either melts API quota, dumps partial data into the wrong place, or hides credential errors behind hundreds of pages of stack trace. The dlt-hub workbench treats this loop as table stakes. Our plugin does a single dry-run gate but doesn't foreground the small-sample iteration.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md` to require the three knobs on every first run, with a checklist that flips them off only after a successful small-sample load. Add a short reference at `plugins/vibedata-data-engineering/playbooks/medallion-guardrails.md` so reviewers cite it.

**What "done" looks like**
- The first generated pipeline file always sets `dev_mode=True`, `.add_limit(1)`, and `write_disposition="replace"`.
- The skill's procedure shows the expected-failure-then-fix loop with example error messages (missing env var, bad token).
- Removing the limits is a discrete step that updates the Pipeline Inventory row status.

**Source** — 08 §6 (sample-and-cap is what only the playbook does); 09 §6 item 2.

---

### 3. Attribution window on incremental resources

**Priority** — Immediate

**What it is** — Every resource that uses an incremental cursor records, in the Pipeline Inventory, how far back the source can still rewrite records. The plugin requires a value: `none`, `1h`, `7d`, `30d`, or `custom`. The generated pipeline wires that value into dlt's `lag` argument on `dlt.sources.incremental(...)` so that each run also rescans the trailing window — catching late-arriving and back-dated rows.

**Why we need it** — Marketing platforms back-date events for up to 30 days; ad networks for 30 days; CRMs commonly for 7. Without the lag, the cursor advances past those edits and the warehouse copy quietly drifts. Today the plugin's resource-conventions playbook mentions this idea but no skill captures it on the Inventory and no generation step wires it through. This is one place where a silent bug is the default outcome.

**Where it lives in the plugin** — Add an `attribution_window` column to the Pipeline Inventory template at `plugins/vibedata-data-engineering/templates/design-doc.md` (or wherever the template lives — verify on first read). Update `plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md` to require the column. Update `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md` to wire the value into `lag=`. Cross-reference from `plugins/vibedata-data-engineering/playbooks/dlt-resource-conventions.md`.

**What "done" looks like**
- Pipeline Inventory rows for `merge` or incremental `append` resources cannot pass review without an `attribution_window` value.
- Generated pipelines call `dlt.sources.incremental(..., lag=...)` with the value from the row.
- Inventory rows with `none` carry a one-line rationale in the row's notes column.

**Source** — 06 §5 item 6 (mutation window wiring); 08 §10 item 2; 09 §9 item 3.

---

### 4. Schema contract defaults that work out of the box

**Priority** — Immediate

**What it is** — Every Inventory row commits to a schema-contract posture; the plugin's defaults are `freeze` for columns, `evolve` for tables, `freeze` for data types — meaning new tables from the source are accepted, but unexpected new columns or type changes fail the load loudly. The skill explains the three postures in plain language and refuses to advance the row's status while the contract field is blank or `TBD`.

**Why we need it** — The plugin already mostly does this — schema pinning today refuses `TBD`. The Immediate-tier improvement is to lock the three default values in code and writing so a Studio user gets a working contract without thinking about it. The playbook says only about 8% of real pipelines set any contract; we want to be in the 8%, by default, on every first build.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/pinning-dlt-schema/SKILL.md` to make the `freeze / evolve / freeze` triplet the default with explicit override rationale required. Update the Pipeline Inventory template to show the three sub-values per row, not one collapsed value.

**What "done" looks like**
- The Inventory shows `columns`, `tables`, `data_type` as three separate sub-cells per row.
- The skill rejects any row that uses the default triplet without one-line rationale only when the default is *overridden*, not when it's accepted.
- The medallion-guardrails playbook cites the default in its bronze rules.

**Source** — 08 §5 item A1; 09 §5 (mandatory contract row); 06 §3 item 8 (comment every override).

---

### 5. Comment every schema override

**Priority** — Immediate

**What it is** — Any time the assistant overrides a default — different schema contract, custom column hint, manual rename, type coercion — the line that does it gets a one-line preceding comment explaining why. No silent overrides.

**Why we need it** — Without this, override calls accumulate inside a pipeline file and become unreadable in three months. The plugin's own pattern catalogue lists this as must-do, but no skill enforces it. This is cheap discipline that pays off immediately and is in scope for a first reliable build.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md` and `plugins/vibedata-data-engineering/skills/pinning-dlt-schema/SKILL.md` to require the comment. Add a check to `plugins/vibedata-data-engineering/skills/evaluating-dlt-pipeline/SKILL.md` so the audit rejects override calls without a preceding comment.

**What "done" looks like**
- Generated pipeline files have a comment line directly above every override call.
- The evaluating-dlt-pipeline audit fails when an override has no comment.

**Source** — 06 §3 item 8, §5 item 7.

---

### 6. Make the pipeline-evaluation rules explicit

**Priority** — Immediate

**What it is** — The skill that audits a generated pipeline today just says "run deterministic audit checks". We replace that with an enumerated checklist: is a schema contract set on every resource; are there no transforms in the bronze pipeline file; does each resource's write disposition match its Inventory row; are all override calls commented; is `allow_external_schedulers=True` set on incremental resources; is `max_table_nesting` set; is the attribution window wired; does the pipeline carry the git commit ID at runtime.

**Why we need it** — Today the audit is a black box. A reviewer reading the skill can't tell whether it catches any of the gaps above. Enumerating the rules turns the audit from "trust me" into a reviewable list and lets us extend it deliberately.

**Where it lives in the plugin** — Rewrite `plugins/vibedata-data-engineering/skills/evaluating-dlt-pipeline/SKILL.md` with an explicit numbered checklist. The skill's output should report pass/fail per rule, not a summary verdict.

**What "done" looks like**
- The skill lists each rule as its own bullet.
- The skill emits one finding per rule, even on success.
- A reviewer can see at a glance which rules ran and which didn't.

**Source** — 06 §5 item 2.

---

### 7. Debug-cleanup discipline

**Priority** — Immediate

**What it is** — When the assistant debugs a failed pipeline run, it changes settings: raises log level, turns on HTTP error body printing, caps retries, adds `progress="log"`. Each change is recorded in a debug-log section of the working notes and reverted before the run is reported successful. The assistant never silently leaves debug settings in production code.

**Why we need it** — Without this, debug knobs leak into the committed pipeline file. Users open PRs full of `log_level="DEBUG"` and end up with noisy production logs and accidentally-disclosed HTTP bodies in CI artefacts. The dlt-hub workbench has this discipline already.

**Where it lives in the plugin** — Add a new playbook at `plugins/vibedata-data-engineering/playbooks/debugging-dlt-pipelines.md` with the revert checklist. Reference it from `plugins/vibedata-data-engineering/skills/running-dlt-in-sandbox/SKILL.md`, the DuckDB sandbox child, and the Fabric sandbox child.

**What "done" looks like**
- The new playbook exists and is linked from each sandbox skill.
- Sandbox skills require the assistant to confirm "no debug settings remain" before marking the step done.
- The pipeline-evaluation audit rule set checks for stray debug knobs.

**Source** — 09 §6 item 3.

---

### 8. Named dev and prod destinations

**Priority** — Immediate

**What it is** — A dlt destination is *where* the data lands — a DuckDB file, a Fabric warehouse, a Postgres database. Today the plugin's sandbox-vs-domain isolation means an interactive run goes to a sandbox and a CI run goes to the domain, but the destination name itself is implicit. We make it explicit: each pipeline declares a named destination, with `dev.secrets.toml` and `prod.secrets.toml` resolving the name to a real connection. Same pipeline file, different secrets profile, no target-conditional code.

**Why we need it** — Today there's a brittle implicit mapping between "is this a sandbox run" and "where does the data go". Making the destination an addressable name lets a user run the same pipeline file locally against DuckDB and in CI against Fabric without code changes — and prevents the surprisingly easy mistake of writing test data into the live domain. The dlt-hub workbench prescribes this pattern and pairs naturally with our sandbox model.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/scaffolding-duckdb-workspace/SKILL.md` and `plugins/vibedata-data-engineering/skills/scaffolding-fabric-workspace/SKILL.md` to create both secrets files and to declare a named destination. Update `plugins/vibedata-data-engineering/playbooks/dlt-resource-conventions.md` to require the named-destination shape.

**What "done" looks like**
- Both scaffolding skills write `.dlt/dev.secrets.toml` and `.dlt/prod.secrets.toml`.
- Generated pipelines call `dlt.pipeline(destination="<named>")` not `destination=duckdb(...)` inline.
- The resource-conventions playbook documents the naming.

**Source** — 09 §6 item 5.

---

### 9. Clarify the bronze test layer

**Priority** — Immediate

**What it is** — The plugin runs Tier 1 tests on bronze: dlt's synthetic row-ID (`_dlt_id`) is present, unique, and the row count is above zero. We make the prose explicit that this test is on the *synthetic* row-ID, not on any natural primary key. Natural-PK uniqueness belongs to the staging layer (downstream dbt tests), not bronze.

**Why we need it** — Without the clarification, an assistant reading the test-tiers skill is tempted to add natural-PK uniqueness checks at bronze, which would violate the medallion guardrails (bronze tests vendor data → flaky). The fix is a few lines of explanatory prose, not a structural change, but it stops a class of well-meaning mistakes.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/running-ingestion-data-tests/SKILL.md` to state the synthetic-vs-natural distinction. Cross-reference the medallion-guardrails playbook in the same edit.

**What "done" looks like**
- The skill's prose says "this test is on `_dlt_id`, a dlt-generated synthetic ID, not on any natural PK".
- The skill explicitly forbids natural-PK uniqueness tests at bronze.
- The medallion-guardrails playbook is cited in the skill's References section.

**Source** — 06 §4 item 1, §5 item 9.

---

## Soon

### 10. `allow_external_schedulers=True` on incremental resources

**Priority** — Soon

**What it is** — A dlt knob on `@dlt.resource` that tells dlt the resource's state is being managed by an external scheduler (Airflow, Dagster, Studio's own scheduler) and not by dlt's local state file. Without it, scheduled runs duplicate state-tracking work and can drift.

**Why we need it** — Standard on production verified sources (Zendesk, Shopify). Absence is silent — pipelines work — until a scheduled CI run starts double-tracking state. Cheap to set; expensive to debug after the fact.

**Where it lives in the plugin** — Add as an invariant in `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md`. Add to the pattern catalogue at `plugins/vibedata-data-engineering/patterns/dlt-patterns.md`. The pipeline-evaluation audit (item 6 above) should check it.

**What "done" looks like**
- Every incremental resource sets the flag by default.
- Inventory rows opt out explicitly with rationale.
- The audit catches missing values.

**Source** — 06 §3 item 1, §5 item 3.

---

### 11. `max_table_nesting=2` and `row_order` decisions

**Priority** — Soon

**What it is** — Two dlt knobs at the source level. `max_table_nesting` caps how deep dlt's automatic flattening goes; without a cap, deeply nested JSON spawns child tables forever. `row_order="asc"` or `"desc"` tells dlt the source returns ordered results, so it can stop early on incremental loads. Both belong in the Inventory as explicit decisions.

**Why we need it** — Schema sprawl from deep nesting is a slow-burn problem — your warehouse fills up with `_v2`, `_v3`, `_v4` child tables and nobody notices for a quarter. `row_order` is a real optimisation with a real foot-gun: misuse it on an unordered source and dlt silently drops records.

**Where it lives in the plugin** — Add both columns to the Pipeline Inventory template. Update `plugins/vibedata-data-engineering/skills/pinning-dlt-schema/SKILL.md` to require `max_table_nesting=2` as default. Update `plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md` to capture the `row_order` decision.

**What "done" looks like**
- Inventory rows show both decisions.
- Generated sources carry both knobs.
- The audit rule set checks both.

**Source** — 06 §3 items 2–3, §5 items 4–5.

---

### 12. Backfill as a separate pipeline

**Priority** — Soon

**What it is** — Backfilling historical data uses a distinct `pipeline_name` and `dataset_name` from production, with bounded `initial_value` and `end_value`. Production keeps its cursor; the backfill writes to its own dataset and gets unioned in the silver layer.

**Why we need it** — Sharing `pipeline_name` between production and backfill causes cursor collisions, dedup confusion, and very fun debugging. Today the plugin doesn't name backfill as a workflow, so users either don't backfill or do it dangerously. This is a "soon" not "immediate" because most first builds don't need a backfill on day one — but the moment someone wants one, the lack of a discipline document bites.

**Where it lives in the plugin** — Add a new skill at `plugins/vibedata-data-engineering/skills/running-dlt-backfill/SKILL.md`. Document the parallel month-window pattern. Reference from `plugins/vibedata-data-engineering/playbooks/dlt-resource-conventions.md`.

**What "done" looks like**
- New skill exists with a separate-pipeline-and-dataset rule.
- The skill prescribes bounded `initial_value` and `end_value`.
- The resource-conventions playbook cross-references it.

**Source** — 08 §10 item 4; 09 §9 item 5.

---

### 13. Load-outcome staging model

**Priority** — Soon

**What it is** — dlt writes a `_dlt_loads` table that records every load package's status. We surface that table as a standard staging model named `stg_<source>__load_outcomes` so analysts can query ingestion health in SQL without learning dlt internals.

**Why we need it** — Today the only way to check ingestion health is to read logs or run a dlt CLI command. Once a Studio user has more than one pipeline, that doesn't scale — but again, it doesn't bite on the first build, so this is "soon" not "immediate".

**Where it lives in the plugin** — Extend `plugins/vibedata-data-engineering/skills/documenting-dlt-pipelines/SKILL.md` with a load-outcomes section, or add a small new skill if the documentation skill is already heavy. Add a "Must" rule to the silver section of `plugins/vibedata-data-engineering/playbooks/medallion-guardrails.md` that any silver model reading bronze filters on load-outcome success.

**What "done" looks like**
- The skill emits a `stg_<source>__load_outcomes.sql` per pipeline.
- The guardrails playbook requires the filter at silver.
- The audit checks for the filter when silver models are present.

**Source** — 08 §10 items 5 and 7; 09 §4 (playbook recommendations bullet 9).

---

### 14. Workspace dashboard handoff

**Priority** — Soon

**What it is** — After every successful pipeline run in the sandbox, the assistant tells the user to run `dlt pipeline <name> show` to open the dlt workspace dashboard. The dashboard renders the schema, the loaded rows, and the load history visually.

**Why we need it** — Today the only output the user gets is per-field YAML and a pass/fail verdict. The dashboard is a free win — dlt already runs it; we just have to surface the command. Helps users build intuition about what their pipeline actually produced.

**Where it lives in the plugin** — Add the handoff to `plugins/vibedata-data-engineering/skills/running-dlt-in-sandbox/SKILL.md` and to the coordinator's success report template at `plugins/vibedata-data-engineering/agents/data-engineer.md`.

**What "done" looks like**
- After a successful sandbox run, the coordinator's report includes the exact `dlt pipeline <name> show` command.
- The sandbox skill's success path mentions the dashboard.

**Source** — 09 §6 item 4, §9 item 8.

---

### 15. Reference the medallion-guardrails playbook from every dlt build skill

**Priority** — Soon

**What it is** — The medallion-guardrails playbook is the plugin's single source of truth for layer rules — what bronze must do, what it must not do, same for silver and gold. Today only the source-profiling skill cites it; the pipeline-generation skill restates a subset of the bronze "must not" rules by hand. We replace the restatement with a reference.

**Why we need it** — Single source of truth. When a rule changes, it changes in one place. Restating rules by hand means they drift.

**Where it lives in the plugin** — Update the References section of `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md`, `pinning-dlt-schema/SKILL.md`, both sandbox skills, and `running-ingestion-data-tests/SKILL.md`.

**What "done" looks like**
- All listed skills cite `playbooks/medallion-guardrails.md` in References.
- The pipeline-generation skill replaces hand-restated rules with a citation.

**Source** — 06 §5 item 8.

---

### 16. Tag pipeline runs with the git commit ID

**Priority** — Soon

**What it is** — Every pipeline run records the git commit ID of the code that produced it in dlt's pipeline metadata. Lets us trace a bad row back to the exact pipeline version that loaded it.

**Why we need it** — Without it, debugging a "this row looks wrong" report devolves into git archaeology. The pattern catalogue lists it as must-do; no skill enforces it.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md` to emit the tag wiring in the generated pipeline file. Add to the pipeline-evaluation audit checklist.

**What "done" looks like**
- Generated pipelines write the commit ID into pipeline metadata at runtime.
- The audit confirms the wiring is present.

**Source** — 06 §3 item 9, §5 item 12.

---

### 17. Pipeline documentation must include cursor, cadence, owner, blast radius

**Priority** — Soon

**What it is** — The documentation skill today bans "TBD" descriptions and requires per-field YAML. We extend it to require, per pipeline: cursor column, refresh cadence (how often the pipeline runs), owner (which team or user is on the hook), blast radius (what downstream models break if this pipeline breaks).

**Why we need it** — All four are listed as must-do in the pattern catalogue; none is enforced. When an incident strikes, these are the four things the on-call needs and currently has to reverse-engineer.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/documenting-dlt-pipelines/SKILL.md`.

**What "done" looks like**
- The YAML doc template includes the four fields.
- Missing any field halts the build.

**Source** — 06 §2 (documenting-dlt-pipelines row), §5 item 11.

---

### 18. Snapshot test for nested shapes

**Priority** — Soon

**What it is** — A unit test type that captures a stable representation of a nested JSON record and fails if the next run produces a different shape. Complements the four canonical scenarios (happy / empty / partial-failure / cursor wiring) the unit-test skill already covers.

**Why we need it** — Nested sources (Salesforce, HubSpot) drift in subtle ways; the canonical four scenarios don't catch shape drift. The pattern is in the catalogue; the skill doesn't surface it.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/writing-dlt-unit-tests/SKILL.md`.

**What "done" looks like**
- The skill describes when to use a snapshot test.
- The skill emits a snapshot test for any resource flagged as nested.

**Source** — 06 §2 (writing-dlt-unit-tests row), §5 item 15.

---

### 19. Resolve `raw_<system>` vs `src_<connection>` naming in writing

**Priority** — Soon

**What it is** — The plugin uses `src_<connection_name>` as the bronze dataset name (e.g. `src_notion_4`). The playbook in the best-practice research folder recommends `raw_<system>` (e.g. `raw_notion`). Both are reasonable. We pick one and document the rationale where readers will see it.

**Why we need it** — Today an assistant reading both gets contradictory instructions. The plugin's choice is right for Studio's multi-connection-per-source reality (two Notion connections can't both write to `raw_notion`), but the rationale is buried.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/playbooks/dlt-resource-conventions.md` with the explicit rebuttal. Update `/tmp/dlt-playground/docs/best_practice_research/INGESTION-PLAYBOOK.md` to flag the multi-connection collision. Add a one-line cross-reference to `plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md`.

**What "done" looks like**
- The conventions playbook explains the conflict and the choice.
- The research playbook flags the multi-connection case.
- The schema-discovery skill points readers at the rationale.

**Source** — 06 §4 item 3; 08 §10 item 3; 09 §8 conflict 1, §9 item 10.

---

### 20. `dev_mode=True` during sandbox iteration

**Priority** — Soon

**What it is** — A dlt flag that suffixes the dataset name with a timestamp on every run, so iterative work doesn't accumulate stale state. Different from item 2 (small-sample first-run loop) — this is about ongoing iteration in the sandbox, not about the first run.

**Why we need it** — Without it, the same dataset accumulates rows across debugging iterations and the assistant ends up debugging the leftover state, not the code. Roughly 7% adoption rate in the wild according to the playbook — high foot-gun.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/running-dlt-in-duckdb-sandbox/SKILL.md` and the Fabric counterpart.

**What "done" looks like**
- Sandbox skills set `dev_mode=True` by default for interactive runs.
- The setting is removed before the pipeline is promoted out of the sandbox.

**Source** — 06 §3 item 4, §5 item 10.

---

## Deferred

### 21. Typed multi-auth credentials

**What it is** — When a source supports multiple authentication methods (API key, OAuth, basic), we wire them as a typed union (`AuthApiKey | AuthOauth | AuthBasic`) rather than a flag-driven dict. Why deferred: most Studio sources have one auth method; this pattern matters when we add sources that don't.

**Where it lives in the plugin** — `plugins/vibedata-data-engineering/skills/pinning-dlt-schema/SKILL.md` and `generating-dlt-pipeline/SKILL.md` when adopted.

**Source** — 06 §3 item 6, §5 item 11.

---

### 22. Pydantic "is this model authoritative?" decision

**What it is** — When a resource has a Pydantic model defined, the schema-pinning step asks whether the Pydantic model is authoritative over the dlt-inferred schema. Why deferred: requires the multi-model authoring path to exist first; today most pipelines don't use Pydantic.

**Where it lives in the plugin** — `plugins/vibedata-data-engineering/skills/pinning-dlt-schema/SKILL.md`.

**Source** — 06 §2 (pinning row), §5 item 13.

---

### 23. Schema-change allow-list PR workflow

**What it is** — When a `freeze` schema contract fails because the source added a column, the workflow is: load fails → engineer opens a PR adding the column to the allow-list → CI runs against staging → merge → prod unblocks. Why deferred: today the plugin handles schema-contract violations as in-session corrections through reviewer gates. The CI-mediated PR workflow is the "correct" production shape but requires a CI ingestion harness we don't have yet.

**Where it lives in the plugin** — Would touch `plugins/vibedata-data-engineering/playbooks/medallion-guardrails.md` and require a new CI workflow file.

**Source** — 08 §6 conflict C4; 08 §3 (production runtime).

---

### 24. Operational-artefacts checklist (runbooks, freshness gates, drift alerts)

**What it is** — Per-source runbook directory, freshness-gate query, schema-drift alert hook, written re-sync procedure. Why deferred: these matter when a pipeline goes to production and starts failing in interesting ways. The Immediate set targets first-run reliability; this targets long-term operability.

**Where it lives in the plugin** — A new playbook at `plugins/vibedata-data-engineering/playbooks/operational-artefacts.md`, referenced from the documentation skill.

**Source** — 08 §10 item 6; 09 §4.

---

### 25. Find-a-better-connector gate

**What it is** — Before scaffolding a custom source, the assistant checks whether a verified dlt source already exists. Why deferred: Studio sources are pre-vetted in our flow, so the gate would rarely fire. If we ever let users define custom sources directly, this becomes Immediate.

**Where it lives in the plugin** — Would be a new front-of-flow step in `plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md`.

**Source** — 09 §6 item 6.

---

### 26. Bidirectional symmetric handoffs between tracks

**What it is** — dlt-hub composes work as small plugins with explicit `incoming` / `outgoing` handoff declarations. Our coordinator owns everything in one linear flow. Why deferred: our scope is one internal track; the multi-plugin architecture is the right shape when we add data-quality and exploration as peers, not now.

**Where it lives in the plugin** — Structural; would touch `plugins/vibedata-data-engineering/.claude-plugin/plugin.json` and the coordinator agent.

**Source** — 09 §6 item 7, §8 conflict 5.

---

### 27. Upstream-gap TODO discipline

**What it is** — Every workaround for a dlt or Studio-source bug carries a `TODO: remove when <repo>#<issue>` comment with a linked issue. Reviewer rejects workarounds without one. Why deferred: meaningful once the plugin has accumulated enough workarounds to need the audit trail; today it would be busywork.

**Where it lives in the plugin** — `plugins/vibedata-data-engineering/skills/evaluating-dlt-pipeline/SKILL.md` and the code reviewer's checklist.

**Source** — 09 §6 item 10.

---

### 28. Surface inventory-as-contract upstream

**What it is** — Promote the Pipeline Inventory pattern back to the best-practice research playbook so other teams can adopt it. Why deferred: this is documentation work in `docs/best_practice_research/`, not plugin work; it doesn't change what Studio users experience.

**Source** — 08 §10 item 8.

---

### 29. Surface two-stage schema-pinning gotcha upstream

**What it is** — Document in the research playbook that freezing tables at generation time raises a dlt validation error; tables can only be frozen after the first successful load. Same reason for deferral as item 28.

**Source** — 08 §10 item 9.

---

### 30. Surface fixture-replay-plus-golden upstream

**What it is** — Promote the row-exact replay with 0.01 threshold and three-run non-determinism halt to the research playbook. Same reason for deferral.

**Source** — 08 §10 item 10.

---

### 31. Surface sandbox-vs-domain isolation upstream

**What it is** — Promote the sandbox-vs-domain pattern (PR-time validation against sandbox, CI-time apply to domain) to the research playbook. Same reason for deferral.

**Source** — 08 §10 item 11.

---

## Cross-cutting themes

The Immediate items concentrate on **capturing knowledge at the right time** — at intake and design, while the Studio user is right there to answer questions, rather than letting the assistant guess later. They also concentrate on **making implicit defaults explicit** — schema contract values, destination names, debug-cleanup steps, the first-run loop. A third theme is **closing the silent-bug class** — attribution windows and commented overrides exist to stop bugs that don't surface until weeks later. The Soon items shift toward **single-source-of-truth hygiene** — referencing the guardrails playbook from every build skill, documenting cursor and cadence, picking one naming convention. The Deferred items are mostly **patterns the plugin will need when its scope grows** — operational artefacts, multi-track handoffs, upstream workflow gates — none of which block today's typical user.

## What we're explicitly NOT doing now

- **Splitting the coordinator into separate ingestion / transformation / data-quality plugins.** dlt-hub's multi-plugin shape is the right long-term architecture but premature for our single-track scope. Revisit when we add a second peer track.
- **Adopting dlt-hub's paid 9,700-source context.** Studio sources are pre-vetted; the discovery problem the upstream solves doesn't exist for us.
- **Mermaid schema export.** Per-field YAML serves the same purpose and is testable; the dashboard handoff (item 14) covers the visual need.
- **dlthub managed runtime deployment.** Our sandbox-versus-domain model is a different production pattern; we don't need the upstream deployment story.
- **A vault-backed credentials path.** dlt's stock provider chain plus our existing Studio secrets handling is enough today; the vault pattern is a future operational concern.
- **Multi-connection workspace ambiguity.** Today the convention is one workspace per connection; we'll revisit the ambiguity if a user files a case where it bites.
