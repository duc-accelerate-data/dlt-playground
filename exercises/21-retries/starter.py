"""Exercise 21 — retries via dlt.sources.helpers.requests.Client."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from dlt.sources.helpers.requests import Client
from unittest.mock import patch
import requests

ATTEMPTS = {"flaky": 0}


def fake_get(url, *a, **kw):
    """Return 429 the first 3 calls for /flaky, 200 after. /forbidden always 401."""
    ATTEMPTS["flaky"] = ATTEMPTS.get("flaky", 0)
    if url.endswith("/forbidden"):
        resp = requests.Response(); resp.status_code = 401; resp._content = b'{"err":"nope"}'
        return resp
    ATTEMPTS["flaky"] += 1
    resp = requests.Response()
    if ATTEMPTS["flaky"] <= 3:
        resp.status_code = 429
        resp.headers["Retry-After"] = "1"
    else:
        resp.status_code = 200
        resp._content = b'[{"id":1,"name":"ok"}]'
    return resp


# TODO: build a Client with retry policy + a resource that uses it.
# TODO: patch requests.get with fake_get for the demo and run.
