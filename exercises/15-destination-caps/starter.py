"""Exercise 15 — destination capabilities + dirty-type coercion."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.synthetic_source import products

dest = dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb"))
# TODO: print dest.capabilities()
# TODO: build a pipeline writing into dataset "bronze_products" and run products()
# TODO: print column types from the resulting schema
