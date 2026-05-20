"""Tiny verification helper shared by every exercise's verify.py.

Usage:
    from shared.verify import header, check, done, run_solution, db

    header("01-pipeline")
    run_solution(__file__)                 # exec solution.py in this exercise's folder
    rows = db().execute("SELECT COUNT(*) FROM bronze_chess.player_profile").fetchone()[0]
    check(rows == 3, f"player_profile has 3 rows (got {rows})")
    done()
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parent.parent
WAREHOUSE = REPO / "data" / "warehouse.duckdb"

_FAILED = False


def header(name: str) -> None:
    print(f"\n=== verifying {name} ===")


def check(cond: bool, msg: str) -> None:
    global _FAILED
    if cond:
        print(f"  ✓ {msg}")
    else:
        print(f"  ✗ FAIL: {msg}")
        _FAILED = True


def done() -> None:
    if _FAILED:
        print("\n✗ ONE OR MORE CHECKS FAILED")
        sys.exit(1)
    print("\n✓ ALL CHECKS PASSED")


def run_solution(verify_file: str | Path) -> None:
    """Execute the sibling solution.py (default) — or starter.py if
    EXERCISE_SOURCE=starter.py is set. Used by verify.py and verify_starter.py.
    """
    import os
    source = os.environ.get("EXERCISE_SOURCE", "solution.py")
    sol = Path(verify_file).resolve().parent / source
    if not sol.exists():
        raise FileNotFoundError(sol)
    print(f"  (running {source})")
    runpy.run_path(str(sol), run_name="__exercise__")


def db() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(WAREHOUSE), read_only=False)


def schema_exists(name: str) -> bool:
    return bool(db().execute(
        "SELECT 1 FROM information_schema.schemata WHERE schema_name = ?", [name]
    ).fetchone())


def table_exists(schema: str, table: str) -> bool:
    return bool(db().execute(
        "SELECT 1 FROM information_schema.tables WHERE table_schema=? AND table_name=?",
        [schema, table],
    ).fetchone())


def table_columns(schema: str, table: str) -> set[str]:
    return {
        r[0]
        for r in db().execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema=? AND table_name=?",
            [schema, table],
        ).fetchall()
    }


def row_count(schema: str, table: str) -> int:
    return db().execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]
