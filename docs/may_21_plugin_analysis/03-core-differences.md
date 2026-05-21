# Core Differences — Ordered by Impact

## 1. Hooks removed

The `SessionStart` bash hook that auto-injected `classifying-data-intents` + `vd-domain.yml` is **gone**. Classification now flows through the coordinator's startup logic and the new implementation-plan instead of runtime context injection.

**Implication for Studio:** anything that relied on `vd-domain.yml` being auto-loaded must inject domain context another way — likely through the OpenHands adapter prompt.

## 2. `lib/` removed (~50 files)

Deleted from the plugin:
- All JSON-schema contracts (`reviewer-verdict.schema.json`, `readiness.schema.json`, `artifact-evidence`, etc.)
- The 18 per-skill error-code catalogues
- The 6 readiness checklists
- The entire `templates/{duckdb, fabric}/` scaffolding tree

Replaced by a slimmer `_shared/references/` (conventions + playbooks + patterns) and `_shared/templates/` (6 generic templates).

The plugin no longer ships per-target scaffolding files — those presumably move into the `scaffolding-*-workspace` skills themselves or onto the host runtime.

## 3. `scripts/` removed

Fabric-notebook bash helpers and Python manifest-validation scripts are gone. Manifest validation likely moved to repo-level CI.

## 4. New first-class artifact: `implementation-plan.md`

**Biggest runtime shift.** Workflow tracking moved from "phase tables embedded in `design.md`" to a separate plan file with explicit step status.

Resume semantics:
- **Old:** scan `design.md` progress markers, infer current phase.
- **New:** read `implementation-plan.md`, find first step where `status != done`.

## 5. Plugin repackaged as a variant

| Field | Old | New |
|---|---|---|
| name | `vibedata-data-engineering` | `vibedata-data-engineering-med` |
| version | `5.8.0` | `0.1.3` |

The new `_shared/references/patterns/{dbt,dlt}-patterns.md` files carry an explicit `variant: med` tag, signaling a family of variants (low/med/high) sharing skills + agents but differing in pattern depth.

## 6. Six-phase vocabulary demoted

Old description and agent prose led with "six-phase gated workflow." New description doesn't mention phases at all. The coordinator's "Workflow Contract" still lists the same six stage names, but treats them as user-visible labels — execution order is governed by the implementation-plan, not by hard phase numbers.

## 7. Eval instrumentation baked in

Coordinator now writes `.skill-ran/<skill>` sentinels when `.eval-run/` or `.opencode/` is present, replacing inferential eval probing.

## 8. Design-doc schema hardened

`design.md` must now include exactly-named sections:
- `Model Inventory` (dbt) / `Pipeline Inventory` (dlt)
- `Gate Status` with `✅` markers

Old version was looser on doc structure.

## 9. Agents and skills unchanged in name and count

- 9 agents (same filenames including `opencode-data-engineer.md`)
- 29 skills (same names)

All structural change concentrates in: coordinator prompt rewrite, manifest rebrand, hooks removal, lib removal, and the new `_shared/` + implementation-plan artifact.

---

## Open questions

- Where did the deleted `lib/contracts/*.schema.json` validation move to? The reviewer-verdict JSON shape is still mandated by coordinator prose, but no schema file ships with the plugin anymore. Possibilities: inlined into individual SKILL.md files, enforced by host code in Studio, or dropped entirely.
- Are the `low` / `high` variant siblings already shipped elsewhere, or just planned?
