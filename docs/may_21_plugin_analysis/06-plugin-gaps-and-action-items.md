# Plugin dlt Skills — Gap and Conflict Audit

Audit of the 16 dlt-focused skills in the vibedata-data-engineering plugin against the joint baseline of (a) `docs/best_practice_research/` and (b) the plugin's own `dlt-patterns.md` + playbooks.

---

## 1. Audit method

For each skill I read its `SKILL.md` (description, invariants, references, procedure, output contract) from `plugins/vibedata-data-engineering/skills/<skill>/SKILL.md` on `main`. I compared the skill's stated invariants and references to (a) what the research baseline identifies as canonical for that step in the ingestion lifecycle and (b) what the plugin's own `dlt-patterns.md` flags as must-do or non-obvious for that step. The audit looks for: missing references to baseline patterns, invariants that contradict the baseline, and operational concerns the skill should enforce but doesn't.

Notable methodological limit: I only read `SKILL.md` for each skill, not its sibling resources (scripts, templates, sub-instructions). Where a skill's `SKILL.md` is sparse, the gap may already be filled by an unread companion file. Flagged inline where relevant.

---

## 2. Per-skill findings

| Skill | Aligned with baseline? | Notable gap or conflict | Severity |
|---|---|---|---|
| `classifying-data-intents` | Yes | Routing concern, not a dlt-technical concern. No baseline conflict. | low |
| `discovering-source-schema` | Mostly | References `dlt-patterns.md` and `dlt-resource-conventions.md`. Does not require profiling `max_table_nesting`, polymorphic field handling, or rate-limit discovery. Inventory row contract does not capture `lag`/lookback window — research treats this as a phase-3 profiling decision. | med |
| `profiling-source-data` | Yes (transform side) | Skill is for *transformation* intents (profiling bronze readiness for silver), not *ingestion* profiling. Plugin has **no skill** that profiles the upstream source pre-ingestion the way research's phase 3 prescribes (server-side vs client-side timestamps, mutation window, cursor field type, server-side filter availability, tenant boundaries). | high |
| `generating-dlt-pipeline` | Mostly | Strong invariants on `tables:freeze` gotcha, no transforms in bronze, verified-source non-wrapping. **Missing**: no invariant requiring `allow_external_schedulers=True`, `max_table_nesting=2`, or `row_order` consideration; no requirement to set `lag` from the discovered mutation window; no requirement to use typed `@configspec Union` when source has multi-auth. References `dlt-patterns.md` but doesn't pin which patterns must be applied. | high |
| `pinning-dlt-schema` | Yes | Correctly defers `tables:freeze` to post-first-load. Forbids `discard_row` without rationale. **Minor gap**: doesn't require Pydantic model authority decision (`is_authoritative_model`) even though `dlt-patterns.md` lists it as must-do. | med |
| `running-dlt-in-sandbox` | Yes | Pure dispatcher, no technical content. Correctly delegates. | low |
| `running-dlt-in-duckdb-sandbox` | Yes | Strong on sandbox-vs-domain separation. References only `git-workflow.md` — does not reference `dlt-patterns.md`, so cost-guard / parallelism / file-rotation patterns are not surfaced during sandbox iteration. | med |
| `running-dlt-in-fabric-sandbox` | Yes | Same shape as DuckDB sandbox; correct on 401/credentials handling. Same pattern-reference gap. | med |
| `ingestion-data-testing` | Yes | Tier 1 (`_dlt_id` non-null + unique) mandatory, defers business rules to dbt — matches baseline. **Possible conflict**: research places PK uniqueness on staging not bronze. Plugin's bronze test is on the synthetic `_dlt_id` so this is actually defensible, but the skill prose doesn't make the distinction explicit. | low |
| `dlt-unit-testing` | Yes | Four canonical scenarios (happy / empty / partial-failure / cursor wiring) match `dlt-patterns.md`'s testing cluster. **Minor gap**: doesn't require snapshot tests (`syrupy`) for nested shapes despite the pattern being in the catalogue. | low |
| `documenting-dlt-pipelines` | Yes | Forbids `description: "TBD"`, requires control-column documentation. **Gap**: doesn't require documenting cursor column / refresh cadence / blast radius / owner per pattern `dlt-define-resource-grain-explicitly-in-the-docstring` and `dlt-document-the-blast-radius-per-pipeline`. | med |
| `evaluating-dlt-pipeline` | Partially | Procedure is generic ("run deterministic audit checks"). `SKILL.md` does not enumerate which rules the audit runs. **Gap**: cannot tell whether the audit checks for `allow_external_schedulers`, `schema_contract` shape, `max_table_nesting`, `apply_hints` comments, etc. The rule set is opaque from `SKILL.md` alone. | high |
| `scaffolding-duckdb-workspace` | Yes | Correctly forbids editing `.dlt/config.toml` / `.dlt/secrets.toml`; requires `dbt debug` green. No baseline conflict. | low |
| `scaffolding-fabric-workspace` | Yes | Same shape; correct on 401 escalation and Spark cold-start. | low |
| `validating-fixture-replay` | Yes | Threshold default 0.01; halt-on-mismatch; non-determinism detection (3 runs differ → halt) is a research-aligned safety. | low |
| `validating-golden-data` | Yes | Row-exact replay with strict threshold matches research's contract-based testing posture. | low |

