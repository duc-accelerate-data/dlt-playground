# 16 — Config providers + secrets resolution

dlt's config resolver walks providers in order: **env vars → `.dlt/secrets.toml` → `.dlt/config.toml` → code defaults**. Each `@dlt.source` / `@dlt.resource` declares what it needs by typing arguments as `dlt.secrets.value` / `dlt.config.value`. Sections route configuration: `[sources.<section>]` in TOML.

## Goal

Run the same `github_source()` against **two different orgs with different PATs** in a single Python file, without leaking either credential. Use `section=` and `with_args()` to keep them isolated.

## Acceptance

1. `.dlt/secrets.toml` has `[sources.github_a]` and `[sources.github_b]` with their own `access_token`s.
2. Both pipelines run successfully and write to **separate datasets**.
3. Neither token appears anywhere in the code.

## Hints

- `github_source.with_args(section="github_a")` rebinds the section.
- `github_source` already declares `access_token: str = dlt.secrets.value` — the resolver picks up the matching section.
- Same trick works for any verified source — Salesforce prod vs sandbox, two HubSpot portals, etc.

## Bonus

Set `SOURCES__GITHUB_B__ACCESS_TOKEN` as an env var and confirm it wins over `secrets.toml` (env > toml in the resolver).
