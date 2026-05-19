# 21 — Retries, 429s, and backoff

Real APIs return 429 (rate-limited), 503 (overloaded), 502 (upstream timeout), and connection resets. A production resource must retry transient errors, respect `Retry-After`, and **not retry 4xx that aren't 408/429**.

`dlt.sources.helpers.requests` ships a `Client` with sensible retry defaults — use it instead of bare `requests`.

## Goal

Build a resource that hits a deliberately flaky local endpoint (provided as a small Flask-less stub via a sleep+counter mock). Configure:

- Retry on `429, 502, 503, 504, connection errors`.
- Respect `Retry-After`.
- Exponential backoff with jitter, max 5 attempts.
- Hard-fail on `401` / `403` / `404` immediately (no retry).

Show:
1. Wall-clock duration with retries vs without.
2. How many attempts were made.
3. What happens when the budget is exhausted.

## Acceptance

1. Resource loads successfully despite 3 simulated 429s.
2. A second run targeting a "permanent 401" URL fails immediately (no retry).
3. Print the attempt log.

## Hints

- `from dlt.sources.helpers.requests import Client`
- `Client(request_timeout=30, request_max_attempts=5, retry_status_codes=[429, 502, 503, 504], respect_retry_after_header=True)`
- The flaky stub is provided as `flaky_endpoint()` — it returns 429 the first 3 calls then 200.
