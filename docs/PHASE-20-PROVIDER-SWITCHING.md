# Phase 20 — Provider Switching / AI Disconnect

## Contract
AI providers are optional services around the canonical knowledge database.

- At most one provider per user is active at a time.
- Activating a connected provider disables the user's other providers.
- A provider cannot be activated after its credential has been disconnected.
- Disconnecting removes the stored credential and disables the provider, but preserves provider metadata.
- Deleting a provider remains destructive to the provider record only; canonical knowledge and historical AI solution rows remain.
- AI solution provenance is preserved through the existing nullable AISolution.provider_id foreign key.

## API
- GET /api/ai/providers — list provider configurations and credential fingerprints.
- GET /api/ai/providers/active — return the active provider or null.
- POST /api/ai/providers/{provider_id}/activate — make a connected provider active.
- POST /api/ai/providers/{provider_id}/disconnect — remove its credential and disable it.
- DELETE /api/ai/providers/{provider_id} — delete the provider configuration.

The provider registry continues to resolve only enabled providers, so disconnecting or switching providers immediately affects future AI work without mutating canonical knowledge.
