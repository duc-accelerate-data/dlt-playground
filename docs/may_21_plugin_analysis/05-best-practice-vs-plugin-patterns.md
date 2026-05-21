# Best-Practice Research vs Plugin `dlt-patterns.md`

Comparison of two reference corpora that both claim to encode "how to do dlt right":

- **Baseline**: `docs/best_practice_research/` — `INGESTION-PLAYBOOK.md`, `DLT-PATTERNS.md`, and the four research reports synthesized from real `verified-sources` connectors, dlt-hub docs/blog, ~30 GitHub production pipelines, vendor (Fivetran/Airbyte) lifecycle docs, and analytics-team templates (jaffle-shop, cal-itp, fivetran packages).
- **Plugin**: the new vibedata-data-engineering plugin's `_shared/references/patterns/dlt-patterns.md` (a 118-entry pattern index, variant `med`), plus its `playbooks/dlt-resource-conventions.md`, `playbooks/medallion-guardrails.md`, and `playbooks/ingestion-test-tiers.md`.

---

## 1. Scope of each source

**Best-practice research** is a *narrative + evidence* corpus. It frames the ingestion lifecycle as a four-axis model (extract mode, cursor, load mode, schema contract) shared across Fivetran/Airbyte/dlt, walks an 8-phase build process (scope → inventory → profile → schema posture → credentials → cursors → bronze layout → testing), and explicitly tracks the **stated-vs-observed gap** (e.g. only ~8% of production pipelines set a `schema_contract`). It deliberately omits dbt-internal materialization details and skirts low-level operational toggles (parallelism, file rotation, OTel) in favor of decision frameworks. Its strength is *judgement* — which knob matters and why.

**Plugin `dlt-patterns.md`** is an *enumerated pattern catalogue*: 118 short rules ("pattern + criticality + applicable skills + summary"). Categories span resource shape, schema contracts, incremental cursors, testing (unit / integration / replay / canary / reconciliation), CI/deploy, cost (parallelism caps, file rotation, lifecycle policies, BigQuery slot reservations), observability (OTel, Datadog, audit logs), governance (SOX/SOC2 two-reviewer rule, approved-source list, ADRs), and runbooks (cursor reset, GDPR erasure, postmortem template). It is breadth-first and operations-heavy. The plugin's `medallion-guardrails.md` and `dlt-resource-conventions.md` playbooks supply the structural "must/must-not" rules per layer. The pattern doc deliberately omits the *why* and the *evidence* — most entries are one-line summaries pointing to an unreferenced expanded source.

---

## 2. Agreements

