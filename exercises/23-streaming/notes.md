# Notes — Streaming + memory

- **Yield, don't return.** A resource is a generator. `return all_rows` defeats the whole streaming design.
- **`chunk_size`** = how many rows dlt buffers before writing a load file. Default 5000. Increase for fewer-larger files (better for warehouse `COPY`); decrease for tighter memory.
- **`buffer_max_items`** in `[normalize]` config controls in-memory normalize buffer — usually 1000 is plenty.
- **Pagination tips:**
  - REST: `yield page_records` per page; `del page` between iterations.
  - SQL: stream rows via cursor — never `cur.fetchall()` on a 50M-row table.
  - S3 / GCS: chunked reads via `smart_open` or the SDK's streaming option.
- **Parquet > JSONL for staging** on big loads. Set `pipeline.run(..., loader_file_format="parquet")` when the destination supports it.
- **Memory bug detection:** the `ru_maxrss` trick in this exercise is rough. For real profiling, `psutil.Process().memory_info().rss` sampled in a thread, or `memory_profiler`.
- **dlt-hub blog "performance optimization":** the two highest-impact knobs are `chunk_size` and `parallelism` — `extract_workers`, `normalize_workers`, `load_workers` in the runtime config.
