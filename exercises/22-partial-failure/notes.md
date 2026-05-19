# Notes — Partial failure + resume

- **Per-package atomicity.** A package commits in one transaction (or in one staged-file load for warehouses). Mid-package crashes leave no half-state in the destination.
- **Failed packages are visible.** `_dlt_loads.status != 0` rows are how SREs find aborted loads to investigate. Don't silently delete them.
- **Resume vs replay.** dlt resumes a *staged* package — extract output already on disk gets normalized and loaded next run. If the crash was in the extract generator before staging, the *source* re-runs.
- **Source replayability is your responsibility.** If your source is "drain this Kafka topic into bronze," you need a checkpoint store. dlt's resume only helps with downstream stages.
- **`pipeline.has_pending_data`** is True between extract and load — use it in CI ("did the last run finish cleanly?").
- **Production discipline:** alert on `_dlt_loads.status != 0`. Hook into `LoadInfo.has_failed_jobs` in CI.
- **Re-running with `dev_mode=True` wipes the working dir** — never use it when you actually want resume.
