# Phase 25 — End-to-End

The backend E2E journey exercises real FastAPI routes against a temporary SQLite database:

1. local workspace and knowledge base discovery
2. persisted question/options
3. practice session creation
4. answer submission and completion
5. persisted results
6. review item creation and resolution
7. analytics summary
8. portability export and validation

The test uses the same application routers and dependency boundary as the running service; it does not replace the API with direct service calls.
