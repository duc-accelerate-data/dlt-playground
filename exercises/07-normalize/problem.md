# 07 — Normalize stage + control columns

dlt's pipeline is **extract → normalize → load**. The normalize stage:

- Flattens nested JSON (`{"chess_blitz":{"last":{"rating":2879}}}` → `chess_blitz__last__rating`).
- Splits nested arrays into child tables linked via `_dlt_parent_id`.
- Injects three control columns into every table:
  - `_dlt_id` — row identity (content hash unless `primary_key` is declared).
  - `_dlt_parent_id` — FK pointing at the parent row's `_dlt_id` (child tables only).
  - `_dlt_load_id` — id of the load package that wrote the row.

## Goal

Load two chess.com endpoints that exercise *different* normalize behaviors:

- `/pub/player/{user}/stats` — deeply nested JSON → demonstrates **flattening**
- `/pub/player/{user}/games/archives` — `{archives: [url, url, …]}` → demonstrates **child tables**

(`player_profile` from earlier exercises is intentionally flat — it would only show control-column injection, not flattening or child tables.)

## Acceptance

1. `bronze_chess.player_stats` has flattened columns of the form `chess_blitz__last__rating`, `chess_blitz__record__win`, etc.
2. A second table `bronze_chess.player_games_archive_index__archives` exists — the child table dlt created for the nested `archives` array.
3. The child rows link back to the parent: `child._dlt_parent_id = parent._dlt_id`.
4. Joining `player_stats._dlt_load_id` to `_dlt_loads.load_id` returns one row per load package.

## Hints

- Query schema via `information_schema.columns` (DuckDB-native).
- List all tables via `information_schema.tables WHERE table_schema='bronze_chess'`.
- `_dlt_loads` and `_dlt_version` live in the same dataset and are part of every dlt-managed schema.
