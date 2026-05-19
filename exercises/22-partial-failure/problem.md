# 22 — Partial failure + resume

`pipeline.run()` is **atomic per load package**: rows in a package either all commit or none. But a package can span multiple resources, and within one resource the extractor can crash mid-way. dlt persists extract/normalize artifacts on disk so the *next* run resumes — you don't re-extract what was already staged.

## Goal

Simulate a crash during the normalize stage (raise after yielding 2 of 5 records). Then re-run *without* `dev_mode=True` and observe dlt resume the load package — final row count should be 5, not 2 or 7.

## Acceptance

1. First run aborts with an exception after 2 yields. No row appears in the destination.
2. `_dlt_loads` shows the aborted package with `status != 0` or no row at all (depending on stage).
3. Second run completes with all 5 rows.
4. Print the `pipeline.last_trace` or working-dir contents between runs to see staged files.

## Hints

- `pipeline.has_pending_data` is True if there are unloaded packages.
- Raise inside the generator after the second yield.
- On rerun, dlt finds staged data in `~/.dlt/pipelines/<pipeline_name>/` and proceeds.
- This is *not* the same as exactly-once at the source level — the *source* must be replayable.
