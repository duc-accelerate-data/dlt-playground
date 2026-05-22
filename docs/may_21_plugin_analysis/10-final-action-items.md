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

Each item also carries a **Home** field that names where in the plugin the fix physically lives:

- **skill body** — a rule inside a specific `skills/<name>/SKILL.md`. Behavioural rules, halt codes, file paths the skill must write, output contracts, audit rules.
- **playbook** — a procedure document under `_shared/references/playbooks/<name>.md`. Multi-step procedures, code templates, env-var inventories, debugging hints — knowledge an agent looks up.
- **pattern catalogue** — one entry in `_shared/references/patterns/dlt-patterns.md`. One-line "do this / don't do that" cards with a 2–3 line rationale.
- **coordinator** — a rule inside `agents/data-engineer.md`. Cross-skill orchestration.
- **design-doc template** — a column or section in whatever template the design doc inherits from.
- **Studio code** — lives in the Studio app codebase, not the plugin.

Many items split across two homes — e.g. an attribution_window column is both **design-doc template** (column exists) and **skill body** (skills read/write it).

---

## Immediate

### 1. Small-sample first-run loop

**Priority** — Immediate

**Home** — skill body, playbook

**What it is** — The first time a new pipeline runs, it runs with three explicit safety knobs: `dev_mode=True` (so dlt creates a throwaway dataset name per run), `.add_limit(1)` on each resource (so we pull one record per endpoint), and `write_disposition="replace"` (so we overwrite, not accumulate). The assistant is told to expect this first run to fail with a credential or config error and to fix it iteratively. Only after the small sample lands cleanly does the assistant remove the limits and switch to the real write disposition.

**Why we need it** — Without this loop, the assistant tries to run a full pipeline against a real source on the first attempt, which either melts API quota, dumps partial data into the wrong place, or hides credential errors behind hundreds of pages of stack trace. The dlt-hub workbench treats this loop as table stakes. Our plugin does a single dry-run gate but doesn't foreground the small-sample iteration.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md` to require the three knobs on every first run, with a checklist that flips them off only after a successful small-sample load. Add the procedural detail and expected-failure examples to `_shared/references/playbooks/medallion-guardrails.md` (or a new `dlt-first-run-loop.md` playbook) so the skill body cites it rather than restates it.

**What "done" looks like**
- The first generated pipeline file always sets `dev_mode=True`, `.add_limit(1)`, and `write_disposition="replace"`.
- The playbook documents the expected-failure-then-fix loop with example error messages (missing env var, bad token).
- Removing the limits is a discrete step that updates the Pipeline Inventory row status.

**Source** — 08 §6 (sample-and-cap is what only the playbook does); 09 §6 item 2.

---

### 2. Schema contract defaults that work out of the box

**Priority** — Immediate

**Home** — skill body, design-doc template

**What it is** — Every Inventory row commits to a schema-contract posture; the plugin's defaults are `freeze` for columns, `evolve` for tables, `freeze` for data types — meaning new tables from the source are accepted, but unexpected new columns or type changes fail the load loudly. The skill explains the three postures in plain language and refuses to advance the row's status while the contract field is blank or `TBD`.

**Why we need it** — The plugin already mostly does this — schema pinning today refuses `TBD`. The Immediate-tier improvement is to lock the three default values in code and writing so a Studio user gets a working contract without thinking about it. The playbook says only about 8% of real pipelines set any contract; we want to be in the 8%, by default, on every first build.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/pinning-dlt-schema/SKILL.md` to make the `freeze / evolve / freeze` triplet the default with explicit override rationale required. Update the Pipeline Inventory template to show the three sub-values per row, not one collapsed value.

**What "done" looks like**
- The Inventory shows `columns`, `tables`, `data_type` as three separate sub-cells per row.
- The skill rejects any row that uses the default triplet without one-line rationale only when the default is *overridden*, not when it's accepted.
- The medallion-guardrails playbook cites the default in its bronze rules.

**Source** — 08 §5 item A1; 09 §5 (mandatory contract row); 06 §3 item 8 (comment every override).

---

### 3. Comment every schema override

**Priority** — Immediate

**Home** — skill body

**What it is** — Any time the assistant overrides a default — different schema contract, custom column hint, manual rename, type coercion — the line that does it gets a one-line preceding comment explaining why. No silent overrides.

**Why we need it** — Without this, override calls accumulate inside a pipeline file and become unreadable in three months. The plugin's own pattern catalogue lists this as must-do, but no skill enforces it. This is cheap discipline that pays off immediately and is in scope for a first reliable build.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md` and `plugins/vibedata-data-engineering/skills/pinning-dlt-schema/SKILL.md` to require the comment. Add a check to `plugins/vibedata-data-engineering/skills/evaluating-dlt-pipeline/SKILL.md` so the audit rejects override calls without a preceding comment.

**What "done" looks like**
- Generated pipeline files have a comment line directly above every override call.
- The evaluating-dlt-pipeline audit fails when an override has no comment.

**Source** — 06 §3 item 8, §5 item 7.

---

### 4. Make the pipeline-evaluation rules explicit

**Priority** — Immediate

**Home** — playbook, skill body

**What it is** — Two coordinated edits. First, a new playbook enumerates the audit rules: a schema contract is set on every resource; no transforms in the bronze pipeline file; each resource's write disposition matches its Inventory row; all override calls are commented; `allow_external_schedulers=True` is set on incremental resources; `max_table_nesting` is set; the attribution window is wired; the pipeline tags the git commit ID at runtime. Each rule entry names the symptom it catches and a severity. Second, the audit skill keeps only the behavioural contract: load the playbook, run every rule, emit per-rule pass/fail findings (not a summary verdict), halt with a known code on critical failures.

