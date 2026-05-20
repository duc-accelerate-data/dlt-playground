"""Verify exercise 18."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, db

header("18-idempotency")
run_solution(__file__)

con = db()


def count(schema: str, table: str = "t") -> int:
    return con.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]


def cols(schema: str, table: str) -> list[str]:
    return [r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema=? AND table_name=?", [schema, table]
    ).fetchall()]


# (1) append not idempotent
check(count("idem_append") == 4, f"append: 4 rows after 2 runs (got {count('idem_append')})")

# (2) merge + PK is idempotent
check(count("idem_merge") == 2, f"merge+PK: 2 rows after 2 runs (got {count('idem_merge')})")

# (3) dev_mode creates multiple schemas
schemas = [r[0] for r in con.execute(
    "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'idem_dev%'"
).fetchall()]
check(len(schemas) >= 2, f"dev_mode: at least 2 timestamped schemas exist (got {len(schemas)}: {schemas})")

# (4) schema drift: row stable, columns grew
check(count("idem_drift") == 1, f"drift: 1 row (got {count('idem_drift')})")
drift_cols = [c for c in cols("idem_drift", "t") if not c.startswith("_dlt_")]
check("email" in drift_cols, f"drift: email column was added (cols {drift_cols})")

# (5) No PK -> no content dedup. Both identical rows survive.
no_pk_rows = count("idem_collision")
check(no_pk_rows == 2, f"no PK: 2 identical rows -> both survive (got {no_pk_rows}). Fix: declare primary_key.")

done()
