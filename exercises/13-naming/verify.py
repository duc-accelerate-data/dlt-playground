"""Verify exercise 13."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_columns

header("13-naming")
run_solution(__file__)

snake = {c for c in table_columns("naming_snake", "people") if not c.startswith("_dlt_")}
direct = {c for c in table_columns("naming_direct", "people") if not c.startswith("_dlt_")}

check("first_name" in snake and "favourite_repo" in snake,
      f"snake_case dataset has first_name + favourite_repo (got {sorted(snake)})")
check("FirstName" in direct or "favouriteRepo" in direct,
      f"direct dataset preserved at least one camel-case column (got {sorted(direct)})")
done()
