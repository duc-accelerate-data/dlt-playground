# Notes — Retries

- **Retry policy is API-shape-dependent.** Stripe, GitHub, Salesforce all return different rate-limit signals. Read the docs once, encode the spec in a `Client`, reuse across resources.
- **Retryable codes:** 408, 425, 429, 500, 502, 503, 504, plus connection errors. **Never** retry 400/401/403/404 — they will not heal.
- **`Retry-After`** is required for 429 — clients that ignore it get banned. Honor it as a *minimum*; add jitter on top.
- **Exponential backoff with jitter** prevents thundering-herd retries on a recovering upstream. `wait_exponential_jitter(initial=0.5, max=30)` is a sane default.
- **Max attempts: 5** is the dlt-hub default. More than that and you should be alerting, not retrying.
- **Pagination + retry interaction.** When you retry mid-pagination, make sure the resumed call uses the *same* cursor — don't restart from `since=initial_value`. The `Retry-After` is per-request, not per-resource.
- **Timeouts must be set.** `request_timeout=30` for most APIs. No timeout = pipeline hangs forever on a stuck connection.
- **Idempotency.** Retries assume the upstream is idempotent. POSTs and writes need an `Idempotency-Key`; reads usually are safe.
- **dlt's built-in `Client`** (`dlt.sources.helpers.requests.Client`) wraps `requests` with all of the above — verified-sources use it. This exercise uses `tenacity` directly to make the mechanics explicit; in real pipelines, prefer the bundled `Client`.
