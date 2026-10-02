# Phase 23 — Performance

- SQLite connections enable WAL, normal synchronous mode and a busy timeout for local Android/Termux concurrency.
- FastAPI adds gzip compression for larger JSON responses.
- Hot query paths receive composite indexes for analytics events, practice sessions, review queues and AI provider activation.
- The existing AI orchestrator keeps bounded TTL caching for repeated structured operations.
- Search remains bounded by explicit result/context limits and FTS5-first lookup with LIKE fallback.
