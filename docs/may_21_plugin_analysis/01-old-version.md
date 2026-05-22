# Older Version — snapshot `e2a5a7b`, version 5.8.0

[Source tree](https://github.com/accelerate-data/vibedata-data-engineering/tree/e2a5a7bc85dc87147d70e0a1e9c1fe088864188c/plugins/vibedata-data-engineering)

## What the plugin says about itself

The manifest file (`.claude-plugin/plugin.json`) names the plugin `vibedata-data-engineering` at version `5.8.0`. Its description leads with the **six-phase coordinator flow**: Intake → Workspace → Requirements → Design → Build → Publish. That ordering is the headline feature.

## Assistant roles (9 of them)

These are the specialised assistant prompts the plugin ships with.

| Role | What it does |
|---|---|
| Data engineer (coordinator) | The lead. Runs the six-phase flow, calls in reviewers, and pastes their pass/fail verdicts in a strict structured format. |
| Data engineer (OpenCode variant) | The same coordinator, adapted to run under a different host environment. |
| Code reviewer | Reviews code at the code gate. |
| Design reviewer | Reviews designs at the design gate. |
| Requirements reviewer | Reviews requirements at the requirements gate. |
| Data-test writer | Writes data-quality tests (for dbt and dlt). |
| Data-test reviewer | Reviews those data-quality tests. |
| Unit-test writer | Writes unit tests. |
| Unit-test reviewer | Reviews unit tests. |

## Automated tasks (29 of them)

Each task is a small instruction file the coordinator can call. Grouped by what they do:

**Intake and scoping**
- Classify what the user is asking for (a "data intent").
- Identify the scope of an issue.
- File anything out of scope as a deferred issue.
- Maintain the intent's design documents.

**Workspace setup**
- Set up a DuckDB-based workspace.
- Set up a Microsoft Fabric workspace.

**Source discovery and modelling**
- Discover what a data source contains (its schema).
- Profile the data inside a source.
- Apply medallion modelling (bronze/silver/gold layering).

**Code generation**
- Generate a dbt model.
- Generate a dlt ingestion pipeline.
- Pin the schema of a dlt pipeline (lock it down).

**Running things in a sandbox** (six tasks: a dispatcher plus four target-specific runners for dbt and dlt against DuckDB and Fabric).

**Fabric-specific**
- Author a Fabric notebook.
- Validate a Fabric notebook.

**Testing**
- Unit tests for dbt and for dlt.
- Data-quality tests for ingestion.
- Replay a recorded fixture and check the result.
- Compare against golden (known-good) data.

**Documentation and publish**
- Document dbt models and dlt pipelines.
- Publish dbt data contracts.
- Evaluate the dbt project and the dlt pipeline.

A shared `references` folder under the automated-tasks directory holds reference material the tasks can link to.

## The auto-start helper

The plugin registers a small script that runs whenever a new session begins (and on reset or compact). The script:

- Pastes the classification instructions straight into the session as high-priority context.
- If the current folder has a domain configuration file (`vd-domain.yml`), pastes that in too — so the coordinator never has to ask the user where to send the data.
- Emits the right JSON shape for whichever host environment is in use.

## The supporting library

A `lib/` folder ships a lot of supporting material:

- **Contracts** — JSON schema files that define the structure of various artefacts (reviewer verdicts, readiness reports, test specs, and so on).
- **Error-code catalogues** — one Markdown file per automated task, listing the named errors that task can raise (18 files).
- **Readiness checklists** — six files, one per quality gate (design, build, golden-data check, profiling, publishing, test generation).
- **Templates** — starter files for new workspaces: dbt project layout, profiles, sources, a dlt pipeline file with its config, a Fabric notebook, organised under per-target folders.

## Helper scripts

A small `scripts/` folder with bash and Python utilities for authoring and validating Fabric notebooks, and for checking that the plugin's own manifest files are valid and properly version-bumped.

## How it all flows

```
Auto-start helper ──► pastes in classification instructions + domain config
        │
        ▼
[Phase 0 Intake]       classify the user's request → identify scope?
                       (if mixed or ambiguous, file a deferred issue or ask the user)
        ▼
[Phase 1 Workspace]    scaffold a DuckDB or Fabric workspace
        ▼
[Phase 2 Requirements] write intent.md → requirements reviewer → wait for user "approved"
        ▼
[Phase 3 Design]       write design.md → design reviewer
        ▼
[Phase 4 Build]
   ├─ ingestion:        discover schema → profile source → generate dlt pipeline
   │                    → run in sandbox → pin schema → run ingestion data tests
   └─ transformation:   apply medallion modelling → generate dbt model
                        → run in sandbox → run dbt unit tests
   plus: unit-test writer/reviewer, data-test writer/reviewer, code reviewer
        ▼
[Phase 5 Publish]      document dbt models + dlt pipelines → publish dbt contracts
                       → evaluate the dbt project and the dlt pipeline
```
