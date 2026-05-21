# dlt-playground — Documentation

The playground itself lives in `../exercises/`. This `docs/` directory is the
prose layer: the *why* and the *industry context* behind the exercises.

## Read in this order

1. **[INGESTION-PLAYBOOK.md](./INGESTION-PLAYBOOK.md)** — vendor-agnostic
   ingestion build process. Read first if you're new to ingestion. Holds
   whether you use dlt, Fivetran, Airbyte, or hand-rolled Python.

2. **[DLT-PATTERNS.md](./DLT-PATTERNS.md)** — dlt-specific patterns and
   idioms. Read after the playbook. Maps the vendor-agnostic mental model
   onto dlt's API surface.

3. **`research/*.md`** — the raw evidence. Four reports synthesizing real
   dlt connectors, blog posts, GitHub usage, vendor lifecycles, and
   analytics-team conventions. Cite-able sources for everything in the
   playbook and patterns docs.

## Research reports

| Report | What it covers |
|---|---|
| [01-dlt-verified-sources-survey.md](./research/01-dlt-verified-sources-survey.md) | Patterns across 10 connectors in `dlt-hub/verified-sources` (chess, github, notion, salesforce, hubspot, stripe, zendesk, shopify, sql_database, jira) |
| [02-dlt-blog-and-real-world-usage.md](./research/02-dlt-blog-and-real-world-usage.md) | dlt-hub's stated best practices vs ~30 real production pipelines on GitHub. Includes adoption stats |
| [03-vendor-lifecycle-comparison.md](./research/03-vendor-lifecycle-comparison.md) | Fivetran and Airbyte lifecycle models, mapped onto dlt's `write_disposition × schema_contract` matrix |
| [04-analytics-team-templates.md](./research/04-analytics-team-templates.md) | How real analytics teams (Cal-ITP, dbt-labs, Fivetran packages) structure the bronze layer |

## How this relates to the exercises

The exercises teach the *mechanics*: how a feature works, what it returns,
where the edge cases are. The docs teach the *judgement*: when to use which
feature, what real teams converge on, where stated practice diverges from
observed practice.

Use the exercises to build dlt fluency. Use the docs to know which patterns
are worth keeping when you walk into a real codebase.
