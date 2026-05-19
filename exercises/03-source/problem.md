# 03 — Source

A **source** (`@dlt.source`) is a grouping of resources that share auth, rate limit, or schedule. It's also the natural place to attach source-level hints (e.g. a default `schema_contract`).

## Goal

Wrap `player_profile` and the new `country_stats` from exercise 02 into a single `chess` source. Run the source through the pipeline — both tables should populate from a single `pipeline.run()` call.

## Acceptance

1. A function `chess()` decorated with `@dlt.source`.
2. `pipeline.run(chess())` produces both `player_profile` and `country_stats`.
3. Only **one** load package is created (check `bronze_chess._dlt_loads` — a single `load_id`).

## Hints

- A source returns a list of resources.
- The shared `chess_source.py` already shows the shape — feel free to copy and adapt.
- Look at `_dlt_loads` in DuckDB after the run: `SELECT load_id, COUNT(*) FROM bronze_chess._dlt_loads GROUP BY 1;`
