"""Verify exercise 13."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_columns

header("13-naming")
run_solution(__file__)

snake = table_columns("naming_snake", "people")
direct = table_columns("naming_direct", "people")

check("first_name" in snake and "favourite_repo" in snake,
      "snake_case produced first_name + favourite_repo")
check("FirstName" in direct and "favouriteRepo" in direct,
      "direct preserved FirstName + favouriteRepo verbatim")
done()
