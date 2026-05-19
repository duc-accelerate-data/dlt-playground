# 23 — Streaming pagination + memory

A naïve resource does `r.json()` and yields the whole array. With a 2 GB response, your worker OOMs. Production resources yield *per page* (or even per record) so the pipeline runs in bounded memory.

## Goal

Build a resource that fakes a paginated source of 100 pages × 1000 records (100k total). Compare:

- **Naïve**: `yield list(all_records)` — accumulates in memory.
- **Streaming**: `yield from page; del page` — bounded memory.

Measure peak RSS for both. Then add `chunk_size` (rows per file) to the streaming version and observe load-file count.

## Acceptance

1. Streaming version's peak RSS is materially smaller than naïve.
2. With `chunk_size=10_000`, dlt writes ~10 load files instead of 1 mega-file.
3. Final row counts match (100,000) for both.

## Hints

- `import resource; resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` for RSS on macOS/Linux.
- `chunk_size` is set on the resource: `@dlt.resource(..., chunk_size=10_000)`.
- Generator vs list — basic Python; the dlt twist is that dlt only buffers one `chunk_size` window.
