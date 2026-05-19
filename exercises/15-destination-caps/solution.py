"""Reference solution for exercise 15."""
import sys
from pathlib import Path
from pprint import pprint

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt, duckdb
from shared.synthetic_source import products

dest = dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb"))

caps = dest.capabilities()
print("\n-- DuckDB destination capabilities --")
pprint({
    "max_identifier_length": caps.max_identifier_length,
    "max_column_identifier_length": caps.max_column_identifier_length,
    "supported_merge_strategies": caps.supported_merge_strategies,
    "supported_loader_file_formats": caps.supported_loader_file_formats,
    "naming_convention": caps.naming_convention,
    "supports_truncate_command": caps.supports_truncate_command,
})

pipeline = dlt.pipeline(
    pipeline_name="products_bronze",
    destination=dest,
    dataset_name="bronze_products",
    dev_mode=True,
)
pipeline.run(products())

cols = pipeline.default_schema.get_table("products")["columns"]
print("\n-- inferred column types --")
for name, spec in cols.items():
    if not name.startswith("_dlt_"):
        print(f"  {name:<14} {spec.get('data_type')}")

print("\n-- sample rows --")
print(duckdb.connect(str(REPO / "data" / "warehouse.duckdb"))
      .execute("SELECT sku, active, launched_on FROM bronze_products.products").fetchall())
