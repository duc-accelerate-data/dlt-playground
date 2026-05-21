# New Version — `main`, v0.1.3

[Source tree](https://github.com/accelerate-data/vibedata-data-engineering/tree/main/plugins/vibedata-data-engineering)

## Manifest

`.claude-plugin/plugin.json`:
- name: **`vibedata-data-engineering-med`** (renamed)
- version: **`0.1.3`** (reset from `5.8.0`)
- description: *"med variant: balanced practitioner-pattern footprint for common production work."*

The plugin is now one variant in a family (`med`), implying `low` / `high` siblings exist or are planned.

## Agents (`agents/`, 9 files)

Same 9 filenames as old version. The coordinator (`data-engineer.md`) was substantively rewritten:

- **"Six-phase" language demoted** from the agent body — still listed in the workflow contract as plain text stage names (Intake, Workspace, Requirements, Design, Build, Publish), but no longer the primary execution model.
- **New first-class artifact: `implementation-plan.md`**, generated post-design by `managing-intent-design-docs`. Each step carries:
  - `step_id`
  - `goal`
  - `skill_to_invoke`
  - `status`
  - `artifacts_touched`
  - `notes`

  The plan is the **resume source of truth** instead of the old "scan progress table in `design.md`" approach.

- **New eval-instrumentation contract**: in workspaces containing `.eval-run/` or `.opencode/`, the coordinator must `touch .skill-ran/<skill-name>` sentinels after loading each skill — used by the eval harness to verify real skills were loaded.

- **Explicit `design.md` schema**: mandatory `Model Inventory` (dbt) / `Pipeline Inventory` (dlt) sections, plus a `Gate Status` section with visible `✅` markers.

- **OpenCode fallback documented inline**: if no `Skill` tool is available, read SKILL.md from `.opencode/plugins/...` or `plugins/...`.

## Skills

Same **29 skill directories, same names**. Frontmatter tightened, e.g. `classifying-data-intents` now keys off an implementation-plan step:

> *"Use for a current implementation-plan step whose `skill_to_invoke` is `classifying-data-intents`"*

— rather than "always run at session start".

## Hooks

**Deleted entirely.** No `hooks/` directory, no `SessionStart` injection. Classification is now driven from inside the coordinator agent prompt + plan steps, not from a runtime hook.

## `lib/`

**Deleted entirely.** All contract schemas, error-code catalogues, readiness checklists, and template files are gone from the plugin.

## `scripts/`

**Deleted entirely.**

## New `_shared/` — replaces old `skills/_shared/` + `lib/templates/` + `lib/readiness/`

- `_shared/references/INDEX.md` — single discoverable index.
- `_shared/references/conventions/` (7 files) — style guides extracted from old flat refs: `git-workflow`, `logging-policy`, `model-naming`, `runtime-audit-columns`, `skill-style`, `sql-style`, `yaml-style`.
- `_shared/references/playbooks/` (15 files) — old refs reclassified as playbooks. New entries:
  - `data-test-tiers`
  - `ingestion-test-tiers`
  - `medallion-guardrails`
  - `multi-session-resume`
- `_shared/references/patterns/` **(NEW)** — `dbt-patterns.md` and `dlt-patterns.md`, explicitly tagged `variant: med`. This is the per-variant payload.
- `_shared/templates/` — 6 templates including the new `implementation-plan-template.md` and `skill-template.md`. Old per-target template trees (`duckdb/`, `fabric/`) are gone.

## Flow

```
[Startup] coordinator reads intents/ → resume from implementation-plan.md (first step ≠ done)
        │
        ▼ (fresh)
classifying-data-intents (touch .skill-ran/) → confirm work type
        ▼
managing-intent-design-docs → intent.md → design.md (Model/Pipeline Inventory + Gate Status)
        ▼
managing-intent-design-docs → emit implementation-plan.md (steps with skill_to_invoke)
        ▼
loop: read next step → load skill named by skill_to_invoke → execute → step.status = done
   ├─ ingestion track:
   │    scaffolding-* → discovering-source-schema → generating-dlt-pipeline
   │    → running-dlt-in-* → pinning-dlt-schema → ingestion-data-testing
   │    → documenting-dlt-pipelines → evaluating-dlt-pipeline
   └─ transformation track:
        scaffolding-* → applying-medallion-data-modelling → generating-dbt-model
        → running-dbt-in-* → dbt-unit-testing → documenting-dbt-models
        → publishing-dbt-contracts → evaluating-dbt-project
        ▼
reviewers dispatched per gate; verbatim JSON; ✅ markers added to design.md Gate Status
```