| Pattern | Best-practice research | Plugin patterns / playbooks |
|---|---|---|
| Default schema contract: `tables:evolve, columns:freeze, data_type:freeze` | `DLT-PATTERNS.md` "Schema contract — when and how"; `INGESTION-PLAYBOOK.md` phase 4 | `dlt-use-evolve-for-new-tables-freeze-for-existing-columns` (must-do); `medallion-guardrails.md` Bronze "Must" |
| Never set `tables:freeze` at generation time — only after first successful load | `DLT-PATTERNS.md` "Critical gotcha" callout | `generating-dlt-pipeline` SKILL invariant; `medallion-guardrails.md` "tables added by `pinning-dlt-schema` only after every resource has loaded once" |
| `merge` + `primary_key` for mutable entities; `append` for immutable events; `replace` for small reference tables | `DLT-PATTERNS.md` "Write disposition decision" table; `INGESTION-PLAYBOOK.md` phase 2 | `dlt-pick-the-write-disposition-with-the-requirement-not-afterwards`; `dlt-resource-conventions.md` Write Dispositions table |
| Secrets via `dlt.secrets.value` kwarg defaults; env vars override in CI; never hardcode tokens | `DLT-PATTERNS.md` "Credentials" §; `research/02` Credentials | `dlt-secrets-in-ci-github-actions-env-never-secrets-toml`; `dlt-env-var-override-in-ci-cd`; `dlt-anti-pattern-same-set-of-credentials-for-dev-and-prod` |
| Server-side `updated_at` cursor; `initial_value` sentinel; configure lag/lookback for late-arriving rows | `DLT-PATTERNS.md` "Incremental cursors" five rules | `dlt-late-arriving-records-configure-a-lookback-window`; `dlt-document-the-cursor-column-in-the-resource-docstring` |
| Backfills use separate `pipeline_name` + `dataset_name`; bounded `initial_value`+`end_value` | `DLT-PATTERNS.md` "Backfill mode"; `INGESTION-PLAYBOOK.md` Backfill safety | `dlt-anti-pattern-running-two-pipelines-with-the-same-name-working-dir-in-parallel`; `dlt-pre-flight-check-before-manual-backfill` |
| Bronze is data, not code: no transforms, no joins, no business rules in the ingestion layer | `INGESTION-PLAYBOOK.md` phase 7 "Bronze is *not* a dbt-materialised layer"; `research/04` | `medallion-guardrails.md` Bronze "Must NOT" (explicit and forceful); `generating-dlt-pipeline` invariant "no casts, joins, filters, surrogate keys" |
| Schema-change workflow: load fails → PR adds column → CI passes → merge → unblock | `DLT-PATTERNS.md` "When a schema change happens" | `dlt-use-schema-contract-freeze-as-a-ci-gate`; `dlt-anti-pattern-changing-schema-in-a-feature-pr` |
| Test the resource as a generator before it touches dlt | `DLT-PATTERNS.md` "Common idioms"; implicit in research/01 | `dlt-a-dlt-resource-is-just-a-generator-test-it-that-way`; `dlt-mock-the-http-client-with-pytest-mock`; `dlt-unit-testing` SKILL |
| DuckDB for dev/CI integration tests; real warehouse for prod | `INGESTION-PLAYBOOK.md`; `research/03` | `dlt-duckdb-for-dev-parquet-on-s3-for-prod`; `dlt-run-integration-tests-in-ci-against-duckdb`; `running-dlt-in-duckdb-sandbox` SKILL |
| Schedule incrementally, not full-refresh | implicit across research | `dlt-schedule-incrementally-not-full-refresh`; `dlt-anti-pattern-pipeline-run-with-no-incremental-config` |
| Don't commit `~/.dlt` / pipeline cache to git | not stated explicitly but assumed | `dlt-anti-pattern-committing-dlt-pipelines-to-git` |
| Test tiers: `_dlt_id` non-null + unique are mandatory bronze checks | `INGESTION-PLAYBOOK.md` phase 8 "PK uniqueness on staging" (slightly different layer) | `ingestion-test-tiers.md` Tier 1 (mandatory); `dlt-assert-dlt-load-id-lineage-on-every-row` |

---

## 3. Conflicts

