# Notes — Dataset name

- **Bronze convention (industry):** `bronze_<vendor>` or `src_<vendor>`. Pick one and enforce it across pipelines — dbt source definitions depend on it.
- **Don't put env in the table name.** Put env in the *dataset/schema* name. Otherwise downstream `dbt`/`sqlmesh` configs explode.
- **`pipeline_name` and `dataset_name` are independent.** It's fine (and common) for both to encode env: `pipeline_name="chess_dev"`, `dataset_name="bronze_chess_dev"`. Just be consistent.
- **`refresh="drop_resources"`** on `pipeline.run()` drops just the named resources' tables before reloading — useful for "rebuild this one table cleanly" without nuking the dataset.
- **dlt also supports `dataset_name=None`** at pipeline-level and per-`run()` — the run-level wins. Lets you write the same source into both `staging_chess` and `prod_chess` from one process.
