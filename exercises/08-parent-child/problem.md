# 08 — Parent / child transformer

When a source returns nested arrays, dlt auto-creates child tables linked via `_dlt_parent_id`. When you need to **fan out one row into many** by calling a *second* API endpoint per row, you use `@dlt.transformer`.

## Goal

Build `player_profile` (parent) + a transformer `player_archive_url` that, for each profile, hits the archives endpoint and yields one row per archive URL. The child table must carry `_dlt_parent_id` pointing back at the player.

## Acceptance

1. Two tables: `bronze_chess.player_profile`, `bronze_chess.player_archive_url`.
2. Every row in `player_archive_url` has a non-null `_dlt_parent_id`.
3. A join `player_archive_url._dlt_parent_id = player_profile._dlt_id` returns the archive count per player.

## Hints

- `@dlt.transformer(data_from=parent_resource)` — dlt feeds the parent's records to the transformer's first arg.
- Yield as many rows per parent record as you like.
- Parent must declare a `primary_key` so dlt makes `_dlt_id` deterministic — otherwise child `_dlt_parent_id` still works, but reruns shuffle parent ids.
