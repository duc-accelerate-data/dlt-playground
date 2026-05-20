# Notes — Documentation discipline

- **The docstring is the first runbook.** When the next engineer opens the file at 2am, they read the resource docstring before anything else. Source URL, auth, cursor field, write disposition, rate limit, owner — these *belong in the function*, not in a wiki that's already stale.
- **Column descriptions are machine-readable docs.** They flow into `pipeline.default_schema.to_pretty_yaml()` → dbt source YAMLs → the data catalog → downstream BI tooltips. One write, four free uses.
- **`RUNBOOK.md` next to the pipeline file.** Not `docs/`, not Confluence — sibling to the code. Sections that matter: backfill, rollback, common errors, alerts, owners. If the on-call can't act from this file alone, the runbook is broken.
- **Don't document what the code says.** "Loads users from GitHub" is a waste of bytes. "GitHub rate-limits authenticated PATs at 5,000 req/h; this pipeline shards by org to stay under" is the doc you wanted.
- **Owner is the most important field.** "Owner: data-eng@accelerate-data" + "Slack #data-eng" beats every other piece of metadata in an incident.
- **Schema YAML export is the bridge to dbt.** `pipeline.default_schema.to_pretty_yaml()` produces a YAML compatible with dbt's `sources:` blocks. Pipe it into your dbt project and you've eliminated the "are the docs in sync with the pipeline" question entirely.
- **One-paragraph rule.** If the docstring is more than one screen, you're missing an abstraction — split into multiple resources.
- **No emojis in docstrings.** They render badly in `dlt --help`, in dbt catalog, and in Slack alert previews.
