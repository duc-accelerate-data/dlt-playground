"""Exercise 14 — primary_key vs merge_key vs dedup_sort, using synthetic events."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt


# A small in-memory dataset with two rows sharing event_id and different updated_at.
def two_versions():
    yield {"event_id": "e1", "user_id": "u1", "ts": "2026-05-10T08:00:00Z",
           "updated_at": "2026-05-10T08:00:00Z", "value": "v1"}
    yield {"event_id": "e1", "user_id": "u1", "ts": "2026-05-10T08:00:00Z",
           "updated_at": "2026-05-10T09:00:00Z", "value": "v2"}


# TODO: build three resources with different hints (primary_key, merge_key, dedup_sort)
#       and run each into its own dataset. Inspect which row wins.