---

## 3. Cross-cutting gaps

Patterns mentioned in `dlt-patterns.md` or the research baseline that no audited skill enforces or references:

1. **`allow_external_schedulers=True` on incrementals** — research's five-rule list, also present in real verified sources (Zendesk, Shopify). **Not referenced** by `generating-dlt-pipeline`, `pinning-dlt-schema`, `discovering-source-schema`. Not even present in the plugin's own `dlt-patterns.md` catalogue.
2. **`row_order="asc"|"desc"` decision** — research treats as canonical; plugin pattern catalogue and all skills are silent.
3. **`max_table_nesting=2` source-level hint** — research/01 calls it canonical defense against schema sprawl. Plugin's `dlt-avoid-deep-nesting-at-the-api-boundary` is in the catalogue but is API-side. The dlt knob is not surfaced in any skill.
4. **`dev_mode=True` during iteration** — referenced nowhere. `running-dlt-in-duckdb-sandbox` would be the natural home.
5. **`lag` / lookback window from profiled mutation window** — `dlt-late-arriving-records-configure-a-lookback-window` is in `dlt-patterns.md`, but no skill enforces that `discovering-source-schema` capture the mutation window or that `generating-dlt-pipeline` wire `lag` from it.
6. **Typed `@configspec` multi-auth union** — research's recommended pattern for multi-auth sources. Not referenced by any skill; not in the pattern catalogue.
7. **Pydantic `is_authoritative_model` decision** — `dlt-pydantic-validation-at-the-resource-boundary` is a "must-do" pattern in `dlt-patterns.md`, but `pinning-dlt-schema` doesn't require the decision and `generating-dlt-pipeline` doesn't require wiring.
8. **`apply_hints` comment requirement** — `dlt-comment-every-apply-hints-call` is must-do in the catalogue, but neither `pinning-dlt-schema` nor `generating-dlt-pipeline` invariants enforce a comment per call.
9. **`tag pipeline runs with git_sha`** — must-do pattern; not referenced by any skill.
10. **Pre-source-profile of mutation window / server-side timestamps / cursor type** — research phase 3. Plugin's `profiling-source-data` skill is for the *bronze-to-silver* readiness check, not the upstream-source profiling. There is no skill that fills this slot.
11. **`evaluating-dlt-pipeline` audit rule list is opaque** — the skill says "run deterministic audit checks" without enumerating them in `SKILL.md`. Whether it catches the gaps above is unverifiable from the public skill content.
12. **No skill references `medallion-guardrails.md`** in the dlt cluster except implicitly through the bronze "must not transform" invariant. The guardrails are strong rules but only `profiling-source-data` cites them — `generating-dlt-pipeline` reproduces a subset by hand instead of referencing the canonical source.

---

## 4. Cross-cutting conflicts

Places where a skill's instructions contradict the patterns doc or the research:

