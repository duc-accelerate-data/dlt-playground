"""Reference solution for exercise 30 — evolving a live pipeline through 6 motions.

Each step runs against the same dataset, keeping state coherent between motions.
The verifier inspects the DuckDB schema between steps via STATE dict.
"""
from __future__ import annotations

import sys
from pathlib import Path

import dlt
import duckdb

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

WH = REPO / "data" / "warehouse.duckdb"
DATASET = "evolve_demo"
STATE: dict[str, int | bool | str] = {}


def fresh():
    duckdb.connect(str(WH)).execute(f"DROP SCHEMA IF EXISTS {DATASET} CASCADE")


def pipe():
    return dlt.pipeline(
        pipeline_name="evolve_demo",
        destination=dlt.destinations.duckdb(str(WH)),
        dataset_name=DATASET,
    )


def rows(table: str) -> int:
    return duckdb.connect(str(WH)).execute(f"SELECT COUNT(*) FROM {DATASET}.{table}").fetchone()[0]


def cols(table: str) -> set[str]:
    return {
        r[0] for r in duckdb.connect(str(WH)).execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema=? AND table_name=?", [DATASET, table]
        ).fetchall()
    }


# --- Step 1: baseline -------------------------------------------------------

fresh()


@dlt.resource(name="users", primary_key="id", write_disposition="replace")
def users_v1():
    yield from [
        {"id": 1, "email": "ada@x.com"},
        {"id": 2, "email": "alan@x.com"},
        {"id": 3, "email": "grace@x.com"},
    ]


pipe().run(users_v1())
STATE["step1_rows"] = rows("users")
print(f"step1 users rows = {STATE['step1_rows']}")


# --- Step 2: add a new resource (events) — state-safe -----------------------

@dlt.resource(name="events", primary_key="event_id", write_disposition="append")
def events_v1():
    yield from [
        {"event_id": "e1", "user_id": 1, "ts": "2026-05-19T10:00:00Z"},
        {"event_id": "e2", "user_id": 2, "ts": "2026-05-19T11:00:00Z"},
    ]


pipe().run(events_v1())
STATE["step2_users_rows"] = rows("users")
STATE["step2_events_rows"] = rows("events")
print(f"step2 users rows = {STATE['step2_users_rows']}, events rows = {STATE['step2_events_rows']}")


# --- Step 3: add a `country` column with a backfill default -----------------

@dlt.resource(name="users", primary_key="id", write_disposition="replace")
def users_v3():
    yield from [
        {"id": 1, "email": "ada@x.com",    "country": "UK"},
        {"id": 2, "email": "alan@x.com",   "country": "UK"},
        {"id": 3, "email": "grace@x.com",  "country": "US"},
    ]


pipe().run(users_v3())
STATE["step3_has_country"] = "country" in cols("users")
print(f"step3 users has country col = {STATE['step3_has_country']}")


# --- Step 4: switch replace -> merge ----------------------------------------

@dlt.resource(name="users", primary_key="id", write_disposition="merge")
def users_v4_merge():
    yield from [
        {"id": 1, "email": "ada@x.com",   "country": "UK"},     # unchanged
        {"id": 2, "email": "alan@x.com",  "country": "GB"},     # updated country
        {"id": 3, "email": "grace@x.com", "country": "US"},     # unchanged
        {"id": 4, "email": "linus@x.com", "country": "FI"},     # new row
    ]


pipe().run(users_v4_merge())
STATE["step4_rows"] = rows("users")
gb = duckdb.connect(str(WH)).execute(
    f"SELECT country FROM {DATASET}.users WHERE id = 2"
).fetchone()[0]
STATE["step4_updated"] = gb
print(f"step4 users rows = {STATE['step4_rows']}, id=2 country = {gb}")


# --- Step 5: change primary_key from id to email (DROP + reload) ------------

# DANGER: do not just change primary_key — dlt will not migrate the row identity.
# Correct migration: drop the existing table, set the new key, reload from source.
duckdb.connect(str(WH)).execute(f"DROP TABLE {DATASET}.users")


@dlt.resource(name="users", primary_key="email", write_disposition="merge")
def users_v5():
    yield from [
        {"id": 1, "email": "ada@x.com",   "country": "UK"},
        {"id": 2, "email": "alan@x.com",  "country": "GB"},
        {"id": 3, "email": "grace@x.com", "country": "US"},
        {"id": 4, "email": "linus@x.com", "country": "FI"},
    ]


pipe().run(users_v5())
STATE["step5_rows"] = rows("users")
STATE["step5_pk_is_email"] = True  # by construction
print(f"step5 users rows after PK migration = {STATE['step5_rows']}")


# --- Step 6: rename users -> customers (explicit DROP of old table) ---------

@dlt.resource(name="customers", primary_key="email", write_disposition="merge")
def customers_v6():
    yield from [
        {"id": 1, "email": "ada@x.com",   "country": "UK"},
        {"id": 2, "email": "alan@x.com",  "country": "GB"},
        {"id": 3, "email": "grace@x.com", "country": "US"},
        {"id": 4, "email": "linus@x.com", "country": "FI"},
    ]


pipe().run(customers_v6())

# Show the old-table-lingers problem first:
old_still_there = duckdb.connect(str(WH)).execute(
    "SELECT 1 FROM information_schema.tables WHERE table_schema=? AND table_name='users'",
    [DATASET],
).fetchone()
STATE["step6_old_users_lingers"] = old_still_there is not None
# Clean migration: drop the old table explicitly.
if old_still_there:
    duckdb.connect(str(WH)).execute(f"DROP TABLE {DATASET}.users")

STATE["step6_customers_rows"] = rows("customers")
STATE["step6_users_dropped"] = duckdb.connect(str(WH)).execute(
    "SELECT 1 FROM information_schema.tables WHERE table_schema=? AND table_name='users'",
    [DATASET],
).fetchone() is None
print(f"step6 customers rows = {STATE['step6_customers_rows']}, "
      f"old users table dropped = {STATE['step6_users_dropped']}")