**Why we need it** — Today the audit is a black box — the skill says "run deterministic audit checks" with no enumeration. A reviewer reading the skill can't tell whether it catches any of the rules above. Splitting the rule list out into a playbook makes the audit reviewable, lets us extend the rule set without rewriting the skill body, and gives the rule list one canonical home that other items extend by adding rule entries (rather than asking the skill body to grow).

**Where it lives in the plugin** —
- New playbook at `plugins/vibedata-data-engineering/_shared/references/playbooks/dlt-pipeline-audit-rules.md`. Each rule entry has: name, what it checks, severity, halt code.
- Rewrite `plugins/vibedata-data-engineering/skills/evaluating-dlt-pipeline/SKILL.md` to cite the playbook and carry the behavioural contract — "run every rule in the playbook, emit per-rule findings, halt on `severity: critical`."

**What "done" looks like**
- The playbook exists, with one entry per rule and each entry carrying its severity.
- The skill cites the playbook in References, not in prose.
- The skill emits one finding per rule, even on success.
- A reviewer can see at a glance which rules ran and which didn't.
- Other items that need a new audit rule add an entry to the playbook, not to the skill body.

**Source** — 06 §5 item 2.

---

### 5. Debug-cleanup discipline

**Priority** — Immediate

**Home** — playbook, skill body

**What it is** — When the assistant debugs a failed pipeline run, it changes settings: raises log level, turns on HTTP error body printing, caps retries, adds `progress="log"`. Each change is recorded in a debug-log section of the working notes and reverted before the run is reported successful. The assistant never silently leaves debug settings in production code.

**Why we need it** — Without this, debug knobs leak into the committed pipeline file. Users open PRs full of `log_level="DEBUG"` and end up with noisy production logs and accidentally-disclosed HTTP bodies in CI artefacts. The dlt-hub workbench has this discipline already.

**Where it lives in the plugin** — Add a new playbook at `_shared/references/playbooks/debugging-dlt-pipelines.md` with the revert checklist. Reference it from `plugins/vibedata-data-engineering/skills/running-dlt-in-sandbox/SKILL.md`, the DuckDB sandbox child, and the Fabric sandbox child. The "no debug settings remain" halt rule lives in the sandbox skill bodies.

**What "done" looks like**
- The new playbook exists and is linked from each sandbox skill.
- Sandbox skills require the assistant to confirm "no debug settings remain" before marking the step done.
- The pipeline-evaluation audit rule set checks for stray debug knobs.

**Source** — 09 §6 item 3.

---

### 6. Named dev and prod destinations

**Priority** — Immediate

**Home** — skill body, playbook

**What it is** — A dlt destination is *where* the data lands — a DuckDB file, a Fabric warehouse, a Postgres database. Today the plugin's sandbox-vs-domain isolation means an interactive run goes to a sandbox and a CI run goes to the domain, but the destination name itself is implicit. We make it explicit: each pipeline declares a named destination, with `dev.secrets.toml` and `prod.secrets.toml` resolving the name to a real connection. Same pipeline file, different secrets profile, no target-conditional code.

**Why we need it** — Today there's a brittle implicit mapping between "is this a sandbox run" and "where does the data go". Making the destination an addressable name lets a user run the same pipeline file locally against DuckDB and in CI against Fabric without code changes — and prevents the surprisingly easy mistake of writing test data into the live domain. The dlt-hub workbench prescribes this pattern and pairs naturally with our sandbox model.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/scaffolding-duckdb-workspace/SKILL.md` and `plugins/vibedata-data-engineering/skills/scaffolding-fabric-workspace/SKILL.md` to create both secrets files and to declare a named destination. Update `_shared/references/playbooks/dlt-resource-conventions.md` to require the named-destination shape.

**What "done" looks like**
- Both scaffolding skills write `.dlt/dev.secrets.toml` and `.dlt/prod.secrets.toml`.
- Generated pipelines call `dlt.pipeline(destination="<named>")` not `destination=duckdb(...)` inline.
- The resource-conventions playbook documents the naming.

**Source** — 09 §6 item 5.

---

### 7. Clarify the bronze test layer

**Priority** — Immediate

**Home** — skill body

**What it is** — The plugin runs Tier 1 tests on bronze: dlt's synthetic row-ID (`_dlt_id`) is present, unique, and the row count is above zero. We make the prose explicit that this test is on the *synthetic* row-ID, not on any natural primary key. Natural-PK uniqueness belongs to the staging layer (downstream dbt tests), not bronze.

**Why we need it** — Without the clarification, an assistant reading the test-tiers skill is tempted to add natural-PK uniqueness checks at bronze, which would violate the medallion guardrails (bronze tests vendor data → flaky). The fix is a few lines of explanatory prose, not a structural change, but it stops a class of well-meaning mistakes.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/running-ingestion-data-tests/SKILL.md` to state the synthetic-vs-natural distinction. Cross-reference the medallion-guardrails playbook in the same edit.

**What "done" looks like**
- The skill's prose says "this test is on `_dlt_id`, a dlt-generated synthetic ID, not on any natural PK".
- The skill explicitly forbids natural-PK uniqueness tests at bronze.
- The medallion-guardrails playbook is cited in the skill's References section.

**Source** — 06 §4 item 1, §5 item 9.

---

## Possible regressions from plugin refactoring

These items came out of comparing the current plugin (`main`) against the older version at commit `e2a5a7b`. Each entry is content that was load-bearing in the old version, dropped during the refactor, and not recovered by the new coordinator or by any shared reference. All are Immediate priority. Verified via cross-grep against `agents/data-engineer.md` and every file in `_shared/references/`.

### 8. Structured table preview after a pipeline run

**Priority** — Immediate

**Home** — playbook, skill body

**What it is** — After every successful pipeline run, the assistant emits a Markdown preview of each loaded table using a fixed format: `df.to_markdown()` against a sparse-row selection (a `WHERE` chain over `_dlt_id`), GitHub-flavoured Markdown with no code fences around the table, `max_colwidth=60`, newlines stripped from cell values, id-shape columns excluded from the projection, and a heading line per table in the form `### <table_name>`. The user reads the preview to confirm the run did what they expected.

