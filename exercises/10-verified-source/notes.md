# Notes — Verified source + hints

- **`.with_resources(...)` is your subset selector.** dlt-hub verified sources ship dozens of resources (Salesforce has 50+) — you almost never want all of them. Pick the ones in your Pipeline Inventory.
- **`apply_hints(...)` overrides decorator defaults.** Centralize policy in your *pipeline file*, not in the vendor module. That way vendor upgrades don't clobber your contract.
- **Add hints, don't fork.** If you find yourself editing `verified-sources/sources/github/`, stop and reach for `apply_hints` first.
- **Combine with `.with_args(section=...)`** for multi-tenant ingestion — see exercise 16.
- **dlt-hub's own example:** verified `salesforce` source declares no contract; their docs recommend the consumer set `{tables: evolve, columns: freeze, data_type: freeze}` at the source via `apply_hints` per resource.
