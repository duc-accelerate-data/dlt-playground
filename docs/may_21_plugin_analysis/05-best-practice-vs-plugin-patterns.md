# Best-Practice Research vs the Plugin's Pattern Catalogue

We're comparing two collections that both claim to encode "how to do ingestion with dlt the right way":

- **The baseline research.** A folder of best-practice notes (`docs/best_practice_research/`) — a long ingestion playbook, a patterns document, and four research reports. These were built by reading real dlt verified-source connectors, the dlt-hub documentation and blog, around 30 production pipelines on GitHub, vendor lifecycle docs from Fivetran and Airbyte, and analytics-team templates (jaffle-shop, Cal-ITP, Fivetran packages).
- **The plugin's catalogue.** The new pattern file inside the data-engineering plugin's shared folder (118 entries, tagged for the "medium" variant), plus three of its playbooks: one for dlt resource conventions, one for medallion guardrails, and one for ingestion test tiers.

---

## 1. What each source is

**The baseline research is a narrative with evidence behind it.** It frames the ingestion lifecycle as four decisions you have to make (how to extract, what cursor to use, how to load, what schema contract to commit to) and treats those as the same four decisions whether the tool is Fivetran, Airbyte, or dlt. It walks an eight-step build process: pick a single source, list the entities, profile the source, decide a schema posture, pick a credential approach, wire incremental cursors, lay out the bronze tables, and test the right layer. It deliberately tracks the **gap between what teams *say* they do and what they actually ship** (for example, only about 8% of production pipelines on GitHub set any schema contract at all). It skips dbt-internal materialisation details and most low-level operational knobs (parallelism, file rotation, observability tooling) in favour of decision frameworks. Its strength is *judgement* — which knob matters, and why.

**The plugin's catalogue is an enumerated list of rules.** 118 short entries, each with a name, a criticality flag, the tasks it applies to, and a one-line summary. Categories span resource shape, schema contracts, incremental cursors, testing (unit, integration, replay, canary, reconciliation), CI and deployment, cost guards (parallelism caps, file rotation, lifecycle policies, BigQuery slot reservations), observability (tracing, Datadog, audit logs), governance (compliance two-reviewer rule, approved-source list, decision records), and runbooks (cursor reset, GDPR erasure, postmortem template). It is breadth-first and operations-heavy. The plugin's medallion-guardrails and resource-conventions playbooks supply the structural "must" and "must not" rules per layer. The catalogue deliberately drops the *why* and the *evidence* — most entries are one-line summaries pointing at an unreferenced longer source.

---

## 2. Where they agree

| Pattern | Baseline research | Plugin |
|---|---|---|
| The default schema contract is: evolve at the table level, freeze at the column level, freeze at the data-type level. | Stated in the patterns doc and in the playbook's schema-posture phase. | Entry tagged must-do in the catalogue; restated in the medallion-guardrails Bronze "Must" section. |
| Never set "tables: freeze" when first generating the pipeline — only after the first successful load. | Called out as a critical gotcha. | Built into the pipeline-generation task as an invariant; the schema-pinning playbook also enforces it. |
| Use `merge` plus a primary key for things that change, `append` for immutable events, and `replace` for small reference tables. | Spelled out in a write-disposition decision table. | Required by the catalogue and restated in the resource-conventions playbook's dispositions table. |
| Get secrets from the dlt-secrets default mechanism; let environment variables override in CI; never hardcode tokens. | Spelled out in the credentials section. | Multiple catalogue entries enforce CI uses environment variables, never the secrets file, and prohibit reusing dev credentials in prod. |
| Use a server-side `updated_at` field as the cursor; set a sensible far-past starting value; configure a lookback window for records that arrive late. | The five rules for incremental cursors. | Catalogue entries for the lookback window and for documenting the cursor column in the resource's docstring. |
| Backfills run as a separate pipeline with their own dataset, and use a bounded start-and-end window. | Stated as a backfill-safety rule. | Anti-pattern entry: never run two pipelines with the same name and working directory in parallel; a pre-flight check is required before a manual backfill. |
| The bronze layer holds raw data, not code. No transforms, no joins, no business rules. | Stated in the bronze layout phase and again in research report 04. | The medallion guardrails make this explicit and forceful in the Bronze "Must NOT" section; the pipeline-generation task forbids casts, joins, filters, and surrogate keys. |
| Schema-change workflow: load fails → open a PR to add the column → CI passes → merge → pipeline unblocks. | Spelled out in the schema-change section. | Catalogue entry: use the freeze contract as a CI gate; another entry treats schema changes inside a feature PR as an anti-pattern. |
| A dlt resource is just a generator; test it as a generator before letting dlt touch it. | Common idioms section; implicit in research report 01. | Multiple catalogue entries on this exact point, plus the dlt unit-testing task. |
| Use DuckDB for development and CI integration tests; use the real warehouse for production. | Stated in the playbook and in research report 03. | Several catalogue entries plus the sandbox tasks for DuckDB. |
| Schedule incrementally — never full-refresh. | Implicit across the research. | A catalogue entry and an explicit anti-pattern for incremental-less runs. |
| Don't commit dlt's local cache (`~/.dlt`) or per-pipeline state to git. | Assumed but not spelled out. | Explicit anti-pattern in the catalogue. |
| Test tiers: a row-level identity column being present and unique is a mandatory bronze check. | Slightly different — the playbook puts PK uniqueness at the staging layer. | Tier 1 of the ingestion-test-tiers playbook makes the synthetic dlt row-ID test mandatory, plus a load-lineage check on every row. |

