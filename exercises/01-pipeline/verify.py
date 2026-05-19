"""Verify exercise 01."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_exists, row_count, table_columns

header("01-pipeline")
run_solution(__file__)

check(table_exists("bronze_chess", "player_profile"), "table bronze_chess.player_profile exists")
check(row_count("bronze_chess", "player_profile") == 3, "exactly 3 player rows")
cols = table_columns("bronze_chess", "player_profile")
check("_dlt_id" in cols and "_dlt_load_id" in cols, "control columns present")
done()
