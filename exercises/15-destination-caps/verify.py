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
# dlt infers types from yielded values; csv.DictReader yields strings, so 'active' lands
# as VARCHAR even though DuckDB advertises BOOLEAN. The pedagogical point: destination
# *capabilities* describe what's possible; the resource's *shape* decides what's stored.
check(dt is not None, f"'active' column landed (inferred type = {dt})")

empty_dates = db().execute(
    "SELECT COUNT(*) FROM bronze_products.products WHERE launched_on IS NULL OR launched_on = ''"
).fetchone()[0]
check(empty_dates >= 1, f"missing-date row preserved as NULL/empty (got {empty_dates})")
done()