1. **`ingestion-data-testing` runs PK tests at bronze, research puts them at staging.** Defensible — plugin's Tier 1 is on synthetic `_dlt_id`, not on a natural PK — but the skill prose doesn't say "this is `_dlt_id`-only; natural-PK uniqueness is a staging-layer dbt test." An agent reading the skill may add natural-PK uniqueness tests at bronze, which violates `medallion-guardrails.md` ("bronze tests should not assert business rules"). Recommend tightening prose.
2. **`generating-dlt-pipeline` says "do not commit Python without YAML (or vice versa)"**, but `pinning-dlt-schema` writes the skeleton+contract and `generating-dlt-pipeline` writes the body. The ordering means a brief intermediate state where Python exists without per-resource YAML. Not a real conflict but the invariant phrasing is loose. Low severity.
3. **`dlt-resource-conventions.md` retires `raw_<source_system>` naming in favor of `src_<connection_name>`** — research recommends `raw_<system>`. Deliberate divergence by the plugin (justified by multi-connection collisions), but the rationale is buried in the playbook. An agent migrating an existing dlt project from elsewhere will not know to rename. Worth a one-line callout in `discovering-source-schema` or `scaffolding-duckdb-workspace`.
4. **`generating-dlt-pipeline` invariant: "Do not write per-resource files for a verified source — `.with_resources()` is sufficient."** Research/01 shows the verified-sources project itself uses per-resource files internally. Plugin's rule is about the *consumer* project (don't fork the verified source's per-resource layout) — correct intent, but the prose risks being misread as forbidding per-resource organization for *custom* sources too. Recommend clarifying.

---

## 5. Action items

Prioritized.

### P0 — should-fix blockers

1. **Add a pre-ingestion source-profiling skill (or expand `discovering-source-schema`)**
   - Skill(s): new `profiling-source-api` or expanded `discovering-source-schema`.
   - Change: introspection must capture server-side-vs-client-side timestamp distinction, mutation window, cursor field type, server-side filter availability, tenant boundary. Record these on the Pipeline Inventory row alongside `schema_contract`.
   - Why: research's `INGESTION-PLAYBOOK.md` phase 3 names this as the single most-skipped step that "burns weeks". Plugin currently has zero coverage of upstream-source profiling. The `profiling-source-data` skill is for bronze→silver readiness and explicitly refuses the upstream-source role.
   - Priority: **P0**.

2. **Enumerate `evaluating-dlt-pipeline`'s audit rules in `SKILL.md`**
   - Skill: `evaluating-dlt-pipeline`.
   - Change: list the deterministic checks the audit runs (schema_contract present, no transforms in pipeline file, write_disposition matches Inventory, `apply_hints` calls have comments, etc.). Without this enumeration the skill is unverifiable.
   - Why: opaque audit rules make the skill un-auditable and prevent contributors from extending it deliberately. Research and the plugin's own `dlt-patterns.md` both treat enumerated rules as a quality signal.
   - Priority: **P0**.

### P1 — should-fix

3. **Add `allow_external_schedulers=True` to `generating-dlt-pipeline` invariants**
   - Skill: `generating-dlt-pipeline`.
   - Change: require incremental resources to set `allow_external_schedulers=True` unless the Inventory row explicitly opts out. Add to the pattern catalogue too.
   - Why: research/01 names this as standard on production verified sources (Zendesk, Shopify); research/02 calls absence "duplicating state mechanisms unnecessarily" with Airflow/Dagster. Plugin is silent.
   - Priority: **P1**.

4. **Add `row_order` decision to the Pipeline Inventory and `generating-dlt-pipeline`**
   - Skill(s): `discovering-source-schema` (capture), `generating-dlt-pipeline` (wire).
   - Change: each Inventory row records "source-ordered? Y/N"; if Y, the resource sets `row_order="asc"` and the unit test covers early-break behavior; if N, document why explicitly.
   - Why: research and dlt docs both flag this as a real optimization with a real foot-gun. Plugin pattern catalogue and skills are both silent.
   - Priority: **P1**.

