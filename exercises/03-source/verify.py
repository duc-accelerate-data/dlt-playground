"""Verify exercise 03."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_exists, db

header("03-source")
run_solution(__file__)

check(table_exists("bronze_chess", "player_profile"), "player_profile present")
check(table_exists("bronze_chess", "country_stats"), "country_stats present")

# Both tables should share at least one load_id (single atomic load package per run).
shared = db().execute("""
    SELECT 1
    FROM bronze_chess.player_profile p
    JOIN bronze_chess.country_stats  c ON p._dlt_load_id = c._dlt_load_id
    LIMIT 1
""").fetchone()
check(shared is not None, "player_profile + country_stats share a load_id (one package)")
done()
