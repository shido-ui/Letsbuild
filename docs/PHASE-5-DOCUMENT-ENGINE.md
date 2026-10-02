# Phase 5 — Production Document Engine Integration

## Status
**GREEN**

Phase 5 follows the master phase plan: MinerU is the production document-intelligence engine, while ModuleIQ owns job lifecycle and later canonical normalization. The phase explicitly does not replace MinerU with a simplistic parser. fileciteturn124file4

## Delivered
- Isolated `MinerUAdapter` boundary around the supplied MinerU implementation.
- Pinned optional document-engine dependency: MinerU 4.0.10.
- Configurable MinerU tier, OCR mode, and image analysis.
- Native MinerU `middle_json.json` preservation.
- Native Markdown and structured-content preservation.
- Native MinerU asset materialization.
- Extraction output stored under the document-version boundary.
- Huey worker now owns long-running MinerU execution.
- Retry policy remains active for extraction failures.
- Processing stages move from validation → document analysis/extraction and expose failures.
- Processing metadata records engine/version/output locations.
- Frontend continues to observe the same processing-job API.

## Architecture boundary
**ModuleIQ:** validation, ownership, job lifecycle, persistence, canonical schema, later normalization.

**MinerU:** PDF/document parsing, OCR, layout understanding, hierarchy signals, equations, tables, images/figures, structured middle representation, native asset handling.

Phase 6 will convert MinerU's engine-specific middle representation into canonical ModuleIQ objects. This keeps the application independent of the extraction implementation while preserving full native output.

## Validation
- [x] Adapter import boundary
- [x] Explicit missing-engine failure
- [x] Native output preservation contract
- [x] Asset materialization contract
- [x] Pinned MinerU dependency declaration
- [x] Huey worker integration
- [x] Retry boundary
- [x] Backend test suite
- [x] Frontend CI remains green

## Important runtime note
The default CI suite does **not** install the heavyweight `document-engine` extra. The production path is intentionally optional so the lightweight API/test environment does not download model/runtime dependencies. A deployment that processes documents installs the `document-engine` extra.

## Phase gate
**GREEN — real document processing now has a production MinerU execution path behind a stable ModuleIQ boundary, with native extraction artifacts and worker/retry lifecycle preserved.**
