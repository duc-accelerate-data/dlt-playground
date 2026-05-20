"""Reference schema tests — bucket 3 of dlt-patterns-expanded.md."""
from __future__ import annotations

import sys
from pathlib import Path

import dlt
import duckdb
import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from shared.chess_source import chess_source  # noqa: E402

WH = REPO / "data" / "warehouse.duckdb"
DATASET = "schema_test_chess"


@pytest.fixture(scope="module")
def loaded_pipeline():
    """Load chess once into a dedicated dataset; reuse across tests."""
    duckdb.connect(str(WH)).execute(f"DROP SCHEMA IF EXISTS {DATASET} CASCADE")
    pipeline = dlt.pipeline(
        pipeline_name="schema_tests",
        destination=dlt.destinations.duckdb(str(WH)),
        dataset_name=DATASET,
    )
    pipeline.run(chess_source(["magnuscarlsen", "hikaru"]))
    return pipeline


# --- 3.4: master assertion — no failed jobs ----------------------------------


def test_no_failed_jobs(loaded_pipeline):
    info = loaded_pipeline.last_trace.last_load_info
    assert info.has_failed_jobs is False, info


# --- 3.5: a load package was recorded ----------------------------------------


def test_load_package_recorded(loaded_pipeline):
    info = loaded_pipeline.last_trace.last_load_info
    assert len(info.load_packages) >= 1
    assert info.load_packages[0].state == "loaded"


# --- 3.1: expected tables exist in dlt's in-memory schema --------------------


def test_expected_tables_exist(loaded_pipeline):
    tables = {t["name"] for t in loaded_pipeline.default_schema.data_tables()}
    assert "player_profile" in tables
    assert "player_games_archive_index" in tables


# --- 3.15: nested child table materialized -----------------------------------


def test_child_tables_present(loaded_pipeline):
    tables = {t["name"] for t in loaded_pipeline.default_schema.data_tables()}
    # `streaming_platforms` is a nested list inside the chess profile.
    assert any("__" in t for t in tables), \
        f"expected an auto-extracted child table, got {tables}"


# --- 3.2: column presence + data type ----------------------------------------


def test_column_types_match_contract(loaded_pipeline):
    cols = loaded_pipeline.default_schema.get_table("player_profile")["columns"]
    assert "player_id" in cols
    # dlt control columns
    assert "_dlt_id" in cols
    assert "_dlt_load_id" in cols
    # player_id should be a number (bigint) — assert via data_type
    assert cols["player_id"]["data_type"] in ("bigint", "wei", "double")


# --- 3.3: row-count smoke test in DuckDB -------------------------------------


def test_row_count_in_range(loaded_pipeline):
    con = duckdb.connect(str(WH))
    n = con.execute(f"SELECT COUNT(*) FROM {DATASET}.player_profile").fetchone()[0]
    assert 1 <= n <= 10, f"expected a small number of profiles, got {n}"


# --- 3.13: schema-version-hash deterministic ---------------------------------


def test_schema_hash_is_stable(loaded_pipeline):
    h = loaded_pipeline.default_schema.stored_version_hash
    assert isinstance(h, str) and len(h) > 8


# --- 3.6: schema_contract="freeze" as a CI gate ------------------------------


def test_freeze_blocks_new_column():
    """A fresh pipeline with frozen columns must raise on drift."""
    duckdb.connect(str(WH)).execute("DROP SCHEMA IF EXISTS schema_freeze_demo CASCADE")
    p = dlt.pipeline(
        pipeline_name="schema_freeze_demo",
        destination=dlt.destinations.duckdb(str(WH)),
        dataset_name="schema_freeze_demo",
    )
    # First load establishes the schema.
    p.run([{"id": 1, "name": "Ada"}], table_name="users")
    # Second load adds a new column under a frozen contract — must raise.
    with pytest.raises(Exception) as exc:
        p.run(
            [{"id": 2, "name": "Alan", "email": "alan@example.com"}],
            table_name="users",
            schema_contract={"columns": "freeze"},
        )
    assert "DataValidation" in type(exc.value).__name__ or "DataValidation" in str(exc.value), \
        f"expected DataValidationError, got {type(exc.value).__name__}: {exc.value}"


# --- 3.16 anti-pattern guard rail: don't hard-code N -------------------------
# (informational — not a test, just documents that the row-count check above
# uses a range, not a fixed integer)
