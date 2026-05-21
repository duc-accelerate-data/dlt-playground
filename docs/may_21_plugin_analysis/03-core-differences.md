# What Actually Changed — ordered by how much it matters

## 1. The auto-start helper is gone

The startup script that used to paste classification instructions and the domain configuration into every new session has been removed. Classification now happens through the coordinator's own instructions and through plan steps — not through runtime injection.

**What this means for Studio:** anything that relied on the domain configuration being automatically loaded must now feed that context in some other way — most likely through the prompt that Studio sends to its runtime.

## 2. The supporting library is gone (about 50 files)

Deleted from the toolkit:
- All JSON schema definitions (reviewer verdicts, readiness reports, test specs, and others).
- The 18 per-task error-code catalogues.
- The six readiness checklists for each quality gate.
- The entire per-target template tree for DuckDB and Fabric workspaces.

In their place: a slimmer shared folder with conventions, playbooks, and patterns, plus a small set of generic templates.

The toolkit no longer ships per-target starter files. Those have presumably moved into the workspace-setup tasks themselves, or onto the host environment that runs the toolkit.

## 3. Helper scripts are gone

The bash and Python utilities for Fabric notebooks and manifest validation are gone. Manifest validation has probably moved to the repository's CI workflows.

## 4. A new central artefact: the step-by-step plan

**This is the biggest change in how the toolkit runs.** Work tracking moved from "phase tables embedded in the design doc" to a separate plan file with explicit per-step status.

How "resume from where I left off" works:
- **Before:** scan progress markers in the design document, then guess the current phase.
- **Now:** read the plan, find the first step whose status is not "done".

## 5. The toolkit is now packaged as a variant

| Field | Older | Newer |
|---|---|---|
| Name | `vibedata-data-engineering` | `vibedata-data-engineering-med` |
| Version | `5.8.0` | `0.1.3` |

The two new pattern files (one for dbt, one for dlt) carry an explicit `variant: med` tag. The toolkit is being set up as a family — low, medium, high — that share the same automated tasks and assistant roles but differ in how deep the patterns guidance goes.

## 6. The "six phases" idea was demoted

The old description and the coordinator's prose led with "six-phase gated workflow". The new description doesn't mention phases at all. The same six stage names still appear in the coordinator's workflow contract, but only as user-visible labels. The order in which work happens is now driven by the step-by-step plan, not by hard-coded phase numbers.

## 7. Evaluation instrumentation is built in

The coordinator now drops a small marker file every time it loads a task, but only when an evaluation workspace is present. That replaces the earlier need to infer from indirect signals whether the right task fired.

## 8. The design document has a stricter shape

The design doc must now include sections with exact, literal names:
- `Model Inventory` (for dbt work) or `Pipeline Inventory` (for dlt work).
- `Gate Status` with checkmarks against each gate.

The older toolkit was looser about document structure.

## 9. Assistant roles and automated tasks are unchanged in name and count

- Same 9 roles, same filenames.
- Same 29 tasks, same names.

All the structural change is concentrated in: the coordinator's rewritten prompt, the rebranded manifest, the removed startup helper, the removed library, and the new shared folder plus plan file.

---

## Open questions

- Where did the deleted contract schemas go? The reviewer-verdict structure is still required by the coordinator's prose, but no schema file ships with the toolkit anymore. Three possibilities: the requirement was inlined into each task's instructions, enforced by Studio's own code, or quietly dropped.
- Are the "low" and "high" sibling variants already shipped somewhere, or just planned?