| Topic | Best-practice research says | Plugin says | Likely correct |
|---|---|---|---|
| **PK uniqueness layer** | Research's `INGESTION-PLAYBOOK.md` phase 8 puts PK `unique`+`not_null` at the **staging** layer (the "bronze↔silver contract"); bronze itself gets only `loaded_at_field` freshness. The cited industry templates (jaffle-shop, fivetran packages) match. | Plugin's `ingestion-test-tiers.md` Tier 1 places `_dlt_id` non-null + unique **on bronze tables directly**, executed as pytest queries against landed DuckDB. | **Context-dependent.** Both are valid. Plugin's choice catches dlt loader bugs earlier; research's choice catches downstream contract breaks. They're complementary, not exclusive — the plugin should clarify the bronze test is on the synthetic `_dlt_id`, not the natural PK (which is still a staging-layer concern). |
| **`replace` for incremental sources** | Research surveys Salesforce treating mutable Contact/Lead/Campaign as `replace` pragmatically (no cheap cursor) and Stripe shipping both replace and incremental source variants. It treats this as a real choice. | `medallion-guardrails.md` Bronze "Must NOT": "No `replace` write disposition for incremental sources … unless the user has explicitly accepted full reload." | **Plugin is right for the default**, research is honest about the escape hatch. Plugin's "explicit user accept" rule preserves the escape. No real conflict, but plugin's phrasing is stricter than research's. |
| **`row_order` on incremental** | Research treats `row_order="asc"` as a genuine optimization, dangerous on unordered sources but worth using when safe. | Plugin's `dlt-patterns.md` does **not** include a `row_order` pattern at all. Neither do the skills. | **Research is right.** Genuine omission in plugin — flagged in §4 below. |
| **dbt as the testing layer for business rules** | Research recommends staging tests (`unique`/`not_null`) plus intermediate/marts for business rules; bronze gets only freshness. | Plugin's `dlt-hook-dbt-downstream-as-the-business-rules-layer` says the same — but `ingestion-data-testing` SKILL ships Tier 1/2 row-count and accepted-values checks at bronze. | **No real conflict** once you read both: plugin runs *structural* tests on bronze and pushes *semantic* tests to dbt. The plugin should make this split explicit in the skill prose; today it reads as if everything happens in pytest. |
| **`schema_contract` adoption claim** | Research/02: ~8% of GitHub pipelines set any contract, and the dlt-hub "Pydantic `is_authoritative_model`" pattern has near-zero adoption. | Plugin treats `is_authoritative_model` / Pydantic validation as a must-do pattern (`dlt-pydantic-validation-at-the-resource-boundary`, `dlt-pydantic-schema-contract-columns-discard-value-maps-to-extra-ignore`). | **Plugin is prescriptively right** (these are good ideas), but it never acknowledges that adoption is rare and the feature is new. An LLM agent following the plugin will produce code patterns that look unlike most real-world dlt pipelines on GitHub. That's an opinion, not a bug, but worth labelling. |
| **`dev_mode=True` for iteration** | Research recommends it (research/02 calls it underused). | Plugin patterns do not surface a `dev_mode` recommendation at all. | **Research is right.** Missing in plugin. |
| **`allow_external_schedulers=True`** | Research recommends it on all production incrementals. | Plugin does not include it as a pattern; no skill mentions it. | **Research is right.** Missing in plugin. |
| **`_dlt_loads` join for freshness** | Research recommends emitting it as a staging model (cited Cal-ITP pattern). | Plugin has `dlt-volume-anomaly-via-dlt-loads-audit-table`, `dlt-audit-log-of-pipeline-runs`, `dlt-track-lineage-via-dlt-load-id-chain` — covers it well. | No conflict; agreement. |

---

## 4. In research only — gaps in plugin

Patterns or guidance present in `docs/best_practice_research/` that the plugin's `dlt-patterns.md` and dlt skills do **not** mention:

