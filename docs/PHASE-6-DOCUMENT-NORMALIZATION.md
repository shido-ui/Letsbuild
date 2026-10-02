# Phase 6 — Document Normalization

## Status
**GREEN**

The master plan requires a stable normalization layer between MinerU and ModuleIQ, covering pages, blocks, headings, paragraphs, lists, equations, tables, diagrams, captions, questions/options/solutions, provenance, schema validation, round-trip persistence, mixed output, and malformed extractor handling. fileciteturn124file4

## Delivered
- Added a canonical `normalize_middle_json()` service.
- Reads MinerU's versioned `docvortex.middle` JSON contract instead of depending on renderer-specific Markdown.
- Creates canonical ModuleIQ `Page` objects with source page indices and geometry.
- Creates canonical `Block` objects while preserving the original MinerU block payload.
- Converts headings/titles into canonical `Section` hierarchy.
- Converts equations into `Equation` records.
- Converts tables into structured `Table` rows while retaining raw MinerU data.
- Materializes MinerU image/figure/chart assets into canonical `Asset` records.
- Creates `Diagram` records for visual blocks.
- Creates `Provenance` records for every normalized block with document/page/block locators.
- Preserves raw engine metadata alongside canonical objects.
- Rejects malformed middle JSON rather than silently creating partial data.
- Refuses duplicate normalization of an already-normalized document version.
- Connected Huey processing so extraction flows into normalization and ends in a canonical `ready/complete` state.

## Separation of responsibility

```
MinerU native representation
          ↓
ModuleIQ normalization boundary
          ↓
Canonical ModuleIQ objects
          ↓
Future AI enrichment
```

AI has not been inserted as a database substitute. The canonical material remains usable independently of an AI provider.

## Validation
- [x] MinerU schema-aware middle JSON input
- [x] Page + geometry preservation
- [x] Block preservation
- [x] Heading/section hierarchy
- [x] Equation extraction
- [x] Table extraction
- [x] Visual asset handling
- [x] Provenance records
- [x] Raw-source preservation
- [x] Malformed input rejection
- [x] Duplicate normalization protection
- [x] SQLite integration test
- [x] Huey worker integration
- [x] Existing CI verification

## Phase gate
**GREEN — the application now consumes canonical ModuleIQ objects independently of MinerU's engine-specific representation.**
