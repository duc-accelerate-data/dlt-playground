# Toolkit's dlt Tasks — Gap and Conflict Audit

This is an audit of the 16 dlt-focused automated tasks in the data-engineering toolkit, measured against two baselines combined: the best-practice research notes, and the toolkit's own pattern catalogue and playbooks.

---

## 1. How the audit was done

For each task I read its instruction file from the toolkit's tasks folder on the main branch. I compared what the task says it does (its description, its invariants, the references it cites, its procedure, and its output contract) to two things: what the research baseline identifies as canonical for that step in the ingestion lifecycle, and what the toolkit's own patterns catalogue flags as must-do or non-obvious for that step. The audit looks for: missing references to baseline patterns, invariants that contradict the baseline, and operational concerns the task should enforce but doesn't.

A methodological caveat: I only read the top-level instruction file for each task, not its sibling resources (scripts, templates, sub-instructions). Where an instruction file is sparse, the gap may already be filled by an unread companion file. Flagged inline where relevant.

---

## 2. Findings per task

| Task | Aligned with baseline? | Notable gap or conflict | Severity |
|---|---|---|---|
| Classify the user's request | Yes | This is a routing concern, not a dlt-technical one. No baseline conflict. | low |
| Discover a source's schema | Mostly | References the toolkit's patterns and resource-conventions playbook. Does not require profiling nesting depth, polymorphic fields, or rate-limit discovery. The inventory row it produces does not capture the lag or lookback window — the research treats that as a profiling decision. | medium |
| Profile the data in a source | Yes (for transformation work) | This task profiles bronze data for readiness to model in silver. There is **no task** that profiles the upstream source *before* anyone tries to build a pipeline — the way the research's profiling phase prescribes. Pre-build profiling questions (server-side vs client-side timestamps, mutation window, cursor field type, server-side filter availability, tenant boundaries) are not asked anywhere. | high |
| Generate a dlt pipeline | Mostly | Strong on the freeze-at-pin-time gotcha, the no-transforms-in-bronze rule, and the don't-wrap-verified-sources rule. **Missing:** no invariant requiring `allow_external_schedulers=True`, `max_table_nesting=2`, or a `row_order` decision; no requirement to set the lookback window from the discovered mutation window; no requirement to use typed multi-auth credentials when a source has multiple auth methods. References the patterns catalogue but doesn't pin which entries must be applied. | high |
| Pin the dlt schema | Yes | Correctly defers freezing tables until after the first successful load. Forbids dropping rows without rationale. **Minor gap:** doesn't require deciding whether a Pydantic model is authoritative, even though the patterns catalogue flags it as must-do. | medium |
| Run dlt in a sandbox (dispatcher) | Yes | Pure dispatcher, no technical content. Correctly delegates. | low |
| Run dlt in the DuckDB sandbox | Yes | Strong on the sandbox-vs-domain separation. References only the git-workflow conventions — does not reference the patterns catalogue, so cost guards, parallelism, and file rotation are not surfaced during sandbox iteration. | medium |
| Run dlt in the Fabric sandbox | Yes | Same shape as the DuckDB sandbox; correct on auth-failure handling. Same gap: it doesn't reference the patterns catalogue. | medium |
| Run ingestion data tests | Yes | The mandatory Tier 1 test (synthetic dlt row-ID present and unique) matches the baseline; business rules are deferred to dbt. **Possible conflict:** the research puts primary-key uniqueness at the staging layer, not bronze. The toolkit's bronze test is on the synthetic dlt row-ID, so it is defensible, but the prose doesn't make the distinction explicit. | low |
| Write dlt unit tests | Yes | Four canonical scenarios (happy / empty / partial-failure / cursor wiring) match the patterns catalogue's testing cluster. **Minor gap:** doesn't require snapshot tests for nested shapes, even though the pattern is in the catalogue. | low |
| Document dlt pipelines | Yes | Forbids "TBD" descriptions and requires documenting the control columns. **Gap:** doesn't require documenting the cursor column, refresh cadence, blast radius, or owner — even though the patterns catalogue lists each as must-do. | medium |
| Evaluate a dlt pipeline | Partially | Procedure is generic ("run deterministic audit checks"). The instruction file does not enumerate which rules the audit runs. **Gap:** you can't tell from reading the instructions whether the audit checks for `allow_external_schedulers`, schema-contract shape, nesting depth, the override-comment rule, and so on. The rule set is opaque. | high |
| Set up a DuckDB workspace | Yes | Correctly forbids editing the dlt config and secrets files; requires `dbt debug` to pass green. No baseline conflict. | low |
| Set up a Fabric workspace | Yes | Same shape; correct on auth-error escalation and Spark cold-start handling. | low |
| Validate fixture replay | Yes | Default mismatch threshold 0.01; halt on mismatch; halts on three non-deterministic re-runs — a sensible safety. | low |
| Validate against golden data | Yes | Row-exact replay with a strict threshold matches the research's contract-based testing posture. | low |

