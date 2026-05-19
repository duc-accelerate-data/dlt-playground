"""Verify exercise 09."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, schema_exists

header("09-dataset-name")
os.environ.setdefault("DLT_ENV", "dev")
run_solution(__file__)
check(schema_exists(f"bronze_chess_{os.environ['DLT_ENV']}"),
      f"dataset bronze_chess_{os.environ['DLT_ENV']} exists")
done()
