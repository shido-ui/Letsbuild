# ModuleIQ — Architecture Lock

## Locked deployment target

**Android-first Web/PWA**

Primary local path:

Android
→ Termux
→ Web/PWA frontend
→ FastAPI backend
→ SQLite/local storage
→ background workers
→ MinerU document engine
→ search/indexing
→ AI provider layer
→ cloud API or local model

## Layer ownership

### Presentation
Owns:
- Figma-derived design system
- routes
- responsive/mobile UX
- interactions
- loading/error/empty/success states

Must not:
- derive visual structure from database tables
- expose provider secrets
- contain document-processing logic

### API/application
Owns:
- authentication/session policy
- domain services
- API contracts
- authorization
- orchestration

### Domain
Owns:
- workspaces
- knowledge bases
- materials
- documents
- knowledge objects
- questions
- solutions
- learner model
- practice
- review
- analytics
- provider lifecycle

### Document engine
Owns:
- parsing
- OCR
- layout
- equation extraction
- table extraction
- figure/diagram extraction
- deterministic document structure

MinerU is the supplied foundation.

### AI provider layer
Owns:
- provider abstraction
- credentials
- prompt orchestration
- structured output
- classification
- enrichment
- solution generation
- verification
- vision analysis

### Worker layer
Owns:
- asynchronous execution
- retries
- job lifecycle
- long-running processing

Huey is the supplied foundation.

### Persistence
Owns:
- canonical ModuleIQ objects
- provenance
- confidence
- practice history
- analytics
- provider metadata
- backups

## Critical invariant

AI is never the database.

The canonical flow is:

Document
→ structured extraction
→ normalized knowledge objects
→ database
→ AI enrichment
→ verification
→ database
→ application

## Source-code reuse rule

Supplied code must be:

1. Used raw when it already matches the required responsibility.
2. Adapted when a small integration change is needed.
3. Wrapped when ModuleIQ needs a stable boundary.
4. Extended when ModuleIQ needs additional behavior.
5. Replaced only when an audit demonstrates incompatibility or unacceptable technical cost.

## UI rule

Figma is the visual source of truth.

Implementation order for UI:

Figma
→ design tokens
→ reusable components
→ screen composition
→ responsive/mobile adaptation
→ interaction wiring
→ API/data integration

Never:

database
→ backend
→ improvised UI

## Completion rule

No phase advances until its checklist is green.
