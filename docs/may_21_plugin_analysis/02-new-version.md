# Newer Version — `main`, version 0.1.3

[Source tree](https://github.com/accelerate-data/vibedata-data-engineering/tree/main/plugins/vibedata-data-engineering)

## What the toolkit says about itself

The manifest (`.claude-plugin/plugin.json`) shows two notable changes:

- The name gained a `-med` suffix: **`vibedata-data-engineering-med`**.
- The version was reset from `5.8.0` to **`0.1.3`**.
- The description now reads: *"med variant: balanced practitioner-pattern footprint for common production work."*

The toolkit is being packaged as one of a family. "Low" and "high" siblings probably exist or are planned.

## Assistant roles

Same nine role files as before, with the same filenames. The coordinator role (the data engineer) was substantially rewritten:

- **The "six-phase" framing was demoted** in the body of the coordinator's instructions. The same six stage names still appear in a workflow contract as plain labels, but they are no longer the main thing driving execution.

- **A new central artefact: a step-by-step plan file** (`implementation-plan.md`), produced right after the design step. Every step in the plan has:
  - an ID,
  - a goal,
  - the name of the automated task that should run,
  - a status,
  - the artefacts it touches,
  - free-text notes.

  The plan is now the **single place the coordinator looks to figure out where it left off**. Before, it had to scan progress markers buried in the design document.

- **A new contract for the eval harness.** In workspaces that include an evaluation marker folder, the coordinator must drop a small empty marker file every time it loads a task. The evaluation system can then check that the right tasks actually fired.

- **The design document has a stricter shape.** It must include a literally-named section (`Model Inventory` for dbt work or `Pipeline Inventory` for dlt work) and a `Gate Status` section with visible checkmarks.

- **A fallback for environments that lack the normal task-loading mechanism** is documented inline: read the task's instruction file directly from a known path.

## Automated tasks

Same 29 task folders, same names. Their headers (the brief descriptions that decide when they fire) were tightened. For example, the classification task now says it should run when the current plan step asks for it — not "always at the start of every session" as before.

## Auto-start helper

**Removed completely.** No startup script, no auto-pasted context. Classification is now invoked from inside the coordinator's instructions and through plan steps, instead of being injected by a runtime hook.

## Supporting library

**Removed completely.** All the contract schemas, error-code catalogues, readiness checklists, and project templates are gone from the toolkit.

## Helper scripts

**Removed completely.**

## New shared folder

The new `_shared/` folder replaces both the old shared references and the deleted library:

- An index file at the top makes the contents discoverable.
- A `conventions/` folder collects seven style guides (git workflow, logging, model naming, runtime audit columns, instruction-file style, SQL style, YAML style).
- A `playbooks/` folder collects fifteen longer how-to documents. New entries include test-tier definitions for both data tests and ingestion tests, medallion guardrails, and multi-session resume rules.
- A **new** `patterns/` folder with two files (one for dbt patterns, one for dlt patterns). These are tagged `variant: med` and are the per-variant payload — what differs between the "low", "med", and "high" toolkits.
- A `templates/` folder with six templates, including a template for the new step-by-step plan file and a template for new automated tasks. The old per-target template trees are gone.

## How it all flows

```
[Startup] coordinator looks at the intents folder → resumes from the
          first step in the plan whose status is not "done"
        │
        ▼ (if there is no plan yet)
classify the user's request (drop the task-ran marker) → confirm work type
        ▼
manage design docs → write intent.md → write design.md
                                       (with Model/Pipeline Inventory + Gate Status)
        ▼
manage design docs → emit the step-by-step plan
        ▼
loop: read next step → load the task it names → run it → mark step done
   ├─ ingestion track:
   │    set up workspace → discover schema → generate dlt pipeline
   │    → run in sandbox → pin schema → run ingestion tests
   │    → document the pipeline → evaluate the pipeline
   └─ transformation track:
        set up workspace → apply medallion modelling → generate dbt model
        → run in sandbox → run dbt unit tests → document the models
        → publish dbt contracts → evaluate the dbt project
        ▼
reviewers run at each gate; their structured verdict is pasted verbatim;
checkmarks are added to design.md's Gate Status section
```