1. **`row_order="asc"|"desc"` on incremental cursors** — research explicitly covers when it's safe and when it silently drops rows. Plugin patterns are silent.
2. **`allow_external_schedulers=True`** — research lists it among the five rules for incremental wiring (Zendesk and Shopify ship it). Plugin: zero mentions.
3. **`dev_mode=True` for iteration** — research/02 calls out ~7% adoption as a foot-gun. Plugin patterns: absent.
4. **Typed `@configspec Union` for multi-auth** — research/01 documents `TZendeskCredentials` / `SalesforceAuth` as the canonical multi-auth shape; research's `DLT-PATTERNS.md` §Credentials gives a full code example. Plugin: no pattern.
5. **`max_table_nesting=2` source-level hint** — research/01 calls this the canonical defense against schema sprawl. Plugin's `dlt-avoid-deep-nesting-at-the-api-boundary` is API-side only, not the dlt knob.
6. **Variant column foot-gun explanation** — research's `DLT-PATTERNS.md` has a half-page on `__v_<type>` semantics. Plugin's `dlt-type-coercion-vs-variant-column-when-each-is-right` is one summary line.
7. **Four-layer idempotency model** (extract/normalize/load/recovery) — research's framing. Plugin treats idempotency obliquely via "pick the right write_disposition".
8. **SCD2 hash-on-add-column foot-gun** — research's `DLT-PATTERNS.md` calls out that adding a column under SCD2 fakes "change" for every existing row. Plugin: not surfaced.
9. **Stated-vs-observed gap awareness** — research treats this as a first-class topic so agents don't copy laziness from GitHub. Plugin patterns read as universally must-do without that calibration.
10. **Bronze schema naming convention `raw_<system>`** vs the plugin's `src_<connection_name>`. Research surveys real teams and lands on `raw_<system>`; plugin's `dlt-resource-conventions.md` explicitly *retires* `raw_<source_system>` because multi-connection setups collide. Not a gap but a deliberate divergence worth noting.
11. **`stg_<system>__<table>` staging naming + dbt source-block layout** — research has a whole report on it (research/04). Plugin's dlt skills don't reference staging conventions at all (that's the dbt side, fair, but cross-link is missing).
12. **Vendor mapping cheat sheet** (Fivetran/Airbyte/dlt translation table) — research/03. Plugin: not present, and not really expected of an internal plugin, but a gap for migration scenarios.

---

## 5. In plugin only — patterns research doesn't cover

Patterns the plugin enforces that the research baseline doesn't discuss in any depth:

1. **Cost guards as first-class patterns** — `cost-guard-cap-parallelism`, `cost-guard-rotate-files-at-sane-sizes`, `cost-guard-lifecycle-policy-on-staging-bucket`, `truncate_staging_dataset`, BigQuery slot reservations vs on-demand, cold-tier archival. Research is silent on cost.
2. **OpenTelemetry tracing integration** (`OTEL_*` env vars, Datadog/Honeycomb exporters) — `dlt-opentelemetry-tracing`, `dlt-datadog-integration-via-opentelemetry`.
3. **Governance/compliance patterns** — approved-source allowlist, SOX/SOC2 two-reviewer rule, GDPR right-to-erasure SOP, PII tagging on resources (`meta={"pii": True}`), row-level PII filtering at ingest.
4. **Operational runbook templates** — postmortem template, pre-flight backfill checklist, cursor-reset SOP, blast-radius documentation per pipeline.
5. **`canary row` round-trip pattern** — insert a known-shape row at source, assert appearance at destination within N minutes.
6. **`tag pipeline runs with git_sha`** (via `_dlt_load_id_suffix=GITHUB_SHA`) for lineage from data row back to commit.
7. **No-op canary PR check** — scheduled draft PR with trivial change to catch CI infra rot before a real PR hits it.
8. **`schema_contract=freeze` as a CI gate** (specifically labelled as a CI mechanism, not a runtime one) — research mentions freeze but doesn't frame it as a CI signal.
9. **Medallion guardrails as enforceable hard rules** — bronze cannot transform, must carry control columns, staging is 1:1, marts must declare contracts. Research describes this as convention; plugin makes it a rule with halt conditions.
10. **Workspace-directory anti-pattern** — `dlt-resource-conventions.md` calls out that naming a project dir `dlt/` collides with the installed package (real foot-gun caught in the field). Research doesn't mention this.
11. **Two-tier sandbox model** (DuckDB vs Fabric) with explicit dispatcher skill — plugin-specific architectural choice.
12. **Per-resource `apply_hints` verified-source override pattern** with mandatory comment — `dlt-comment-every-apply-hints-call`. Research mentions `apply_hints` as a tool, plugin makes it a documented decision.

---

## 6. Verdict

The two corpora are **strongly aligned on the core technical decisions** — write disposition, schema contract default, cursor design, secret handling, bronze-as-data discipline — and the conflicts are mostly differences of layer (bronze vs staging PK tests) or emphasis (plugin makes prescriptions absolute that research treats as defaults). Where they diverge meaningfully, the divergence is one of *scope*: research is a build-process narrative with calibrated awareness of the stated-vs-observed gap; plugin is an exhaustive operational/governance/cost catalogue tuned for an LLM agent in a specific (vibedata) tooling context.

The biggest functional divergence is the plugin's **missing coverage of several dlt-specific incremental and source knobs that research treats as canonical**: `row_order`, `allow_external_schedulers`, `dev_mode`, `max_table_nesting`, typed `@configspec` multi-auth unions, and the variant-column / SCD2-hash foot-guns. An agent driven only by the plugin will produce pipelines that work but miss optimizations and defensive idioms that the verified-sources survey shows are standard in production. The plugin's strengths (medallion guardrails, cost guards, governance, operational runbooks, workspace-naming gotcha) are exactly the layer research underweights — combining the two would produce a noticeably stronger reference than either alone.
