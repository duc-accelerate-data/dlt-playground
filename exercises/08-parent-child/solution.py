"""Reference solution for exercise 08."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from dlt.sources.helpers import requests

BASE = "https://api.chess.com/pub"


@dlt.resource(name="player_profile", primary_key="player_id", write_disposition="merge")
def player_profile(usernames):
    for u in usernames:
        r = requests.get(f"{BASE}/player/{u}")
        r.raise_for_status()
        yield r.json()


# Bind the parent BEFORE the transformer references it via data_from, so dlt knows
# which arguments to feed.
_parent = player_profile(["magnuscarlsen", "hikaru"])


@dlt.transformer(
    name="player_archive_url",
    data_from=_parent,
    write_disposition="replace",
)
def player_archive_url(profile):
    r = requests.get(f"{BASE}/player/{profile['username']}/games/archives")
    r.raise_for_status()
    for url in r.json().get("archives", []):
        # Transformer-emitted child tables in dlt 1.x don't auto-inject _dlt_parent_id;
        # capture the parent's PK explicitly so the join is restorable downstream.
        yield {"player_id": profile["player_id"], "archive_url": url}


pipeline = dlt.pipeline(
    pipeline_name="chess_bronze",
    destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
    dataset_name="bronze_chess",
)
print(pipeline.run([_parent, player_archive_url]))
