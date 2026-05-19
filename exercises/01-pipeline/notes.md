# Notes — Pipeline

- **Pipeline name = state key.** Two `dlt.pipeline("chess_bronze", ...)` calls in different files share the same incremental state, schema, and load history. This is a feature, not a bug — name pipelines deliberately.
- **`dev_mode=True`** wipes the pipeline working dir on every run. Useful in exercise drafts; **never** in prod.
- **Destination is configurable three ways**, in increasing precedence: env var → `config.toml` → keyword arg. Keyword arg is fine for exercises; in CI you'd flip via env.
- **One pipeline per vendor**, not per table. Putting `repos`, `issues`, `pulls` in one `github_bronze` pipeline lets dlt share the load package, schema, and state across them — atomic for the vendor.
- **Industry norm:** `<vendor>_bronze` is the most common name; some teams prefix with layer (`raw_github`) or system (`fivetran_github`). Stick to your team's convention.
