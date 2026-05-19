"""Exercise 23 — naïve list vs streaming generator."""
import sys, resource
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt

PAGES, PAGE_SIZE = 100, 1000


def fake_page(p):
    return [{"i": p * PAGE_SIZE + j, "payload": "x" * 200} for j in range(PAGE_SIZE)]


# TODO: build naive_resource that accumulates all rows in a list before yielding.
# TODO: build stream_resource that yields page-by-page.
# TODO: run both into separate datasets and print peak RSS.