5. **Add `max_table_nesting=2` (or explicit decision) to `pinning-dlt-schema`**
   - Skill: `pinning-dlt-schema`.
   - Change: each `@dlt.source` decorator gets `max_table_nesting=2` by default; deeper nesting is an explicit Inventory decision with rationale.
   - Why: research/01 canonical defense against schema sprawl; observed in real verified sources.
   - Priority: **P1**.

6. **Add `lag` capture + wire**
   - Skills: `discovering-source-schema` (capture mutation window in Inventory), `generating-dlt-pipeline` (set `lag` on `dlt.sources.incremental(...)`).
   - Change: Pipeline Inventory grows a `lag_seconds` column derived from upstream mutation window; the generated pipeline reads it.
   - Why: `dlt-late-arriving-records-configure-a-lookback-window` is must-do in the plugin's own pattern catalogue but no skill operationalizes it.
   - Priority: **P1**.

7. **Add `apply_hints` comment invariant**
   - Skill: `generating-dlt-pipeline` and `pinning-dlt-schema`.
   - Change: every `apply_hints(...)` call must be preceded by a one-line comment explaining the override.
   - Why: `dlt-comment-every-apply-hints-call` is must-do in the catalogue.
   - Priority: **P1**.

8. **Reference `medallion-guardrails.md` from every dlt-build skill**
   - Skills: `generating-dlt-pipeline`, `pinning-dlt-schema`, `running-dlt-in-duckdb-sandbox`, `running-dlt-in-fabric-sandbox`, `ingestion-data-testing`.
   - Change: add `_shared/references/playbooks/medallion-guardrails.md` to References; cite Bronze "Must NOT" rules in invariants by reference rather than restating.
   - Why: single source of truth for layer rules. Currently only `profiling-source-data` cites it; the dlt cluster reproduces a subset by hand.
   - Priority: **P1**.

9. **Clarify `ingestion-data-testing` PK semantics**
   - Skill: `ingestion-data-testing`.
   - Change: state explicitly that Tier 1 tests are on `_dlt_id` (synthetic), and natural-PK uniqueness is a downstream-staging concern; cite `medallion-guardrails.md`.
   - Why: prevents agents from adding natural-PK uniqueness tests at bronze, which would violate the guardrail.
   - Priority: **P1**.

### P2 — nice-to-have

10. **Add `dev_mode=True` to `running-dlt-in-duckdb-sandbox`**
    - Why: research/02 calls out ~7% adoption as a foot-gun.

11. **Add typed `@configspec` multi-auth pattern**
    - Skills: `pinning-dlt-schema`, `generating-dlt-pipeline`.
    - Why: research's canonical multi-auth shape. Plugin missing.

12. **Add `tag pipeline runs with git_sha`**
    - Skill: `generating-dlt-pipeline`.
    - Why: must-do in pattern catalogue; missing in skill.

13. **Document Pydantic `is_authoritative_model` decision**
    - Skill: `pinning-dlt-schema`.
    - Why: catalogue marks Pydantic patterns must-do; skill doesn't require the decision.

14. **Cross-link `dlt-resource-conventions.md` naming rationale**
    - Skill: `discovering-source-schema`.
    - Why: agents coming from research/other plugins expect `raw_<system>`; the plugin uses `src_<connection_name>` deliberately and the rationale should be one click away.

15. **Add snapshot-test (`syrupy`) recommendation to `dlt-unit-testing`**
    - Why: `dlt-snapshot-test-the-yielded-shape-with-syrupy` is in the catalogue; skill doesn't surface it.

---

## Honest summary

The plugin's dlt skill cluster is **structurally sound**. Layer separation is enforced, secrets handling is correct, sandbox isolation is taken seriously, and the medallion guardrails are stronger than what most teams ship. The plugin also outpaces the research baseline on cost guards, governance, OTel, and operational runbook discipline.

The real gaps are in **technical defense-in-depth for the ingestion build itself**: missing source profiling, missing incremental knobs (`allow_external_schedulers`, `row_order`, `lag` wiring, `max_table_nesting`), and an opaque pipeline-evaluation rule set. None of these block correctness; they reduce the floor of what an LLM agent will produce when driven only by this plugin. Implementing the P0+P1 items would close most of the divergence with the research baseline without touching the plugin's strengths.
