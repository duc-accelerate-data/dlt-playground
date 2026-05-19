# Notes — Config providers + secrets

- **Resolution order:** env vars → `.dlt/secrets.toml` → `.dlt/config.toml` → defaults in code. Env always wins — that's how CI overrides local for free.
- **Env var spelling:** `__` (double underscore) maps to `.` in TOML. `[sources.github_a].access_token` ↔ `SOURCES__GITHUB_A__ACCESS_TOKEN`. Lower / upper case in env is normalized.
- **`section=` is the multi-tenant lever.** One verified-source module, N customers, N tokens. Without `section=`, all callers race for the same `[sources.github]` block — disaster.
- **Never hardcode `access_token=...` in code.** Even in playgrounds — muscle memory matters.
- **Secret managers:** dlt-hub has providers for AWS Secrets Manager, GCP Secret Manager, Vault. Drop them in via `dlt.config.providers` register call at startup; everything else (the `section=` plumbing, the `dlt.secrets.value` defaults) stays the same.
- **Fivetran parallel:** Fivetran "connector instance" ≈ dlt source bound to a specific section.
