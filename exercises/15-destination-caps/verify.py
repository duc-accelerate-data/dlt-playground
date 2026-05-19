"""Verify exercise 15."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_exists, row_count, db

header("15-destination-caps")
run_solution(__file__)

check(table_exists("bronze_products", "products"), "products table loaded")
check(row_count("bronze_products", "products") == 6, "all 6 product rows landed")

dt = db().execute("""
    SELECT data_type FROM information_schema.columns
    WHERE table_schema='bronze_products' AND table_name='products' AND column_name='active'
""").fetchone()
check(dt is not None and "BOOL" in dt[0].upper(),
      f"'active' coerced to BOOLEAN (got {dt})")

null_dates = db().execute(
    "SELECT COUNT(*) FROM bronze_products.products WHERE launched_on IS NULL"
).fetchone()[0]
check(null_dates >= 1, f"missing-date row landed as NULL (got {null_dates})")
done()
