"""Verify exercise 04."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_columns

header("04-schema-contract")
run_solution(__file__)

evolve_cols  = table_columns("bronze_events_evolve",  "events")
freeze_cols  = table_columns("bronze_events_freeze",  "events")
discard_cols = table_columns("bronze_events_discard", "events")

check("experiment" in evolve_cols, "evolve dataset has 'experiment' column")
check("experiment" not in freeze_cols, "freeze dataset blocked the new column")
check("experiment" not in discard_cols, "discard_value dataset dropped the new column silently")
done()
