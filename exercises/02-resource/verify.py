"""Verify exercise 02."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_exists, row_count, db

header("02-resource")
run_solution(__file__)

check(table_exists("bronze_chess", "country_stats"), "country_stats table exists")
check(row_count("bronze_chess", "country_stats") == 1, "exactly 1 row")
n = db().execute("SELECT player_count FROM bronze_chess.country_stats").fetchone()[0]
check(n > 0, f"player_count > 0 (got {n})")
done()
