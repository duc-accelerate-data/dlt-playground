"""Verify exercise 17."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, db

header("17-schema-inference")
run_solution(__file__)

con = db()


def cols_of(schema: str, table: str) -> dict[str, str]:
    rows = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema=? AND table_name=?",
        [schema, table],
    ).fetchall()
    return {c: t for c, t in rows}


# (1) first-sight
c1 = cols_of("infer_first", "t")
check(c1.get("id", "").lower() in ("bigint", "hugeint"), f"first-sight: id is bigint (got {c1.get('id')})")
check(c1.get("name", "").lower() == "varchar", f"first-sight: name is text/varchar (got {c1.get('name')})")
check("double" in c1.get("score", "").lower() or "float" in c1.get("score", "").lower(), f"first-sight: score is double (got {c1.get('score')})")
check(c1.get("active", "").lower() == "boolean", f"first-sight: active is bool (got {c1.get('active')})")

# (2) nullable — note column exists as text
c2 = cols_of("infer_nullable", "t")
check("note" in c2, f"nullable: note column exists (got cols {list(c2)})")
check("varchar" in c2.get("note", "").lower(), f"nullable: note is text (got {c2.get('note')})")

# (3) iso auto-detect
c3 = cols_of("infer_iso", "t")
check("timestamp" in c3.get("created", "").lower(), f"iso-detect: created is timestamp (got {c3.get('created')})")

# (4) variant column on evolve
c4 = cols_of("infer_variant", "t")
check("x" in c4 and "bigint" in c4["x"].lower(), f"variant: x is still bigint (got {c4.get('x')})")
check("x__v_text" in c4, f"variant: x__v_text was created (got cols {list(c4)})")

# (5) freeze raised — the table either doesn't exist or only has the bigint row
# Easiest check: schema 'infer_freeze' has table 't' with no variant column
c5 = cols_of("infer_freeze", "t")
check("x" in c5 and "x__v_text" not in c5, f"freeze: no variant column created (cols {list(c5)})")

done()
