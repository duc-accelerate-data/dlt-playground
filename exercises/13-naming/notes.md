# Notes — Naming convention

- **Cross-destination foot-gun.** Default `snake_case` works everywhere. Switching to `direct` and then deploying to a destination with shorter identifier limits (Fabric, Synapse, older Snowflake) silently truncates and collisions become silent dupes.
- **Locked once data lands.** Once a table exists, you can't switch its naming convention without rebuilding. Set it in `.dlt/config.toml` from day 1 and treat changes as a migration.
- **Custom conventions** (subclass `NamingConvention`) are how dlt-hub users handle vendor-specific oddities — e.g., always uppercasing for Snowflake-classic users.
- **Flattening uses `__`.** Predictable, but check your downstream tooling — some dbt adapters dislike double underscores in column names.
- **Common pattern:** keep dlt naming = `snake_case`, then in dbt rename via a one-line model: `select foo as foo_dlt_id from ...`.