---

## 3. Cross-cutting gaps

Patterns from the toolkit's own catalogue or from the research baseline that no audited task enforces or references:

1. **`allow_external_schedulers=True` on incremental resources.** A rule in the research's incremental-cursor list, present in real verified sources (Zendesk, Shopify). Not referenced by pipeline generation, schema pinning, or schema discovery. Not even in the toolkit's catalogue.
2. **`row_order="asc"|"desc"` decision.** The research treats this as canonical; the toolkit's catalogue and every task are silent.
3. **`max_table_nesting=2` as a source-level hint.** The research calls this the canonical defence against schema sprawl. The toolkit has an entry about avoiding deep nesting at the API boundary, but the dlt knob itself isn't in any task.
4. **`dev_mode=True` during iteration.** Mentioned nowhere. The DuckDB sandbox task would be the natural home.
5. **Setting the lookback window from the discovered mutation window.** The pattern about lookback windows is in the catalogue, but no task enforces that the schema-discovery step capture the mutation window or that pipeline generation wire it through.
6. **Typed multi-auth credentials.** The research's canonical pattern for sources that support more than one auth method. Not referenced by any task; not in the catalogue.
7. **The Pydantic "is this model authoritative?" decision.** Catalogue marks the Pydantic patterns as must-do, but the schema-pinning task doesn't require the decision, and pipeline generation doesn't require wiring it in.
8. **The "comment every override" rule.** Catalogue must-do, but neither the pinning task nor the generation task enforces a comment per override call.
9. **Tagging pipeline runs with the git commit ID.** Must-do in the catalogue; not referenced by any task.
10. **Profiling the upstream source before building.** Research treats this as the highest-leverage phase. The toolkit's source-profiling task is for the bronze-to-silver readiness check, not the upstream source. There is no task that fills this slot.
11. **The pipeline-evaluation task's audit rules are opaque.** The instruction file says "run deterministic audit checks" without enumerating them. Whether it catches any of the gaps above is unverifiable from the public instructions.
12. **No dlt task references the medallion-guardrails playbook**, except implicitly through the bronze "must not transform" rule. The guardrails are the strongest layer-rule document in the toolkit, but only the source-profiling task cites them — the pipeline-generation task reproduces a subset by hand instead of pointing to the canonical source.

---

## 4. Cross-cutting conflicts

Places where a task's instructions contradict the patterns catalogue or the research:

1. **The ingestion-data-testing task runs primary-key tests at bronze, but the research puts them at staging.** Defensible — the toolkit's Tier 1 is on the synthetic dlt row-ID, not on a natural primary key — but the prose doesn't say "this test is on the synthetic ID; natural-PK uniqueness is a staging-layer dbt test." An assistant reading this task may add natural-PK uniqueness tests at bronze, which would violate the medallion guardrails. Recommend tightening the prose.
2. **Pipeline generation says "do not commit Python without YAML, or vice versa."** But schema pinning writes the skeleton and contract while pipeline generation writes the body. The ordering means a brief intermediate state where Python exists without per-resource YAML. Not a real conflict but the invariant phrasing is loose. Low severity.
3. **The resource-conventions playbook retires the older `raw_<system>` bronze schema name in favour of `src_<connection_name>`.** The research recommends `raw_<system>`. Deliberate divergence by the toolkit (justified by multi-connection collisions), but the rationale is buried in the playbook. An assistant migrating an existing dlt project from elsewhere will not know to rename. Worth a one-line callout in the schema-discovery task or the workspace-setup task.
4. **Pipeline generation says: "do not write per-resource files for a verified source — using `.with_resources()` is enough."** The research's report 01 shows the verified-sources project itself uses per-resource files internally. The toolkit's rule is about the *consumer* project (don't fork the verified source's per-resource layout) — correct intent, but the prose risks being misread as forbidding per-resource organisation for *custom* sources too. Recommend clarifying.

---

## 5. Action items

Prioritised.

### Highest priority — should-fix blockers

1. **Add a step that profiles the source *before* building (or expand the schema-discovery task).**
   - Add a new task (suggested name: `profiling-source-api`) or expand the existing schema-discovery task.
   - The change: the discovery must capture whether timestamps are server-side or client-side, how long after creation records can still be modified (the mutation window), what type the cursor field is, whether the API supports server-side filtering, and where tenant boundaries lie. Record these on the Pipeline Inventory row alongside the schema contract.
   - Why: the research playbook names this as the single most-skipped step, the one that "burns weeks". The toolkit currently has zero coverage of upstream-source profiling. The source-profiling task is for bronze-to-silver readiness and explicitly refuses the upstream-source role.

