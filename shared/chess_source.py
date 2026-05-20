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
        res = r.json()
        print('--------------', res)
        yield res


@dlt.resource(name="player_stats", primary_key="player_id", write_disposition="merge")
def player_stats(usernames: list[str]):
    """Per-format rating stats — deeply nested, perfect for showing dlt's normalize/flatten."""
    for u in usernames:
        r = requests.get(f"{BASE}/player/{u}/stats", headers=HEADERS)
        r.raise_for_status()
        profile = requests.get(f"{BASE}/player/{u}", headers=HEADERS)
        profile.raise_for_status()
        # tag with player_id so we can merge — /stats endpoint doesn't include it
        res = {"username": u, "player_id": profile.json()["player_id"], **r.json()}
        print('-----\n', res)
        print('-----\n')
        yield res


@dlt.resource(name="player_games_archive_index", write_disposition="replace")
def player_games_archive_index(usernames: list[str]):
    """The archive index changes every month — replace is correct."""
    for u in usernames:
        r = requests.get(f"{BASE}/player/{u}/games/archives", headers=HEADERS)
        r.raise_for_status()
        res = {"username": u, "archives": r.json().get("archives", [])}
        print('-----\n', res)
        print('-----\n')
        yield res


@dlt.source(name="chess")
def chess_source(usernames: list[str] | None = None):
    usernames = usernames or ["magnuscarlsen", "hikaru"]
    return [
        player_profile(usernames),
        player_games_archive_index(usernames),
    ]
