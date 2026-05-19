# Notes — Parent / child transformer

- **`@dlt.transformer` ≠ child table for nested array.** Nested arrays in the *same* JSON payload become child tables automatically — no transformer needed. Transformer = "I need to call a *second* endpoint per parent row".
- **`data_from`** can be a resource *or* a list of resources. The transformer iterates whatever the parent yields.
- **Build order:** parent first, then transformer. dlt enforces this — the load package commits in dependency order.
- **`_dlt_parent_id` injection is automatic** inside transformers and inside auto-flattened child tables. You should *never* hand-set it.
- **Don't merge child on its own primary key** if the parent uses merge — when a parent row is deleted/replaced, children should follow. dlt handles cascade for auto-created child tables; for transformer children you usually want `write_disposition="replace"` per-run or `merge` with `merge_key` on `_dlt_parent_id`.
