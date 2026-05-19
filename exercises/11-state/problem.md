# 11 — State

dlt keeps two state scopes:
- **Pipeline state** — survives runs, stores incremental cursors.
- **Resource state** — `dlt.current.resource_state()` lets a resource stash custom KV (last-seen ETag, last sync timestamp, dedup window).

## Goal

Write a resource that calls `https://api.github.com/orgs/dlt-hub/repos` and uses an **ETag** to avoid re-downloading unchanged data. Store the ETag in resource state.

## Acceptance

1. First run: downloads and yields repos.
2. Second run: server returns 304 Not Modified — the resource yields nothing, no rows added.
3. State printed: `{'etag': 'W/"..."'}`.

## Hints

- `state = dlt.current.resource_state()` — dict-like.
- Send `If-None-Match: <etag>` header.
- On 304, return early (yield nothing).
- Save `r.headers["ETag"]` into state on 200.
