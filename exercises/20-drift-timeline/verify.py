"""Verify exercise 20."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_columns

header("20-drift-timeline")
run_solution(__file__)

permissive = table_columns("drift_permissive", "people")
check("email" in permissive, "permissive: v2's `email` column landed")
check("full_name" in permissive, "permissive: v3's `full_name` column landed")
check("name" in permissive, "permissive: original `name` lingers (rename gap)")

strict = table_columns("drift_strict", "people")
check("email" not in strict, "strict: v2's `email` blocked by freeze")

hybrid = table_columns("drift_hybrid", "people")
check("email" in hybrid and "full_name" in hybrid,
      "hybrid: v2/v3 columns allowed (columns: evolve)")
done()
