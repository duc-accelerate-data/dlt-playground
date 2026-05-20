"""Verify exercise 05."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, row_count

header("05-write-disposition")
run_solution(__file__)

replace = row_count("wd_replace", "events")
append  = row_count("wd_append",  "events")
merge   = row_count("wd_merge",   "events")

check(replace == 5,            f"replace -> 5 (got {replace})")
check(append  == 20,           f"append == 20 ({append} == 20")
check(merge   <= append,       f"merge dedup'd to {merge} (≤ append {append})")
check(merge   == 9,            f"merge -> 9 unique events (got {merge})")
done()
