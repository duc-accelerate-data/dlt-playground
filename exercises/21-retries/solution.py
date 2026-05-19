"""Reference solution for exercise 21 — production retry policy.

Uses tenacity directly so we don't depend on dlt's internal Client retry shape
(which has shifted across minor versions). The principles are identical.
"""
import sys, time, json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
import requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type

RETRYABLE = {429, 502, 503, 504}
ATTEMPTS = {"n": 0}


class Transient(Exception):
    pass


class Permanent(Exception):
    pass


def fake_get(url):
    ATTEMPTS["n"] += 1
    if url.endswith("/forbidden"):
        resp = requests.Response(); resp.status_code = 401; resp._content = b'{"err":"nope"}'
        return resp
    if ATTEMPTS["n"] <= 3:
        resp = requests.Response(); resp.status_code = 429
        resp.headers["Retry-After"] = "0"
        return resp
    resp = requests.Response(); resp.status_code = 200
    resp._content = b'[{"id":1,"name":"ok"},{"id":2,"name":"good"}]'
    return resp


@retry(
    retry=retry_if_exception_type(Transient),
    stop=stop_after_attempt(5),
    wait=wait_exponential_jitter(initial=0.2, max=5),
    reraise=True,
)
def fetch(url):
    r = fake_get(url)
    if r.status_code == 200:
        return r.json()
    if r.status_code in RETRYABLE:
        # Honor Retry-After before raising so backoff is additive.
        if (ra := r.headers.get("Retry-After")):
            time.sleep(float(ra))
        raise Transient(f"{r.status_code} {url}")
    raise Permanent(f"{r.status_code} {url}")


@dlt.resource(name="items", primary_key="id", write_disposition="merge")
def items(url: str = "https://example.test/flaky"):
    yield from fetch(url)


pipeline = dlt.pipeline(
    pipeline_name="retries",
    destination=dlt.destinations.duckdb(str(REPO / "data" / "warehouse.duckdb")),
    dataset_name="resilience",
)

t0 = time.perf_counter()
print(pipeline.run(items("https://example.test/flaky")))
print(f"  flaky took {time.perf_counter()-t0:.2f}s after {ATTEMPTS['n']} attempts (3 retries + 1 success).\n")

# Permanent failure should fail fast — no retries.
try:
    ATTEMPTS["n"] = 0
    pipeline.run(items("https://example.test/forbidden"))
except Exception as e:
    print(f"  fast-failed on 401 after {ATTEMPTS['n']} attempt(s): {type(e).__name__}")
