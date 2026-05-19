# 09 — Dataset name

`dataset_name` is the schema namespace inside the destination. Same pipeline code can write to `bronze_dev` locally and `bronze_prod` in production by flipping one env var.

## Goal

Make a single `chess` pipeline that writes to `bronze_chess_dev` or `bronze_chess_prod` based on `DLT_ENV`.

## Acceptance

1. `DLT_ENV=dev python solution.py` → table in `bronze_chess_dev`.
2. `DLT_ENV=prod python solution.py` → table in `bronze_chess_prod`.
3. Same source code, no `if/else` for table names anywhere downstream.

## Hints

- Read `os.environ["DLT_ENV"]` at the top of the script.
- This isn't a deep dlt feature — it's the convention that lets one pipeline file ship to many environments.
