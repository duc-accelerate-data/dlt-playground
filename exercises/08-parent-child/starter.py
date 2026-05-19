"""Exercise 08 — parent / child transformer."""
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


# TODO: build a transformer that takes a profile row and yields one row per archive URL.
def player_archive_url(profile):
    ...


pipeline = dlt.pipeline(
    pipeline_name="chess_bronze",
    destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
    dataset_name="bronze_chess",
)
pipeline.run([player_profile(["magnuscarlsen", "hikaru"]), player_archive_url])
