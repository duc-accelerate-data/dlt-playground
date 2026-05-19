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


@dlt.transformer(
    name="player_archive_url",
    data_from=player_profile,
    write_disposition="replace",
)
def player_archive_url(profile):
    r = requests.get(f"{BASE}/player/{profile['username']}/games/archives")
    r.raise_for_status()
    for url in r.json().get("archives", []):
        # dlt will inject _dlt_parent_id pointing at the parent's _dlt_id automatically.
        yield {"archive_url": url}


pipeline = dlt.pipeline(
    pipeline_name="chess_bronze",
    destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
    dataset_name="bronze_chess",
)
print(pipeline.run([player_profile(["magnuscarlsen", "hikaru"]), player_archive_url]))
