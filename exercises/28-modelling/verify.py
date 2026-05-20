"""Verify exercise 28."""
import os
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, db, row_count, table_columns

EX = Path(__file__).resolve().parent
SRC = os.environ.get("EXERCISE_SOURCE", "solution")

header("28-modelling")
sol = EX / SRC / "solution.py"
if not sol.exists():
    check(False, f"no solution at {sol}")
    done()
runpy.run_path(str(sol), run_name="__exercise__")

# 1. replace — only the final state
check(row_count("customers_replace", "customers") == 2,
      f"replace dataset = 2 rows (got {row_count('customers_replace', 'customers')})")

# 2. SCD2 — historical row visible via _dlt_valid_to
scd2_n = row_count("customers_scd2", "customers")
check(scd2_n >= 3, f"SCD2 dataset has at least 3 rows (got {scd2_n}) — retired + current versions")

retired = db().execute(
    "SELECT COUNT(*) FROM customers_scd2.customers WHERE _dlt_valid_to IS NOT NULL"
).fetchone()[0]
check(retired >= 1,
      f"at least one SCD2 row has non-null _dlt_valid_to (got {retired} retired rows)")

# 3. JSON preservation — `address` column is JSON-typed, queryable as such
json_cols = table_columns("customers_json", "customers")
check("address" in json_cols, "json dataset preserves `address` as a top-level column")

addr_type = db().execute(
    "SELECT data_type FROM information_schema.columns "
    "WHERE table_schema='customers_json' AND table_name='customers' AND column_name='address'"
).fetchone()
check(addr_type is not None and "JSON" in addr_type[0].upper(),
      f"address column is JSON-typed in DuckDB (got {addr_type})")

# Queryable as JSON
city = db().execute(
    "SELECT address->>'city' FROM customers_json.customers WHERE customer_id=1"
).fetchone()
check(city is not None and city[0] == "London",
      f"can query nested JSON path address->>'city' (got {city})")

done()
