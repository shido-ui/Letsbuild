# Phase 24 — Failure / Recovery

Ingestion jobs now have an explicit lifecycle: queued, processing, retrying, complete, or failed.

- Transient extraction failures retry up to the configured Huey retry count.
- Terminal failures are persisted as failed rather than remaining indefinitely in retrying.
- MinerU engine-unavailable failures are persisted as terminal failures.
- A failed or retrying job can be reset to queued through the recovery API.
- Recovery resets stage progress and errors so the next run starts from a clean persisted state.
- The frontend can surface the persisted job status and invoke recovery without recreating the uploaded material.
