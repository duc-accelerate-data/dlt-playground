# Old Version — commit `e2a5a7b`, v5.8.0

[Source tree](https://github.com/accelerate-data/vibedata-data-engineering/tree/e2a5a7bc85dc87147d70e0a1e9c1fe088864188c/plugins/vibedata-data-engineering)

## Manifest

`.claude-plugin/plugin.json`:
- name: `vibedata-data-engineering`
- version: `5.8.0`
- description leads with the **six-phase coordinator flow**: Intake → Workspace → Requirements → Design → Build → Publish.

## Agents (`agents/`, 9 files)

| File | Role |
|---|---|
| `data-engineer.md` | Primary coordinator. Runs the six-phase gated workflow, dispatches reviewers, enforces paste-verbatim verdict-JSON contract. |
| `opencode-data-engineer.md` | OpenCode runtime variant of the coordinator. |
| `code-reviewer.md` | Code gate reviewer. |
| `design-reviewer.md` | Design gate reviewer. |
| `requirements-reviewer.md` | Requirements gate reviewer. |
| `data-test-writer.md` | Writes dbt+dlt data tests. |
| `data-test-reviewer.md` | Reviews data tests. |
| `unit-test-writer.md` | Writes unit tests. |
| `unit-test-reviewer.md` | Reviews unit tests. |

## Skills (`skills/`, 29 SKILL.md files)

Intake & scoping:
- `classifying-data-intents`
- `identifying-issue-scope`
- `filing-deferred-issue`
- `managing-intent-design-docs`

Workspace scaffolding:
- `scaffolding-duckdb-workspace`
- `scaffolding-fabric-workspace`

Source discovery & modelling:
- `discovering-source-schema`
- `profiling-source-data`
- `applying-medallion-data-modelling`

Generation:
- `generating-dbt-model`
- `generating-dlt-pipeline`
- `pinning-dlt-schema`

Sandbox execution (6):
- `running-dbt-in-sandbox`
- `running-dbt-in-duckdb-sandbox`
- `running-dbt-in-fabric-sandbox`
- `running-dlt-in-sandbox`
- `running-dlt-in-duckdb-sandbox`
- `running-dlt-in-fabric-sandbox`

Fabric-specific:
- `authoring-fabric-notebook`
- `validating-fabric-notebook`

Testing:
- `dbt-unit-testing`
- `dlt-unit-testing`
- `ingestion-data-testing`
- `validating-fixture-replay`
- `validating-golden-data`

Documentation & publish:
- `documenting-dbt-models`
- `documenting-dlt-pipelines`
- `publishing-dbt-contracts`
- `evaluating-dbt-project`
- `evaluating-dlt-pipeline`

Shared refs live flat under `skills/_shared/references/`.

## Hooks (`hooks/`)

- `hooks.json` registers a `SessionStart` hook on `startup | clear | compact`.
- `session-start` bash script:
  - Inlines `classifying-data-intents/SKILL.md` into the session as `<EXTREMELY_IMPORTANT>` context.
  - If `vd-domain.yml` exists in cwd, inlines it as `<DOMAIN_CONTEXT>` so the coordinator never asks the user for destination/workspace.
  - Emits runtime-specific JSON (Cursor vs Claude vs Copilot).

## `lib/` — runtime contracts and lookup tables

- `contracts/*.schema.json` — JSON schemas: `artifact-evidence`, `data-test-recommendation`, `readiness`, `reviewer-verdict`, `scaffold-result`, `test-spec`.
- `error-codes/*.md` — per-skill error-code catalogues (18 files).
- `readiness/*.md` — gate-readiness checklists: `design`, `build`, `golden`, `profile`, `publish`, `test-gen`.
- `templates/{_shared, duckdb, fabric}/` — workspace scaffolding: dbt project / profiles / sources, dlt `pipeline.py` + `config.toml`, Fabric notebook `.ipynb` + `.platform`.

## `scripts/`

Bash + Python:
- `author-fabric-notebook.sh`
- `validate-fabric-notebook.sh`
- `check_plugin_version_bump.py`
- `validate_plugin_manifests.py`

## Flow

```
SessionStart hook ──► injects classifying-data-intents + vd-domain.yml
        │
        ▼
[Phase 0 Intake]       classifying-data-intents → identifying-issue-scope?
                          (mixed/ambiguous → filing-deferred-issue or AskUserQuestion)
        ▼
[Phase 1 Workspace]    scaffolding-{duckdb | fabric}-workspace
        ▼
[Phase 2 Requirements] managing-intent-design-docs (intent.md) → requirements-reviewer → user "approved"
        ▼
[Phase 3 Design]       managing-intent-design-docs (design.md) → design-reviewer
        ▼
[Phase 4 Build]
   ├─ ingestion:      discovering-source-schema → profiling-source-data → generating-dlt-pipeline
   │                  → running-dlt-in-* → pinning-dlt-schema → ingestion-data-testing
   └─ transformation: applying-medallion-data-modelling → generating-dbt-model
                      → running-dbt-in-* → dbt-unit-testing
   reviewers: unit-test-writer/reviewer, data-test-writer/reviewer, code-reviewer
        ▼
[Phase 5 Publish]      documenting-{dbt-models | dlt-pipelines} → publishing-dbt-contracts
                       → evaluating-{dbt-project | dlt-pipeline}
```
