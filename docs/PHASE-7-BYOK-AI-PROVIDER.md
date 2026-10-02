# Phase 7 — BYOK / AI Provider Engine

## Status
**GREEN**

The master plan requires persistent, provider-independent AI credentials, Gemini, OpenAI-compatible and local-model boundaries, provider selection/testing, credential validation, encrypted storage, secret masking, replacement/deletion, restart persistence, and provider switching without touching knowledge data. fileciteturn161file0

## Delivered
- Stable `AIProvider` interface for classify/extract/solve/verify/summarize/generateQuestions/analyzeImage.
- Gemini provider boundary.
- OpenAI-compatible provider.
- Local-model provider boundary for OpenAI-compatible local servers.
- Provider registry that reconstructs a provider from persisted configuration.
- Provider connection-test API.
- Persistent provider records.
- Encrypted credential ciphertext using an application encryption secret.
- SHA-256 credential fingerprint for identification without exposing the secret.
- Provider deletion that cascades its credential without deleting documents, knowledge, questions, analytics, or practice records.
- API never returns the raw saved credential.
- Provider endpoint/model configuration is persisted independently of knowledge data.
- Explicit provider errors for invalid credentials, timeouts, unavailable providers, and malformed provider responses.
- Environment configuration documented in `.env.example`.

## API boundary

```
POST   /api/ai/providers
GET    /api/ai/providers
POST   /api/ai/providers/{id}/test
DELETE /api/ai/providers/{id}
```

Saved credentials are only decrypted inside the provider construction path. The provider list exposes metadata and a fingerprint, never the secret.

## Separation invariant

```
Documents / Knowledge / Questions / Analytics / Practice
                         │
                         │ independent
                         ▼
                 AI provider layer
                         │
               encrypted credentials
```

Deleting or replacing a provider does not delete canonical ModuleIQ knowledge.

## Validation
- [x] Provider interface
- [x] Gemini boundary
- [x] OpenAI-compatible boundary
- [x] Local-model boundary
- [x] Credential encryption round trip
- [x] Credential fingerprinting
- [x] Connection-test path
- [x] Invalid credential/error boundary
- [x] Provider deletion isolation
- [x] Restart-persistent database storage
- [x] No raw-key response path
- [x] Existing CI regression suite

## Security boundary note
The master plan places comprehensive authentication, authorization, user isolation, secure deletion, request limits, and hardened secret handling in Phase 21. Phase 7 establishes the provider/credential architecture without pretending that the later security phase is already complete. fileciteturn161file2

## Phase gate
**GREEN — provider credentials and provider selection are persistent and replaceable without making the canonical knowledge database dependent on AI availability.**
