"""Reference business data checks — bucket 4 of dlt-patterns-expanded.md.

Loads a small synthetic orders dataset, then asserts both recon (source vs
destination) and business rules (no negatives, no orphans, required fields).
"""
from __future__ import annotations

import sys
from pathlib import Path

import dlt
import duckdb
import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

WH = REPO / "data" / "warehouse.duckdb"
DATASET = "business_checks"


ORDERS = [
    {"order_id": 1, "customer_id": 100, "status": "paid",      "total_cents": 4990,  "currency": "USD"},
    {"order_id": 2, "customer_id": 100, "status": "paid",      "total_cents": 12990, "currency": "USD"},
    {"order_id": 3, "customer_id": 200, "status": "cancelled", "total_cents": 990,   "currency": "USD"},
    {"order_id": 4, "customer_id": 300, "status": "shipped",   "total_cents": 24990, "currency": "USD"},
    {"order_id": 5, "customer_id": 300, "status": "pending",   "total_cents": 9990,  "currency": "USD"},
    {"order_id": 6, "customer_id": 500, "status": "paid",      "total_cents": 4990,  "currency": "EUR"},
]
LINE_ITEMS = [
    {"order_id": 1, "sku": "BOOK-CALC", "qty": 1, "price_cents": 4990},
    {"order_id": 2, "sku": "BOOK-CALC", "qty": 1, "price_cents": 4990},
    {"order_id": 2, "sku": "STICKER",   "qty": 4, "price_cents": 2000},
    {"order_id": 3, "sku": "MUG",       "qty": 1, "price_cents": 990},
    {"order_id": 4, "sku": "BOOK-COBOL","qty": 2, "price_cents": 12495},
    {"order_id": 5, "sku": "TSHIRT",    "qty": 1, "price_cents": 9990},
    {"order_id": 6, "sku": "BOOK-EU",   "qty": 1, "price_cents": 4990},
]


@pytest.fixture(scope="module")
def loaded():
    duckdb.connect(str(WH)).execute(f"DROP SCHEMA IF EXISTS {DATASET} CASCADE")
    p = dlt.pipeline(
        pipeline_name="business_checks",
        destination=dlt.destinations.duckdb(str(WH)),
        dataset_name=DATASET,
    )

    @dlt.resource(name="orders", primary_key="order_id", write_disposition="merge")
    def orders():
        yield from ORDERS

    @dlt.resource(name="order_items",
                  primary_key=("order_id", "sku"),
                  write_disposition="merge")
    def order_items():
        yield from LINE_ITEMS

    p.run([orders(), order_items()])
    return duckdb.connect(str(WH))


# --- Recon: row counts -------------------------------------------------------


def test_source_destination_rowcount_recon(loaded):
    """The destination must have exactly as many orders as the fixture."""
    n = loaded.execute(f"SELECT COUNT(*) FROM {DATASET}.orders").fetchone()[0]
    assert n == len(ORDERS), \
        f"orders rowcount drift: source={len(ORDERS)} destination={n}"


# --- Recon: monetary sum -----------------------------------------------------


def test_total_amount_sums_match(loaded):
    expected = sum(o["total_cents"] for o in ORDERS)
    actual = loaded.execute(
        f"SELECT SUM(total_cents) FROM {DATASET}.orders"
    ).fetchone()[0]
    assert actual == expected, \
        f"sum(total_cents) drift: expected={expected} actual={actual}"


# --- Rule: no negatives ------------------------------------------------------


def test_no_negative_totals(loaded):
    bad = loaded.execute(
        f"SELECT order_id, total_cents FROM {DATASET}.orders WHERE total_cents < 0"
    ).fetchall()
    assert not bad, f"orders with negative totals: {bad}"


# --- Rule: every order has at least one line item (referential parent→child) -


def test_every_order_has_a_line_item(loaded):
    orphans = loaded.execute(f"""
        SELECT o.order_id
        FROM {DATASET}.orders o
        LEFT JOIN {DATASET}.order_items li USING (order_id)
        WHERE li.order_id IS NULL
    """).fetchall()
    assert not orphans, f"orders without line items: {orphans}"


# --- Rule: no orphan children (child→parent integrity) -----------------------


def test_no_orphan_children(loaded):
    orphans = loaded.execute(f"""
        SELECT li.order_id
        FROM {DATASET}.order_items li
        LEFT JOIN {DATASET}.orders o USING (order_id)
        WHERE o.order_id IS NULL
    """).fetchall()
    assert not orphans, f"line items pointing at non-existent order: {orphans}"


# --- Rule: required fields are populated -------------------------------------


def test_required_fields_not_null(loaded):
    for col in ("order_id", "customer_id", "status", "total_cents", "currency"):
        nulls = loaded.execute(
            f"SELECT COUNT(*) FROM {DATASET}.orders WHERE {col} IS NULL"
        ).fetchone()[0]
        assert nulls == 0, f"{col} has {nulls} NULL rows in orders"


# --- Distribution: no status dominates more than 70% -------------------------


def test_status_distribution_is_balanced(loaded):
    rows = loaded.execute(f"""
        SELECT status, COUNT(*) * 1.0 / (SELECT COUNT(*) FROM {DATASET}.orders) AS pct
        FROM {DATASET}.orders
        GROUP BY status
        ORDER BY pct DESC
    """).fetchall()
    top_status, top_pct = rows[0]
    assert top_pct <= 0.70, \
        f"single status '{top_status}' dominates at {top_pct:.0%} (>70% threshold)"
