# 02 — Resource

A **resource** (`@dlt.resource`) is a generator. One resource ≈ one table. Resources can be combined into a source, run alone, parameterized, and given hints (`primary_key`, `write_disposition`, `columns`).

## Goal

Write a new resource `country_stats` from scratch (don't import the shared one). It hits `https://api.chess.com/pub/country/US/players` and yields a single row `{"country": "US", "player_count": N}`. Run it through the same `chess_bronze` pipeline.

## Acceptance

1. New table `bronze_chess.country_stats` exists.
2. The table has exactly one row, with `player_count > 0`.
3. Re-running does not duplicate (think about disposition).

## Hints

- Yield dicts or lists of dicts. Either works.
- Resource name = table name by default. Override with `name="..."`.
- Don't worry about cursors yet — just `replace`.
