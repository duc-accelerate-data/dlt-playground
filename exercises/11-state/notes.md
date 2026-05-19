# Notes — State

- **State scopes:** `dlt.current.pipeline_state()` (whole pipeline) and `dlt.current.resource_state()` (per-resource — most common). dlt-hub recommends resource_state for cursors / ETags / pagination tokens.
- **State persists in the destination.** Wiping the warehouse loses state. Use `dev_mode=True` only when you want that.
- **`refresh="drop_resources"`** clears the cursor for the named resources — useful for "forget what you know and reload."
- **Don't stash secrets in state.** It's written to the destination in plaintext.
- **Common use cases:** ETag / If-Modified-Since headers, pagination cursors that aren't a simple cursor field, dedup windows ("the last 1000 ids we saw"), high-watermarks for non-time-series sources.