---

## 3. Where they disagree

| Topic | Baseline research says | Plugin says | Likely correct |
|---|---|---|---|
| **Which layer owns the primary-key uniqueness test.** | The research's playbook puts PK uniqueness and not-null at the **staging** layer — treating it as the bronze-to-silver contract. Bronze itself gets only a freshness check. Industry templates (jaffle-shop, Fivetran packages) match. | The plugin's test-tiers playbook puts a uniqueness test on the **synthetic dlt row-ID** at the bronze layer, run as pytest queries against the landed DuckDB. | **Both can be right.** They catch different things. The plugin's test catches dlt loader bugs early; the research's test catches downstream contract breaks. They are complementary. The plugin should make explicit that its bronze test is on the synthetic ID, not on the natural primary key (which is still a staging-layer concern). |
| **Whether `replace` is ever OK for an incremental-shaped source.** | The research surveys real teams — Salesforce sometimes treats mutable entities as `replace` because no cheap cursor exists; Stripe ships both `replace` and incremental source variants. It treats this as a real judgement call. | The medallion guardrails forbid `replace` for incremental sources unless the user explicitly accepted a full reload. | **The plugin is right for the default**; the research is honest about the escape hatch. The plugin preserves the escape hatch (explicit user accept). Not a real conflict, but the plugin's phrasing is stricter. |
| **`row_order` on incremental cursors.** | The research treats `row_order="asc"` as a real optimisation — dangerous on unordered sources, but worth using when safe. | The plugin's catalogue does not include `row_order` at all. Nor do any tasks. | **The research is right.** Genuine gap in the plugin — flagged below. |
| **Where business rules get tested.** | The research recommends running uniqueness and not-null tests at staging, and business rules at intermediate and marts; bronze gets only freshness. | The plugin agrees on paper (one catalogue entry routes business rules to dbt) — but its ingestion-test task still runs row-count and accepted-values checks at the bronze layer. | **No real conflict** once you read both: the plugin runs *structural* tests at bronze and pushes *semantic* tests into dbt. The plugin's task should make this split explicit. As written, it reads like everything happens in pytest. |
| **How widely the strong schema-contract patterns are adopted.** | About 8% of pipelines on GitHub set any contract; the dlt-hub Pydantic-based "authoritative model" pattern has near-zero adoption. | The plugin treats Pydantic validation at the resource boundary as a must-do pattern. | **The plugin is prescriptively right** — these are good ideas. But it never acknowledges that adoption is rare and the feature is new. An assistant following the plugin will produce code that looks unlike most real-world dlt pipelines on GitHub. That's an opinion, not a bug, but it's worth labelling. |
| **Using dlt's iteration mode (`dev_mode=True`) when developing.** | The research recommends it; calls it underused. | The plugin's patterns don't mention it. | **The research is right.** Missing from the plugin. |
| **Letting external schedulers manage state (`allow_external_schedulers=True`).** | The research recommends it on all production incrementals. | The plugin doesn't mention it. No task references it. | **The research is right.** Missing from the plugin. |
| **Surfacing the dlt loads table for freshness.** | The research recommends emitting it as a staging model (Cal-ITP pattern). | The plugin has entries for tracking lineage and detecting volume anomalies using the loads table. | No conflict. They agree. |

---

## 4. Things only the research covers — gaps in the plugin

These appear in the baseline research but neither the plugin's catalogue nor any of its dlt tasks mention them:

