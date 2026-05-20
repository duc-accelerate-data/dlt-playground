"""Reference solution for exercise 28 — modelling techniques.

Three variations of `customers` loaded twice each, showing the practical
difference between replace, SCD2, and JSON-column preservation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import dlt
import duckdb

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

WH = REPO / "data" / "warehouse.duckdb"


def state(version: int):
    if version == 1:
        return [
            {"customer_id": 1, "name": "Ada Lovelace",   "plan": "free",
             "address": {"city": "London", "country": "UK"}},
            {"customer_id": 2, "name": "Alan Turing",    "plan": "free",
             "address": {"city": "London", "country": "UK"}},
        ]
    return [
        {"customer_id": 1, "name": "Ada Lovelace",   "plan": "pro",   # plan changed
         "address": {"city": "London", "country": "UK"}},
        {"customer_id": 2, "name": "Alan Turing",    "plan": "free",
         "address": {"city": "London", "country": "UK"}},
    ]


def run_replace():
    @dlt.resource(name="customers", write_disposition="replace")
    def customers(v):
        yield from state(v)

    duckdb.connect(str(WH)).execute("DROP SCHEMA IF EXISTS customers_replace CASCADE")
    p = dlt.pipeline(pipeline_name="cust_replace",
                     destination=dlt.destinations.duckdb(str(WH)),
                     dataset_name="customers_replace")
    p.run(customers(1))
    p.run(customers(2))


def run_scd2():
    @dlt.resource(name="customers",
                  primary_key="customer_id",
                  write_disposition={"disposition": "merge", "strategy": "scd2"})
    def customers(v):
        yield from state(v)

    duckdb.connect(str(WH)).execute("DROP SCHEMA IF EXISTS customers_scd2 CASCADE")
    p = dlt.pipeline(pipeline_name="cust_scd2",
                     destination=dlt.destinations.duckdb(str(WH)),
                     dataset_name="customers_scd2")
    p.run(customers(1))
    p.run(customers(2))


def run_json():
    @dlt.resource(name="customers",
                  primary_key="customer_id",
                  write_disposition="merge",
                  columns={"address": {"data_type": "json"}})
    def customers(v):
        yield from state(v)

    duckdb.connect(str(WH)).execute("DROP SCHEMA IF EXISTS customers_json CASCADE")
    p = dlt.pipeline(pipeline_name="cust_json",
                     destination=dlt.destinations.duckdb(str(WH)),
                     dataset_name="customers_json")
    p.run(customers(1))
    p.run(customers(2))


if __name__ == "__main__" or __name__ == "__exercise__":
    run_replace()
    run_scd2()
    run_json()

    con = duckdb.connect(str(WH))
    print("\nreplace rows :", con.execute("SELECT COUNT(*) FROM customers_replace.customers").fetchone()[0])
    print("scd2 rows    :", con.execute("SELECT COUNT(*) FROM customers_scd2.customers").fetchone()[0])
    print("json rows    :", con.execute("SELECT COUNT(*) FROM customers_json.customers").fetchone()[0])
