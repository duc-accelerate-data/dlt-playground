# `vibedata-data-engineering` Plugin Analysis — May 21, 2026

Comparison of two versions of the `vibedata-data-engineering` Claude Code plugin used by the Studio app to drive intent classification + dlt ingestion + dbt transformation through its OpenHands runtime.

## Sources

| Version | Ref | Manifest name | Version |
|---|---|---|---|
| **Old** | [`e2a5a7bc`](https://github.com/accelerate-data/vibedata-data-engineering/tree/e2a5a7bc85dc87147d70e0a1e9c1fe088864188c/plugins/vibedata-data-engineering) | `vibedata-data-engineering` | `5.8.0` |
| **New** | [`main`](https://github.com/accelerate-data/vibedata-data-engineering/tree/main/plugins/vibedata-data-engineering) | `vibedata-data-engineering-med` | `0.1.3` |

Both live at `plugins/vibedata-data-engineering/` inside `accelerate-data/vd-data-engineering`.

## Contents

- [`01-old-version.md`](./01-old-version.md) — Old (`e2a5a7b`, v5.8.0): agents, skills, hooks, lib, scripts, and flow diagram.
- [`02-new-version.md`](./02-new-version.md) — New (`main`, v0.1.3): same inventory + the new `implementation-plan.md` runtime model.
- [`03-core-differences.md`](./03-core-differences.md) — Diff focused on architectural shifts, ordered by impact.
- [`04-diagrams.md`](./04-diagrams.md) — Side-by-side Mermaid flowcharts.

## TL;DR

The new version is a **runtime model rewrite**, not a feature change:

1. **Hooks deleted** — `SessionStart` bash hook that injected classification + `vd-domain.yml` is gone.
2. **`lib/` deleted** — ~50 files (JSON-schema contracts, error-code catalogues, readiness checklists, per-target templates) removed; replaced by a slimmer `_shared/`.
3. **`scripts/` deleted.**
4. **New artifact: `implementation-plan.md`** — explicit per-step status ledger replaces inferred progress tracking in `design.md`. This is the biggest runtime shift.
5. **Plugin repackaged as a variant** — name suffixed `-med`, version reset `5.8.0` → `0.1.3`. Signals a planned low/med/high family sharing skills+agents.
6. **Six-phase vocabulary demoted** — phase names survive as labels; execution order is now plan-driven.
7. **Agents (9) and skills (29) unchanged in count and naming.** All structural change concentrates in the coordinator prompt, hooks/lib removal, and the new `_shared/` + plan artifact.
