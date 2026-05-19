"""Minimal Chess.com source — used by exercises 01, 02, 03, 07, 08."""
from __future__ import annotations

import dlt
from dlt.sources.helpers import requests

BASE = "https://api.chess.com/pub"
HEADERS = {"User-Agent": "dlt-playground (https://github.com/duc-accelerate-data)"}


@dlt.resource(name="player_profile", primary_key="player_id", write_disposition="merge")
def player_profile(usernames: list[str]):
    """One profile row per username. Merge by player_id so re-runs don't accumulate child rows."""
    for u in usernames:
        r = requests.get(f"{BASE}/player/{u}", headers=HEADERS)
        r.raise_for_status()
        yield r.json()


@dlt.resource(name="player_games_archive_index", write_disposition="replace")
def player_games_archive_index(usernames: list[str]):
    """The archive index changes every month — replace is correct."""
    for u in usernames:
        r = requests.get(f"{BASE}/player/{u}/games/archives", headers=HEADERS)
        r.raise_for_status()
        yield {"username": u, "archives": r.json().get("archives", [])}


@dlt.source(name="chess")
def chess_source(usernames: list[str] | None = None):
    usernames = usernames or ["magnuscarlsen", "hikaru"]
    return [
        player_profile(usernames),
        player_games_archive_index(usernames),
    ]
