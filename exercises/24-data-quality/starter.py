"""Exercise 24 — validate, redact, bound."""
import sys, hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from pydantic import BaseModel

RAW = [
    {"event_id": "e1", "user_id": "u1", "ts": "2026-05-10T08:00:00Z", "email": "a@b.com", "age": 30},
    {"event_id": "e2", "user_id": "u2", "ts": "2026-05-10T08:01:00Z"},  # ok
    {"event_id": "e3", "ts": "2026-05-10T08:02:00Z"},  # missing user_id -> drop
    {"user_id": "u4", "ts": "2026-05-10T08:03:00Z"},  # missing event_id -> drop
    {"event_id": "e5", "user_id": "u5", "ts": "2026-05-10T08:04:00Z", "email": "c@d.com", "age": 999},
    {"event_id": "e6", "user_id": "u6", "ts": "2026-05-10T08:05:00Z", "email": "e@f.com", "age": 27},
]


class Event(BaseModel):
    event_id: str
    user_id: str
    ts: str
    email: str | None = None
    age: int | None = None


def hash_email(value):
    if not value:
        return None
    return hashlib.sha256(value.encode()).hexdigest()[:16]


# TODO: build a resource with columns=Event, schema_contract={"data_type": "discard_value"}
# TODO: add_filter to require event_id + user_id + ts
# TODO: add_map to redact email
# TODO: run and print resulting table
