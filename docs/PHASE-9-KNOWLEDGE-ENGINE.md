# Phase 9 — Knowledge Engine

Status: GREEN

Implemented domain-agnostic knowledge hierarchy inference above canonical document objects.

- AI output contract for subject, section, chapter, topics, subtopics, concepts, prerequisites, related concepts, confidence, and source references.
- Context is assembled from normalized document blocks rather than raw PDF text.
- Existing canonical sections are reused when possible; chapters, topics, subtopics, concepts, and prerequisite edges are persisted idempotently.
- AI/provider metadata and confidence are retained on the document version and topic metadata.
- AI enriches canonical data; it does not replace the database.
- The hierarchy is domain-agnostic.

Phase gate: a material collection can become a navigable knowledge hierarchy rather than remaining only a folder of PDFs.
