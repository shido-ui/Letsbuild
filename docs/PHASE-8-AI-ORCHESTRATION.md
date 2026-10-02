# Phase 8 — AI Orchestration Engine

Status: GREEN

The Phase 8 layer implements the Master Phase-Wise Plan requirements: prompt orchestration, structured output schemas, source-grounded context assembly, validation/retries, malformed-response recovery, bounded caching, context limits, and provider-independent operations.

The orchestrator validates model output into ModuleIQ Pydantic objects for classification, extraction, solutions, verification, summaries, and generated questions. Source references are carried in the returned object. Context is explicitly bounded before invocation, and deterministic requests are cached in a bounded in-memory TTL cache.

Malformed JSON is repaired with a schema-specific retry prompt. Provider timeouts and provider errors are retried within the configured attempt budget and then surfaced to the caller. Provider-specific transport remains behind the Phase 7 AIProvider interface.

Canonical persistence is deliberately outside the orchestrator: validated AI output can enrich ModuleIQ records, but model text is not treated as the database or source of truth.

Validation covers schema validation, malformed JSON retry, timeout retry/propagation, cache behavior, long-context bounding, and source-reference preservation.