2. **Enumerate the pipeline-evaluation audit rules in the task's instructions.**
   - The change: list the deterministic checks the audit runs (is a schema contract present, are there no transforms in the pipeline file, does the write disposition match the inventory, are override calls all commented, and so on). Without this enumeration the task is unverifiable.
   - Why: an opaque audit makes the task un-auditable and prevents contributors from extending it deliberately. The research and the toolkit's own catalogue both treat enumerated rules as a quality signal.

### Important — should-fix

3. **Add `allow_external_schedulers=True` to the pipeline-generation invariants.**
   - Require incremental resources to set this to true unless the inventory row explicitly opts out. Add it to the patterns catalogue too.
   - Why: the research names it as standard on production verified sources (Zendesk, Shopify); absence means duplicating state mechanisms unnecessarily when running under Airflow or Dagster. The toolkit is silent.

4. **Add a `row_order` decision to the Pipeline Inventory and to pipeline generation.**
   - Each inventory row records whether the source is source-ordered. If yes, the resource sets `row_order="asc"` and the unit test covers early-break behaviour. If no, document why explicitly.
   - Why: the research and the dlt docs both flag this as a real optimisation with a real foot-gun. Toolkit catalogue and tasks are silent.

5. **Add `max_table_nesting=2` (or an explicit decision) to the schema-pinning task.**
   - Each `@dlt.source` decorator gets this default; deeper nesting is an explicit inventory decision with rationale.
   - Why: the research's canonical defence against schema sprawl; observed in real verified sources.

6. **Capture the mutation window and wire it through.**
   - At schema discovery: capture the upstream mutation window into the Pipeline Inventory. At pipeline generation: set the lookback window on the incremental source from that value.
   - Why: the lookback-window pattern is must-do in the toolkit's own catalogue, but no task operationalises it.

7. **Require a comment on every override call.**
   - Every override call must be preceded by a one-line comment explaining why the override exists.
   - Why: the comment-every-override-call rule is must-do in the catalogue.

8. **Reference the medallion-guardrails playbook from every dlt build task.**
   - Add the guardrails to the References section of pipeline generation, schema pinning, both sandbox tasks, and ingestion data testing; cite the Bronze "Must NOT" rules by reference rather than restating.
   - Why: single source of truth for layer rules. Today only the source-profiling task cites it; the dlt cluster reproduces a subset by hand.

9. **Clarify the primary-key test semantics in the ingestion-data-testing task.**
   - State explicitly that the Tier 1 test is on the synthetic dlt row-ID, and that natural-PK uniqueness is a downstream-staging concern; cite the medallion-guardrails playbook.
   - Why: prevents assistants from adding natural-PK uniqueness tests at bronze, which would violate the guardrails.

### Nice-to-have

10. **Add `dev_mode=True` to the DuckDB sandbox task.**
    - Why: the research calls out the roughly 7% adoption rate as a foot-gun.

11. **Add a typed multi-auth credentials pattern** to the schema-pinning and pipeline-generation tasks.
    - Why: the research's canonical multi-auth shape; missing from the toolkit.

12. **Add "tag pipeline runs with the git commit ID"** to pipeline generation.
    - Why: must-do in the catalogue; missing from the task.

13. **Document the Pydantic "is this model authoritative?" decision** in the schema-pinning task.
    - Why: the catalogue marks Pydantic patterns as must-do; the task doesn't require the decision.

14. **Cross-link the naming-convention rationale** from the schema-discovery task to the resource-conventions playbook.
    - Why: assistants coming from research or other toolkits expect the older bronze schema name; the toolkit uses a different one deliberately, and the rationale should be one click away.

15. **Add a snapshot-test recommendation** to the dlt unit-testing task.
    - Why: the snapshot-test pattern is in the catalogue but isn't surfaced by the task.

---

## Honest summary

The toolkit's dlt task cluster is **structurally sound**. Layer separation is enforced, secret handling is correct, sandbox isolation is taken seriously, and the medallion guardrails are stronger than what most teams ship. The toolkit also outpaces the research baseline on cost guards, governance, observability tracing, and operational runbook discipline.

The real gaps are in **technical defence-in-depth for the ingestion build itself**: missing source profiling, missing incremental knobs (`allow_external_schedulers`, `row_order`, lookback wiring, nesting depth), and an opaque pipeline-evaluation rule set. None of these block correctness; they reduce the floor of what an automated assistant will produce when driven only by this toolkit. Implementing the highest-priority and important items would close most of the divergence with the research baseline without touching the toolkit's strengths.
