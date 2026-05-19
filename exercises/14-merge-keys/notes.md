# Notes — Merge keys / dedup

- **`primary_key`** = "this column uniquely identifies the row across loads". Affects `_dlt_id` derivation too.
- **`merge_key`** = "find existing rows by this combination and delete them before insert". No uniqueness requirement. Composite is supported.
- **`dedup_sort=(field, "desc")`** is the *deterministic late-arrival winner* mechanism. Without it, two duplicates within the same batch resolve in insertion order — unpredictable when paginating.
- **Composite PK with `_dlt_id` collisions:** rare but real — happens when two endpoints emit the same `(id, _table)` pair. Add `dedup_sort` or use `merge_key` instead.
- **Industry rule of thumb:** if the source has a stable, server-side ID → `primary_key`. If you're partitioning by (date, region) and reloading slices → `merge_key`. If you're stitching webhook + backfill streams → `primary_key` + `dedup_sort` on the modification timestamp.
