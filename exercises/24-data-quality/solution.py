"""Reference solution for exercise 24."""
import sys, hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt, duckdb
from pydantic import BaseModel, Field

WH = REPO / "data" / "warehouse.duckdb"

RAW = [
    {"event_id": "e1", "user_id": "u1", "ts": "2026-05-10T08:00:00Z", "email": "a@b.com", "age": 30},
    {"event_id": "e2", "user_id": "u2", "ts": "2026-05-10T08:01:00Z"},
    {"event_id": "e3", "ts": "2026-05-10T08:02:00Z"},
    {"user_id": "u4", "ts": "2026-05-10T08:03:00Z"},
    {"event_id": "e5", "user_id": "u5", "ts": "2026-05-10T08:04:00Z", "email": "c@d.com", "age": 999},
    {"event_id": "e6", "user_id": "u6", "ts": "2026-05-10T08:05:00Z", "email": "e@f.com", "age": 27},
]

REQUIRED = ("event_id", "user_id", "ts")


class Event(BaseModel):
    event_id: str
    user_id: str
    ts: str
    email: str | None = None
    age: int | None = Field(default=None, ge=0, le=120)


def hash_email(v):
    return hashlib.sha256(v.encode()).hexdigest()[:16] if v else None


@dlt.resource(
    name="events",
    primary_key="event_id",
    write_disposition="merge",
    columns=Event,
    schema_contract={"data_type": "discard_value"},
)
def events():
    yield from RAW


res = events()
res.add_filter(lambda x: all(k in x and x[k] for k in REQUIRED))
res.add_map(lambda x: {**x, "email": hash_email(x.get("email"))})

p = dlt.pipeline(
    pipeline_name="dq",
    destination=dlt.destinations.duckdb(str(WH)),
    dataset_name="bronze_dq",
    dev_mode=True,
)
print(p.run(res))

rows = duckdb.connect(str(WH)).execute(
    "SELECT event_id, email, age FROM bronze_dq.events ORDER BY event_id"
).fetchall()
for r in rows:
    print(" ", r)
print(f"final row count = {len(rows)} (expected 4)")
