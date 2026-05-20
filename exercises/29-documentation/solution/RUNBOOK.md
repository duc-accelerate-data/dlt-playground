# RUNBOOK — github bronze pipeline

> Owner: data-eng@accelerate-data — Slack #data-eng — on-call: PagerDuty `data-eng`

## What this pipeline does

Loads GitHub org/repo + issues into bronze for downstream silver models. Runs hourly via the orchestrator.

| Resource | Endpoint                                | Auth        | Cursor       | Write disposition |
|----------|-----------------------------------------|-------------|--------------|--------------------|
| repos    | `/orgs/{org}/repos`                     | Bearer PAT  | none         | merge by `id`      |
| issues   | `/repos/{org}/{repo}/issues?since=...`  | Bearer PAT  | `updated_at` | merge by `id`      |

Bronze location: `bronze_github` dataset on the analytics warehouse.

## Backfill from cold

Use when first deploying, or after rotating tokens / changing the org.

```bash
# 1. Drop pipeline state so the cursor resets to initial_value.
dlt pipeline github_bronze drop --drop-all

# 2. Re-run from beginning of time.
GITHUB_INITIAL_VALUE="1970-01-01T00:00:00Z" python pipelines/github.py
```

Expected runtime: ~3 min for dlt-hub, ~15 min for a 1k-repo org.

## Rollback a specific load

Use when a bad PAT or upstream bug poisoned a load. Find the `load_id` from
`_dlt_loads`, then delete its rows from every data table:

```sql
-- 1. find the bad load
SELECT load_id, inserted_at, status FROM bronze_github._dlt_loads
ORDER BY inserted_at DESC LIMIT 10;

-- 2. delete its rows (repeat per data table)
DELETE FROM bronze_github.repos  WHERE _dlt_load_id = '<load_id>';
DELETE FROM bronze_github.issues WHERE _dlt_load_id = '<load_id>';
-- ...for all data tables in the schema
```

## Common errors

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `401 Unauthorized` | PAT expired or revoked | Rotate token in [sources.github] secret, re-deploy |
| `403 rate limit exceeded` | hit 5k/hr authenticated cap | Wait until the `X-RateLimit-Reset` header time, or shard by org |
| `_dlt_loads.status != 0` | mid-load crash | Re-run pipeline; dlt resumes the staged package |
| schema drift exception (`DataValidationError`) | vendor added a field | Review the new column, update Pydantic / `columns=`, ship a migration |

## Alerts

- **Page**: `_dlt_loads.status != 0` for > 2 consecutive runs.
- **Warn**: row count drops > 20% week-over-week.
- **Warn**: schema hash changed.

## Who to call

- Data-eng on-call (PagerDuty)
- GitHub admin: it@accelerate-data (for PAT issues)
