"""Reference solution for exercise 03."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from dlt.sources.helpers import requests
from shared.chess_source import player_profile


@dlt.resource(name="country_stats", write_disposition="replace")
def country_stats(code: str = "US"):
    r = requests.get(f"https://api.chess.com/pub/country/{code}/players")
    r.raise_for_status()
    yield {"country": code, "player_count": len(r.json().get("players", []))}


@dlt.source(name="chess")
def chess(usernames=("magnuscarlsen", "hikaru"), country="US"):
    return [
        player_profile(list(usernames)),
        country_stats(country),
    ]


pipeline = dlt.pipeline(
    pipeline_name="chess_bronze",
    destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
    dataset_name="bronze_chess",
)
print(pipeline.run(chess()))
