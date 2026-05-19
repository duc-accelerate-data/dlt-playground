# Notes — Source

- **Source = grouping unit**, not a magic structure. dlt-hub verified sources are just one `@dlt.source` per vendor with N resources.
- **Source-level hints cascade** to all its resources unless overridden. Set `schema_contract` once on the source instead of repeating it on every resource.
- **One load package per `pipeline.run(source())` call.** Multiple resources from the same source share an atomic load — they all commit or none do. This is the *whole point* of grouping.
- **Section discipline.** Sources resolve config under `[sources.<name>]`. If you run two `salesforce` connections, give them distinct sections (`section="salesforce_prod"`, `section="salesforce_sandbox"`) so credentials don't collide.
- **Fivetran parallel:** Source ≈ Fivetran "connector". Don't put every vendor in one mega-source.
