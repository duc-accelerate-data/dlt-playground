# Notes — Resource

- **Resource name = table name.** Singular, snake_case (`country_stat` for one-row-per-thing, plural for collections). dlt's verified sources follow this.
- **Resources are lazy.** Calling `country_stats("US")` returns a *resource instance* — nothing fires until `pipeline.run()` iterates it.
- **`@dlt.resource(standalone=True)`** lets a resource be called directly without a parent source. Useful when one entity has its own auth or schedule.
- **Industry idiom:** keep API plumbing inside the resource (URL building, pagination, retries). Don't pre-shape data in the resource — let the normalizer handle it. The resource's job is *yield raw records*.
- **`@dlt.transformer`** (covered in exercise 08) is a resource fed by another resource — used for parent/child fan-out.
