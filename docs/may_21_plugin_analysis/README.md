# Data-Engineering Toolkit Analysis — May 21, 2026

This is a comparison of two versions of the toolkit that the Studio app uses to automate its data work. The toolkit is a bundle of automated tasks the app calls out to: figure out what a user wants, pull data in (ingestion with dlt), and shape that data (transformation with dbt).

## What we compared

| Version | Where it lives | Internal name | Version number |
|---|---|---|---|
| **Older** | [an earlier snapshot](https://github.com/accelerate-data/vibedata-data-engineering/tree/e2a5a7bc85dc87147d70e0a1e9c1fe088864188c/plugins/vibedata-data-engineering) | `vibedata-data-engineering` | `5.8.0` |
| **Newer** | [today's main branch](https://github.com/accelerate-data/vibedata-data-engineering/tree/main/plugins/vibedata-data-engineering) | `vibedata-data-engineering-med` | `0.1.3` |

Both live in the same place inside the team's `vd-data-engineering` repository.

## What's in this folder

- [`01-old-version.md`](./01-old-version.md) — What the older toolkit contains: its automated jobs, helper scripts, and built-in startup behavior.
- [`02-new-version.md`](./02-new-version.md) — Same inventory for the newer toolkit, plus the new step-by-step plan file that drives it.
- [`03-core-differences.md`](./03-core-differences.md) — What actually changed, ordered by how much it matters.
- [`04-diagrams.md`](./04-diagrams.md) — Two flowcharts you can read side by side.

## The short version

The newer toolkit is a rewrite of *how the work flows*, not a rewrite of what it can do:

1. **The auto-start helper was removed.** The old toolkit had a small script that ran every time a session began. It pasted in classification instructions and the domain configuration so the assistant always knew where to put things. That script is gone.
2. **A large library of supporting files was removed.** Around 50 files — schema definitions, error-code lists, readiness checklists, project templates — were deleted. A smaller shared folder replaces them.
3. **Helper scripts were removed** (the small Python and bash utilities for validating notebooks and manifest files).
4. **A new file drives the work: a step-by-step plan.** Every task now lives as a row in this plan with an explicit status. Before, the assistant had to read a design document and guess what was done. Now it just reads the plan.
5. **The toolkit is now packaged as one of a family.** The name gained a `-med` suffix (for "medium") and the version was reset, hinting at "low" and "high" siblings that share the same automated jobs but offer different depth of guidance.
6. **The six-phase vocabulary was downplayed.** The phase names (Intake, Workspace, Requirements, Design, Build, Publish) still appear as labels, but the plan file decides what runs next — not a hard-coded phase order.
7. **The lineup of automated jobs is unchanged.** Same nine assistant roles, same 29 automated tasks, same filenames. All the real change is in the coordinator's instructions, the removed startup helper and library, and the new shared folder plus plan file.