1. **`row_order="asc"|"desc"` on incremental cursors.** The research explains when it's safe and when it silently drops rows. The plugin is silent.
2. **`allow_external_schedulers=True`.** Listed in the research's five rules for incremental wiring (Zendesk and Shopify ship it). Not mentioned anywhere in the plugin.
3. **`dev_mode=True` for iteration.** The research calls out the roughly 7% adoption rate as a foot-gun. The plugin doesn't mention it.
4. **Typed multi-auth credentials using dlt's `@configspec` union.** The research's report 01 documents the canonical pattern for sources that support more than one auth method (Zendesk, Salesforce); the research's patterns doc gives a full code example. Not in the plugin.
5. **`max_table_nesting=2` as a source-level hint.** The research calls this the canonical defence against schema sprawl. The plugin has an entry about avoiding deep nesting at the API boundary, but that's the API side. The dlt knob itself isn't surfaced.
6. **The variant-column foot-gun explained at length.** The research's patterns doc spends half a page on what dlt's variant columns mean and when they appear. The plugin reduces this to a single one-line entry.
7. **A four-layer idempotency model** (extract / normalize / load / recovery) — the research's framing. The plugin handles idempotency obliquely, through "pick the right write disposition".
8. **The slowly-changing-dimensions hash-on-add-column foot-gun.** The research calls out that adding a column under SCD2 fakes a "change" for every existing row. The plugin doesn't surface this.
9. **Awareness of the stated-vs-observed gap.** The research treats this as a first-class topic so assistants don't copy laziness from GitHub. The plugin's entries read as universally must-do without that calibration.
10. **Bronze schema naming.** The research surveys real teams and lands on `raw_<system>`. The plugin deliberately retires that convention in favour of `src_<connection_name>` because multi-connection setups collide on the older name. This is a deliberate divergence rather than a gap, but worth noting.
11. **Staging naming and dbt source-block layout.** The research has a whole report on this (research/04). The plugin's dlt tasks don't reference staging conventions at all. That's the dbt side, fair, but a cross-link is missing.
12. **A vendor-mapping cheat sheet** (Fivetran/Airbyte/dlt translation table) — the research has this in report 03. The plugin doesn't, and it isn't really expected to, but it's a gap for migration scenarios.

---

## 5. Things only the plugin covers — patterns the research doesn't discuss

1. **Cost guards as first-class patterns.** Parallelism caps, file-rotation at sane sizes, lifecycle policies on staging buckets, truncating staging datasets, BigQuery slot reservations vs on-demand, cold-tier archival. The research is silent on cost.
2. **OpenTelemetry tracing integration**, including exporters for Datadog and Honeycomb. The plugin has multiple entries; the research has none.
3. **Governance and compliance patterns.** Approved-source allowlist, compliance two-reviewer rule, GDPR right-to-erasure procedure, PII tagging on resources, row-level PII filtering at ingest. None in the research.
4. **Operational runbook templates.** A postmortem template, a pre-flight backfill checklist, a cursor-reset procedure, blast-radius documentation per pipeline.
5. **A canary-row round-trip pattern.** Insert a known-shape row at the source, assert it appears at the destination within N minutes.
6. **Tag pipeline runs with the git commit ID** so a data row can be traced back to the commit that produced it.
7. **A no-op canary PR check.** A scheduled draft PR with a trivial change to catch CI infrastructure rot before a real PR runs into it.
8. **The frozen schema contract used as a CI gate** (specifically labelled as a CI mechanism, not a runtime one). The research mentions freeze but doesn't frame it as a CI signal.
9. **Medallion guardrails as enforceable hard rules.** Bronze cannot transform, must carry control columns; staging is 1:1; marts must declare contracts. The research describes this as convention; the plugin makes it a rule with halt conditions.
10. **A workspace-directory anti-pattern.** The plugin's resource-conventions playbook calls out that naming a project folder `dlt/` collides with the installed Python package (a real foot-gun seen in the field). The research doesn't mention this.
11. **A two-tier sandbox model** (DuckDB vs Fabric) with an explicit dispatcher task. Plugin-specific architectural choice.
12. **A per-resource override pattern** with mandatory inline comment explaining each override (the plugin calls this out as must-do). The research mentions the underlying dlt mechanism but doesn't require the comment.

---

## 6. Verdict

The two collections are **strongly aligned on the core technical decisions** — write disposition, schema-contract default, cursor design, secret handling, bronze-as-data discipline. Where they conflict, it's mostly about which layer owns a test (bronze vs staging primary-key tests) or about emphasis (the plugin makes prescriptions absolute where the research treats them as defaults). Where they meaningfully diverge, the divergence is one of *scope*: the research is a build-process narrative with calibrated awareness of what teams actually ship; the plugin is an exhaustive catalogue of operations, governance, and cost rules tuned for an autonomous assistant inside the Studio environment.

The biggest functional divergence is the plugin's **missing coverage of several dlt-specific incremental and source knobs that the research treats as canonical**: `row_order`, `allow_external_schedulers`, `dev_mode`, `max_table_nesting`, typed multi-auth credentials, and the variant-column and SCD2-hash foot-guns. An assistant driven only by the plugin will produce pipelines that work, but that miss the optimisations and defensive idioms the verified-sources survey shows are standard in production. The plugin's strengths (medallion guardrails, cost guards, governance, operational runbooks, the workspace-naming gotcha) are exactly the layer the research underweights. Combining the two would produce a noticeably stronger reference than either alone.