**Why we need it** — The old skill emitted this preview on every run and the user came to rely on it as the first signal that the load worked. The refactor dropped it, so the assistant now paraphrases or skips the preview, which buries shape regressions. The format spec is detailed enough that it belongs in a playbook; the behavioural rule "always emit, never paraphrase" is a skill-body halt.

**Where it lives in the plugin** — Add the format spec to a new playbook `_shared/references/playbooks/dlt-pipeline-build-conventions.md`. Add the behavioural rule (always emit; never paraphrase the preview) to the body of `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md`, citing the playbook.

**What "done" looks like**
- `_shared/references/playbooks/dlt-pipeline-build-conventions.md` exists and contains the table-preview format spec.
- `skills/generating-dlt-pipeline/SKILL.md` cites the playbook and requires the preview on every successful run.
- The pipeline-evaluation audit (item 4) checks that a preview block was emitted.

**Source** — old-commit `e2a5a7b` `generating-dlt-pipeline/SKILL.md` lines 19, 186–253.

---

### 9. Mixed-shape wrapper for loose-decorator connectors

**Priority** — Immediate

**Home** — playbook

**What it is** — Some upstream dlt connectors define resources with loose decorators that don't compose under `dlt.source()` cleanly. The fix is a `@dlt.source` wrapper around the connector's resources with explicit `with_args` (when the resource takes parameters) vs `with_resources` (when it doesn't). Misuse raises an opaque `AttributeError` at pipeline assembly. The old skill documented the symptom, the trap, and the wrapper template.

**Why we need it** — Without this in a lookup-able place, agents hit the AttributeError, don't recognise it, and either give up or write fragile workarounds. The refactor dropped the template entirely.

**Where it lives in the plugin** — Add the wrapper template and the `with_args` vs `with_resources` rule to `_shared/references/playbooks/dlt-pipeline-build-conventions.md` (same playbook created in item 8). Have `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md` cite it.

**What "done" looks like**
- The playbook contains the wrapper code template and the AttributeError symptom note.
- `skills/generating-dlt-pipeline/SKILL.md` cites the playbook entry.
- A grep for `with_resources` or `with_args` lands a reader on the explanation.

**Source** — old-commit `e2a5a7b` `generating-dlt-pipeline/SKILL.md` lines 119–146.

---

### 10. Foreground vs background Bash and polling rule

**Priority** — Immediate

**Home** — coordinator

**What it is** — A tool-use rule for any skill that runs shell commands: long-running commands (pipeline runs, sandbox spin-up) go in the foreground so the agent sees output streamed; short commands run inline; the agent never spawns background processes and polls them. The old `generating-dlt-pipeline` skill carried this rule, but it's not dlt-specific — it governs how every shell-running skill behaves.

**Why we need it** — Without it, the agent backgrounds a `dlt run` and then polls `ps` or `tail -f` log files, which is unreliable and floods the chat. The rule belongs once, in the coordinator, where every skill inherits it.

**Where it lives in the plugin** — Add the rule to `plugins/vibedata-data-engineering/agents/data-engineer.md` under a "shell command discipline" subsection. Have every sandbox-running and pipeline-running skill cite the coordinator section rather than restate it.

**What "done" looks like**
- `agents/data-engineer.md` contains the foreground/background rule and forbids background+poll.
- Sandbox skills cite the coordinator section in their References.
- No skill body restates the rule.

**Source** — old-commit `e2a5a7b` `generating-dlt-pipeline/SKILL.md` lines 186–202.

---

### 11. Entry-point chain between discovery and generation

**Priority** — Immediate

**Home** — skill body, design-doc template

**What it is** — The discovery skill writes an `entry_point` column to the Pipeline Inventory recording the module path or callable the generated pipeline will import. The generation skill reads it and halts with `ENTRY_POINT_MISSING` if absent. The evaluator (item 4) checks the entry point resolves. The old plugin had this chain wired across both skills; the refactor broke it by dropping the column.

**Why we need it** — Without the chain, generation either guesses the import path (wrong half the time) or hard-codes one (brittle). The discovery step is the right time to capture it because the assistant has just inspected the source's module layout.

**Where it lives in the plugin** — Add an `entry_point` column to the design-doc template (same template item 39 updates). Update `plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md` to write the column. Update `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md` to read it and halt with `ENTRY_POINT_MISSING` when blank.

**What "done" looks like**
- The Pipeline Inventory template carries an `entry_point` column.
- Discovery populates the column or halts.
- Generation halts with `ENTRY_POINT_MISSING` when the column is empty.
- The evaluator confirms the entry point imports cleanly.

**Source** — old-commit `e2a5a7b` `discovering-source-schema/SKILL.md` lines 44–66 and `generating-dlt-pipeline/SKILL.md` lines 1–67.

---

### 12. Fabric destination env-var table and snippet

**Priority** — Immediate

**Home** — playbook

**What it is** — Running a pipeline against Fabric needs `EPHEMERAL_WORKSPACE_ID`, `EPHEMERAL_LAKEHOUSE_ID`, and the canonical destination call shape `dlt.destinations.fabric(workspace_id=..., lakehouse_id=...)`. The old Fabric sandbox skill carried a table of the env vars, where Studio sets them, and the exact destination call. The refactor dropped the table and left the skill with a vague "set the environment".

**Why we need it** — Without the table, agents either invent variable names or pull connection details from the wrong place (Studio sets these per workspace; the agent shouldn't see them as static config). The detail is reference material — it belongs in a playbook.

**Where it lives in the plugin** — Add a new entry to `_shared/references/playbooks/fab-cli-cheatsheet.md` (or a sibling playbook) covering the env-var table, where Studio sets each variable, and the canonical destination call. `plugins/vibedata-data-engineering/skills/running-dlt-in-fabric-sandbox/SKILL.md` cites it.

**What "done" looks like**
- The Fabric playbook contains the env-var table and the destination snippet.
- The Fabric sandbox skill cites the playbook.
- A grep for `EPHEMERAL_WORKSPACE_ID` lands on the playbook entry.

**Source** — old-commit `e2a5a7b` Fabric sandbox skill lines 13–44.

---

### 13. `uv pip install` rule for the workspace venv

**Priority** — Immediate

**Home** — coordinator

**What it is** — All package installs into a workspace venv use `uv pip install`, not `pip install`. The old coordinator carried this rule; the refactor dropped it, so individual skills now drift between `pip` and `uv pip`.

**Why we need it** — Mixed tooling produces lockfile drift and slow installs. The rule is one line in the coordinator and every shell-running skill inherits it.

**Where it lives in the plugin** — Add the rule to `plugins/vibedata-data-engineering/agents/data-engineer.md` (same "shell command discipline" subsection as item 10).

**What "done" looks like**
- `agents/data-engineer.md` requires `uv pip install` for all workspace installs.
- No skill body restates it; skills cite the coordinator.

**Source** — old-commit `e2a5a7b` `agents/data-engineer.md` line 209.

---

### 14. YAML field-documentation shape (`source_ref:` vs synthesized)

**Priority** — Immediate

**Home** — playbook

**What it is** — The per-field YAML the documentation skill emits has a specific shape: fields the source provides carry a `source_ref:` pointing at the source's own field name; fields the pipeline synthesizes (computed columns, derived flags) omit `source_ref:` and instead carry a `derivation:` block. The old skill validated this shape and halted with `SOURCE_REF_MISSING` when a non-synthesized field lacked the key. The refactor dropped the shape spec.

**Why we need it** — Without the spec, the YAML degrades into freeform notes and the halt code can't fire. The shape is the contract between docs and the evaluator.

**Where it lives in the plugin** — Add the YAML shape to a new playbook `_shared/references/playbooks/ingestion-docs-yaml-shape.md` (or extend `_shared/references/conventions/yaml-style.md`). `plugins/vibedata-data-engineering/skills/documenting-dlt-pipelines/SKILL.md` cites it and uses it as the validation shape for the `SOURCE_REF_MISSING` halt.

**What "done" looks like**
- The playbook documents the `source_ref:` vs synthesized-field shape.
- The documentation skill cites the playbook and halts with `SOURCE_REF_MISSING` per the spec.
- The evaluator audit cross-checks the shape.

**Source** — old-commit `e2a5a7b` `documenting-dlt-pipelines/SKILL.md` lines 30–62.

---

### 15. Golden-data fenced JSON outcome block

**Priority** — Immediate

**Home** — skill body

**What it is** — After running golden-data validation, the skill emits a fenced JSON block of the shape `{"outcome": "pass|fail|skipped", "details": ...}` so the evaluator (item 4) and downstream tooling can machine-read the result. The old `validating-golden-data` skill enforced this; the refactor dropped both the shape and the emission rule.

**Why we need it** — Without the block, the evaluator falls back to substring matching on free prose, which is brittle. The JSON contract is small and belongs inside the skill body that emits it — not a shared reference.

**Where it lives in the plugin** — Add the exact JSON shape and the emission rule to the body of `plugins/vibedata-data-engineering/skills/validating-golden-data/SKILL.md`. The evaluator rule set (item 4) checks for the block.

**What "done" looks like**
- `validating-golden-data/SKILL.md` documents the JSON shape and requires emission on every run.
- The evaluator checks for a parseable fenced JSON block with the `outcome` key.
- A failed validation still emits the block (with `outcome: "fail"`).

**Source** — old-commit `e2a5a7b` `validating-golden-data` skill.

---

## Soon

### 16. `allow_external_schedulers=True` on incremental resources

**Priority** — Soon

**Home** — pattern catalogue, skill body

**What it is** — A dlt knob on `@dlt.resource` that tells dlt the resource's state is being managed by an external scheduler (Airflow, Dagster, Studio's own scheduler) and not by dlt's local state file. Without it, scheduled runs duplicate state-tracking work and can drift.

**Why we need it** — Standard on production verified sources (Zendesk, Shopify). Absence is silent — pipelines work — until a scheduled CI run starts double-tracking state. Cheap to set; expensive to debug after the fact.

**Where it lives in the plugin** — Add a pattern card to `_shared/references/patterns/dlt-patterns.md` describing the knob, when to set it, and the silent-failure mode. Reference the pattern from `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md`. The pipeline-evaluation audit (item 4) should check it.

**What "done" looks like**
- The pattern catalogue carries the card.
- Every incremental resource sets the flag by default.
- Inventory rows opt out explicitly with rationale.
- The audit catches missing values.

**Source** — 06 §3 item 1, §5 item 3.

---

### 17. `max_table_nesting=2` and `row_order` decisions

**Priority** — Soon

**Home** — pattern catalogue, design-doc template, skill body

**What it is** — Two dlt knobs at the source level. `max_table_nesting` caps how deep dlt's automatic flattening goes; without a cap, deeply nested JSON spawns child tables forever. `row_order="asc"` or `"desc"` tells dlt the source returns ordered results, so it can stop early on incremental loads. Both belong in the Inventory as explicit decisions.

**Why we need it** — Schema sprawl from deep nesting is a slow-burn problem — your warehouse fills up with `_v2`, `_v3`, `_v4` child tables and nobody notices for a quarter. `row_order` is a real optimisation with a real foot-gun: misuse it on an unordered source and dlt silently drops records.

**Where it lives in the plugin** — Add two pattern cards (one per knob) to `_shared/references/patterns/dlt-patterns.md` covering the default and the foot-gun. Add both columns to the Pipeline Inventory template. Update `plugins/vibedata-data-engineering/skills/pinning-dlt-schema/SKILL.md` to require `max_table_nesting=2` as default. Update `plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md` to capture the `row_order` decision.

**What "done" looks like**
- The catalogue has both cards.
- Inventory rows show both decisions.
- Generated sources carry both knobs.
- The audit rule set checks both.

**Source** — 06 §3 items 2–3, §5 items 4–5.

---

### 18. Backfill as a separate pipeline

**Priority** — Soon

**Home** — playbook, skill body

**What it is** — Backfilling historical data uses a distinct `pipeline_name` and `dataset_name` from production, with bounded `initial_value` and `end_value`. Production keeps its cursor; the backfill writes to its own dataset and gets unioned in the silver layer.

**Why we need it** — Sharing `pipeline_name` between production and backfill causes cursor collisions, dedup confusion, and very fun debugging. Today the plugin doesn't name backfill as a workflow, so users either don't backfill or do it dangerously. This is a "soon" not "immediate" because most first builds don't need a backfill on day one — but the moment someone wants one, the lack of a discipline document bites.

**Where it lives in the plugin** — Add a new skill at `plugins/vibedata-data-engineering/skills/running-dlt-backfill/SKILL.md` for the behavioural rule. Put the parallel month-window code template and the cursor-collision symptom into `_shared/references/playbooks/dlt-resource-conventions.md` (or a sibling backfill playbook). Skill cites playbook.

**What "done" looks like**
- New skill exists with a separate-pipeline-and-dataset rule.
- The playbook carries the parallel month-window template.
- The skill prescribes bounded `initial_value` and `end_value`.

**Source** — 08 §10 item 4; 09 §9 item 5.

---

### 19. Load-outcome staging model

**Priority** — Soon

**Home** — skill body, playbook

**What it is** — dlt writes a `_dlt_loads` table that records every load package's status. We surface that table as a standard staging model named `stg_<source>__load_outcomes` so analysts can query ingestion health in SQL without learning dlt internals.

**Why we need it** — Today the only way to check ingestion health is to read logs or run a dlt CLI command. Once a Studio user has more than one pipeline, that doesn't scale — but again, it doesn't bite on the first build, so this is "soon" not "immediate".

**Where it lives in the plugin** — Extend `plugins/vibedata-data-engineering/skills/documenting-dlt-pipelines/SKILL.md` with a load-outcomes section, or add a small new skill if the documentation skill is already heavy. Add a "Must" rule to the silver section of `_shared/references/playbooks/medallion-guardrails.md` that any silver model reading bronze filters on load-outcome success.

**What "done" looks like**
- The skill emits a `stg_<source>__load_outcomes.sql` per pipeline.
- The guardrails playbook requires the filter at silver.
- The audit checks for the filter when silver models are present.

**Source** — 08 §10 items 5 and 7; 09 §4 (playbook recommendations bullet 9).

---

### 20. Workspace dashboard handoff

**Priority** — Soon

**Home** — coordinator, skill body

**What it is** — After every successful pipeline run in the sandbox, the assistant tells the user to run `dlt pipeline <name> show` to open the dlt workspace dashboard. The dashboard renders the schema, the loaded rows, and the load history visually.

**Why we need it** — Today the only output the user gets is per-field YAML and a pass/fail verdict. The dashboard is a free win — dlt already runs it; we just have to surface the command. Helps users build intuition about what their pipeline actually produced.

**Where it lives in the plugin** — Add the handoff to `plugins/vibedata-data-engineering/skills/running-dlt-in-sandbox/SKILL.md` and to the coordinator's success report template at `plugins/vibedata-data-engineering/agents/data-engineer.md`.

**What "done" looks like**
- After a successful sandbox run, the coordinator's report includes the exact `dlt pipeline <name> show` command.
- The sandbox skill's success path mentions the dashboard.

**Source** — 09 §6 item 4, §9 item 8.

---

### 21. Reference the medallion-guardrails playbook from every dlt build skill

**Priority** — Soon

**Home** — skill body

**What it is** — The medallion-guardrails playbook is the plugin's single source of truth for layer rules — what bronze must do, what it must not do, same for silver and gold. Today only the source-profiling skill cites it; the pipeline-generation skill restates a subset of the bronze "must not" rules by hand. We replace the restatement with a reference.

**Why we need it** — Single source of truth. When a rule changes, it changes in one place. Restating rules by hand means they drift.

**Where it lives in the plugin** — Update the References section of `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md`, `pinning-dlt-schema/SKILL.md`, both sandbox skills, and `running-ingestion-data-tests/SKILL.md` to cite `_shared/references/playbooks/medallion-guardrails.md`.

**What "done" looks like**
- All listed skills cite the medallion-guardrails playbook in References.
- The pipeline-generation skill replaces hand-restated rules with a citation.

**Source** — 06 §5 item 8.

---

### 22. Tag pipeline runs with the git commit ID

**Priority** — Soon

**Home** — pattern catalogue, skill body

**What it is** — Every pipeline run records the git commit ID of the code that produced it in dlt's pipeline metadata. Lets us trace a bad row back to the exact pipeline version that loaded it.

**Why we need it** — Without it, debugging a "this row looks wrong" report devolves into git archaeology. The pattern catalogue lists it as must-do; no skill enforces it.

**Where it lives in the plugin** — Add a pattern card to `_shared/references/patterns/dlt-patterns.md` describing the commit-tag wiring. Update `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md` to emit the wiring in the generated pipeline file. Add to the pipeline-evaluation audit checklist.

**What "done" looks like**
- The catalogue carries the card.
- Generated pipelines write the commit ID into pipeline metadata at runtime.
- The audit confirms the wiring is present.

**Source** — 06 §3 item 9, §5 item 12.

---

### 23. Pipeline documentation must include cursor, cadence, owner, blast radius

**Priority** — Soon

**Home** — skill body, design-doc template

**What it is** — The documentation skill today bans "TBD" descriptions and requires per-field YAML. We extend it to require, per pipeline: cursor column, refresh cadence (how often the pipeline runs), owner (which team or user is on the hook), blast radius (what downstream models break if this pipeline breaks).

**Why we need it** — All four are listed as must-do in the pattern catalogue; none is enforced. When an incident strikes, these are the four things the on-call needs and currently has to reverse-engineer.

**Where it lives in the plugin** — Update `plugins/vibedata-data-engineering/skills/documenting-dlt-pipelines/SKILL.md` and add the four fields to the YAML template the skill emits.

**What "done" looks like**
- The YAML doc template includes the four fields.
- Missing any field halts the build.

**Source** — 06 §2 (documenting-dlt-pipelines row), §5 item 11.

---

### 24. Snapshot test for nested shapes

**Priority** — Soon

**Home** — skill body, pattern catalogue

**What it is** — A unit test type that captures a stable representation of a nested JSON record and fails if the next run produces a different shape. Complements the four canonical scenarios (happy / empty / partial-failure / cursor wiring) the unit-test skill already covers.

**Why we need it** — Nested sources (Salesforce, HubSpot) drift in subtle ways; the canonical four scenarios don't catch shape drift. The pattern is in the catalogue; the skill doesn't surface it.

**Where it lives in the plugin** — Add a pattern card to `_shared/references/patterns/dlt-patterns.md` describing when to reach for a snapshot test. Update `plugins/vibedata-data-engineering/skills/writing-dlt-unit-tests/SKILL.md` to cite the card and emit a snapshot test for resources flagged as nested.

**What "done" looks like**
- The catalogue carries the card.
- The skill describes when to use a snapshot test.
- The skill emits a snapshot test for any resource flagged as nested.

**Source** — 06 §2 (writing-dlt-unit-tests row), §5 item 15.

---

### 25. Resolve `raw_<system>` vs `src_<connection>` naming in writing

**Priority** — Soon

**Home** — playbook, skill body

**What it is** — The plugin uses `src_<connection_name>` as the bronze dataset name (e.g. `src_notion_4`). The playbook in the best-practice research folder recommends `raw_<system>` (e.g. `raw_notion`). Both are reasonable. We pick one and document the rationale where readers will see it.

**Why we need it** — Today an assistant reading both gets contradictory instructions. The plugin's choice is right for Studio's multi-connection-per-source reality (two Notion connections can't both write to `raw_notion`), but the rationale is buried.

**Where it lives in the plugin** — Update `_shared/references/playbooks/dlt-resource-conventions.md` with the explicit rebuttal. Update `/tmp/dlt-playground/docs/best_practice_research/INGESTION-PLAYBOOK.md` to flag the multi-connection collision. Add a one-line cross-reference to `plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md`.

**What "done" looks like**
- The conventions playbook explains the conflict and the choice.
- The research playbook flags the multi-connection case.
- The schema-discovery skill points readers at the rationale.

**Source** — 06 §4 item 3; 08 §10 item 3; 09 §8 conflict 1, §9 item 10.

---

### 26. `dev_mode=True` during sandbox iteration

**Priority** — Soon

**Home** — pattern catalogue, skill body

**What it is** — A dlt flag that suffixes the dataset name with a timestamp on every run, so iterative work doesn't accumulate stale state. Different from item 1 (small-sample first-run loop) — this is about ongoing iteration in the sandbox, not about the first run.

**Why we need it** — Without it, the same dataset accumulates rows across debugging iterations and the assistant ends up debugging the leftover state, not the code. Roughly 7% adoption rate in the wild according to the playbook — high foot-gun.

**Where it lives in the plugin** — Add a pattern card to `_shared/references/patterns/dlt-patterns.md` describing `dev_mode=True` for iterative sandbox use and the "remove before promotion" rule. Update `plugins/vibedata-data-engineering/skills/running-dlt-in-duckdb-sandbox/SKILL.md` and the Fabric counterpart to cite the card.

**What "done" looks like**
- The catalogue carries the card.
- Sandbox skills set `dev_mode=True` by default for interactive runs.
- The setting is removed before the pipeline is promoted out of the sandbox.

**Source** — 06 §3 item 4, §5 item 10.

---

## Deferred

### 27. Typed multi-auth credentials

**Home** — skill body

**What it is** — When a source supports multiple authentication methods (API key, OAuth, basic), we wire them as a typed union (`AuthApiKey | AuthOauth | AuthBasic`) rather than a flag-driven dict. Why deferred: most Studio sources have one auth method; this pattern matters when we add sources that don't.

**Where it lives in the plugin** — `plugins/vibedata-data-engineering/skills/pinning-dlt-schema/SKILL.md` and `generating-dlt-pipeline/SKILL.md` when adopted.

**Source** — 06 §3 item 6, §5 item 11.

---

### 28. Pydantic "is this model authoritative?" decision

**Home** — skill body

**What it is** — When a resource has a Pydantic model defined, the schema-pinning step asks whether the Pydantic model is authoritative over the dlt-inferred schema. Why deferred: requires the multi-model authoring path to exist first; today most pipelines don't use Pydantic.

**Where it lives in the plugin** — `plugins/vibedata-data-engineering/skills/pinning-dlt-schema/SKILL.md`.

**Source** — 06 §2 (pinning row), §5 item 13.

---

### 29. Schema-change allow-list PR workflow

**Home** — playbook, Studio code

**What it is** — When a `freeze` schema contract fails because the source added a column, the workflow is: load fails → engineer opens a PR adding the column to the allow-list → CI runs against staging → merge → prod unblocks. Why deferred: today the plugin handles schema-contract violations as in-session corrections through reviewer gates. The CI-mediated PR workflow is the "correct" production shape but requires a CI ingestion harness we don't have yet.

**Where it lives in the plugin** — Would touch `_shared/references/playbooks/medallion-guardrails.md` and require a new CI workflow file in Studio.

**Source** — 08 §6 conflict C4; 08 §3 (production runtime).

---

### 30. Operational-artefacts checklist (runbooks, freshness gates, drift alerts)

**Home** — playbook

**What it is** — Per-source runbook directory, freshness-gate query, schema-drift alert hook, written re-sync procedure. Why deferred: these matter when a pipeline goes to production and starts failing in interesting ways. The Immediate set targets first-run reliability; this targets long-term operability.

**Where it lives in the plugin** — A new playbook at `_shared/references/playbooks/operational-artefacts.md`, referenced from the documentation skill.

**Source** — 08 §10 item 6; 09 §4.

---

### 31. Find-a-better-connector gate

**Home** — skill body

**What it is** — Before scaffolding a custom source, the assistant checks whether a verified dlt source already exists. Why deferred: Studio sources are pre-vetted in our flow, so the gate would rarely fire. If we ever let users define custom sources directly, this becomes Immediate.

**Where it lives in the plugin** — Would be a new front-of-flow step in `plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md`.

**Source** — 09 §6 item 6.

---

### 32. Bidirectional symmetric handoffs between tracks

**Home** — coordinator

**What it is** — dlt-hub composes work as small plugins with explicit `incoming` / `outgoing` handoff declarations. Our coordinator owns everything in one linear flow. Why deferred: our scope is one internal track; the multi-plugin architecture is the right shape when we add data-quality and exploration as peers, not now.

**Where it lives in the plugin** — Structural; would touch `plugins/vibedata-data-engineering/.claude-plugin/plugin.json` and the coordinator agent.

**Source** — 09 §6 item 7, §8 conflict 5.

---

### 33. Upstream-gap TODO discipline

**Home** — skill body

**What it is** — Every workaround for a dlt or Studio-source bug carries a `TODO: remove when <repo>#<issue>` comment with a linked issue. Reviewer rejects workarounds without one. Why deferred: meaningful once the plugin has accumulated enough workarounds to need the audit trail; today it would be busywork.

**Where it lives in the plugin** — `plugins/vibedata-data-engineering/skills/evaluating-dlt-pipeline/SKILL.md` and the code reviewer's checklist.

**Source** — 09 §6 item 10.

---

### 34. Surface inventory-as-contract upstream

**Home** — playbook (external)

**What it is** — Promote the Pipeline Inventory pattern back to the best-practice research playbook so other teams can adopt it. Why deferred: this is documentation work in `docs/best_practice_research/`, not plugin work; it doesn't change what Studio users experience.

**Source** — 08 §10 item 8.

---

### 35. Surface two-stage schema-pinning gotcha upstream

**Home** — playbook (external)

**What it is** — Document in the research playbook that freezing tables at generation time raises a dlt validation error; tables can only be frozen after the first successful load. Same reason for deferral as item 34.

**Source** — 08 §10 item 9.

---

### 36. Surface fixture-replay-plus-golden upstream

**Home** — playbook (external)

**What it is** — Promote the row-exact replay with 0.01 threshold and three-run non-determinism halt to the research playbook. Same reason for deferral.

**Source** — 08 §10 item 10.

---

### 37. Surface sandbox-vs-domain isolation upstream

**Home** — playbook (external)

**What it is** — Promote the sandbox-vs-domain pattern (PR-time validation against sandbox, CI-time apply to domain) to the research playbook. Same reason for deferral.

**Source** — 08 §10 item 11.

---

### 38. Pre-build source profiling

**Priority** — Deferred

**Why deferred** — Live source profiling sounds simple but is hard in practice. A passive 100-row sample cannot answer the two highest-value questions — whether timestamps are reliably set by the source on every write, and how far back the source rewrites history — because both require mutation testing (create a record, edit it through multiple paths, observe what happens) or curated per-connector metadata. The other three dimensions (cursor wire format, server-side filter availability, tenant boundaries) *are* answerable from sampling, but each needs its own deliberate probe. Worse, the existing discovery skill explicitly forbids hitting the live source — verbatim: *"Do not connect to a source system unless the connector requires it for introspection — most verified sources expose their resource definitions statically"* (`plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md`, the Invariants section). So implementing this means relaxing a load-bearing existing rule alongside building a new skill, an unbounded scope for the first wave of fixes. Defer until either (a) a curated per-connector metadata table exists that can answer the semantic questions without sampling, or (b) the priority becomes "we keep shipping broken Marketo / HubSpot pipelines and need to stop."

**Home** — skill body, coordinator

**What it is** — Before writing any pipeline code, the assistant inspects the live source for five things: are timestamps server-side (set by the source) or client-side (set by us at fetch time); can the source rewrite or back-date a record after we already loaded it, and for how long (the *attribution window* — the time range during which a source might still mutate records we've already ingested); what wire format the cursor field uses (ISO string, Unix epoch, integer); whether the source can filter "since X" server-side; where tenant boundaries lie. The findings get written into the design document before schema pinning.

**Why we need it** — The single biggest cause of broken ingestion in real teams. A user wires up a HubSpot source today, picks `created_at` as the cursor, looks fine for two weeks, and then silently misses every record HubSpot back-dates. The plugin currently jumps from static schema introspection straight to pinning the schema contract, with no live-data check in between. This is the playbook's most-emphasised step and the workbench's `find-source` pattern in different forms.

**Where it lives in the plugin** — Future work would add a new skill at `plugins/vibedata-data-engineering/skills/profiling-source-api/SKILL.md` (sibling to `discovering-source-schema/` and `profiling-source-data/`), wire it into the design phase before `pinning-dlt-schema/`, and update the data-engineer coordinator at `plugins/vibedata-data-engineering/agents/data-engineer.md` to include it in the implementation-plan template. The existing `profiling-source-data/` skill stays as-is — it targets bronze-to-silver readiness, a different step.

**What "done" looks like**
- New skill writes a "Source Profile" subsection into `design.md` covering timestamps, attribution window, cursor wire format, server-side filter availability, tenant scoping.
- Pipeline Inventory rows cannot reach `pinned` status until the Source Profile section is filled in.
- The skill calls the live source (within sandbox limits) and records at least 100 sampled rows' worth of observations.

**Source** — 06 §5 item 1; 08 §10 item 1; 09 §9 item 1.

---

### 39. Attribution window on incremental resources

**Priority** — Deferred

**Why deferred** — This is the *wiring and enforcement* half of attribution-window discipline (require the value on every inventory row, wire it into dlt's `lag` argument, audit both). The *detection* half — figuring out how far back a given source actually rewrites records — was deferred separately as item 38 (Pre-build source profiling), because detection cannot be done from passive sampling alone and the existing discovery skill explicitly forbids live source connections. Shipping this item without a way to determine the value would force a fallback: ask the user, use curated per-connector metadata, or default to a conservative window. All three are workable but each is a substantial design decision in its own right. Defer until either (a) item 38 lands and provides authoritative values, or (b) we commit to one of the fallback approaches and that fallback gets its own scoped item.

**Home** — design-doc template, skill body

**What it is** — Every resource that uses an incremental cursor records, in the Pipeline Inventory, how far back the source can still rewrite records. The plugin requires a value: `none`, `1h`, `7d`, `30d`, or `custom`. The generated pipeline wires that value into dlt's `lag` argument on `dlt.sources.incremental(...)` so that each run also rescans the trailing window — catching late-arriving and back-dated rows.

**Why we need it** — Marketing platforms back-date events for up to 30 days; ad networks for 30 days; CRMs commonly for 7. Without the lag, the cursor advances past those edits and the warehouse copy quietly drifts. Today the plugin's resource-conventions playbook mentions this idea but no skill captures it on the Inventory and no generation step wires it through. This is one place where a silent bug is the default outcome.

**Where it lives in the plugin** — Add an `attribution_window` column to the Pipeline Inventory template (the design-doc template the plugin inherits from). Update `plugins/vibedata-data-engineering/skills/discovering-source-schema/SKILL.md` to require the column. Update `plugins/vibedata-data-engineering/skills/generating-dlt-pipeline/SKILL.md` to wire the value into `lag=`. Cross-reference from `_shared/references/playbooks/dlt-resource-conventions.md`.

**What "done" looks like**
- Pipeline Inventory rows for `merge` or incremental `append` resources cannot pass review without an `attribution_window` value.
- Generated pipelines call `dlt.sources.incremental(..., lag=...)` with the value from the row.
- Inventory rows with `none` carry a one-line rationale in the row's notes column.

**Source** — 06 §5 item 6 (mutation window wiring); 08 §10 item 2; 09 §9 item 3.

---

## Cross-cutting themes

The Immediate items concentrate on **capturing knowledge at the right time** — at intake and design, while the Studio user is right there to answer questions, rather than letting the assistant guess later. They also concentrate on **making implicit defaults explicit** — schema contract values, destination names, debug-cleanup steps, the first-run loop. A third theme is **closing the silent-bug class** — attribution windows and commented overrides exist to stop bugs that don't surface until weeks later. The Soon items shift toward **single-source-of-truth hygiene** — referencing the guardrails playbook from every build skill, documenting cursor and cadence, picking one naming convention. The Deferred items are mostly **patterns the plugin will need when its scope grows** — operational artefacts, multi-track handoffs, upstream workflow gates — none of which block today's typical user.

## What we're explicitly NOT doing now

- **Splitting the coordinator into separate ingestion / transformation / data-quality plugins.** dlt-hub's multi-plugin shape is the right long-term architecture but premature for our single-track scope. Revisit when we add a second peer track.
- **Adopting dlt-hub's paid 9,700-source context.** Studio sources are pre-vetted; the discovery problem the upstream solves doesn't exist for us.
- **Mermaid schema export.** Per-field YAML serves the same purpose and is testable; the dashboard handoff (item 20) covers the visual need.
- **dlthub managed runtime deployment.** Our sandbox-versus-domain model is a different production pattern; we don't need the upstream deployment story.
- **A vault-backed credentials path.** dlt's stock provider chain plus our existing Studio secrets handling is enough today; the vault pattern is a future operational concern.
- **Multi-connection workspace ambiguity.** Today the convention is one workspace per connection; we'll revisit the ambiguity if a user files a case where it bites.
