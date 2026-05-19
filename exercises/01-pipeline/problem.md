# 01 — Pipeline

**Concept.** `dlt.pipeline()` is the orchestrator. It owns:
- a `pipeline_name` (unique on disk — state lives in `~/.dlt/pipelines/<name>/`)
- a `destination` (where rows go)
- a `dataset_name` (the schema / DB-namespace inside the destination)

Everything else — resources, sources, schema, state — is keyed off the pipeline.

## Goal

Load the first 3 Chess.com player profiles into DuckDB. Verify the table exists with the right name and that re-running the script does **not** duplicate rows.

## Acceptance

1. `data/warehouse.duckdb` exists.
2. `bronze_chess.player_profile` has exactly 3 rows.
3. Run twice → still 3 rows.
4. `python -m dlt pipeline chess_bronze info` prints a load history with at least 1 successful load.

## Hints

- `pipeline_name="chess_bronze"`, `destination="duckdb"`, `dataset_name="bronze_chess"`.
- The shared `player_profile` resource defaults to `write_disposition="replace"` — why does that solve "no duplicates on re-run"?
- DuckDB destination defaults to a file in `pipelines_dir` — pin it to the repo by setting `destination=dlt.destinations.duckdb("data/warehouse.duckdb")`.
