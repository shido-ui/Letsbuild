# Phase 14 — Search Engine

ModuleIQ search is built around the canonical structured knowledge database rather than raw PDF grep.

## Indexed objects

Documents, pages, blocks, sections, chapters, topics, subtopics, concepts, questions, solutions, equations, tables, and diagrams are indexed.

## Retrieval

- SQLite FTS5 is used when available.
- A safe tokenized query supports exact/prefix retrieval.
- Relevance is ranked with FTS BM25 plus exact-title/content boosts.
- A structured semantic-expansion pass uses concept names/definitions already present in the knowledge graph.
- Non-FTS databases fall back to structured SQL LIKE retrieval.

## Filters

- 'knowledge_base_id' is required.
- 'kind' filters object type.
- 'document_id' filters source document.

## Provenance

Every result includes canonical object kind/id and source document/page references where available.

## API

GET /api/search?knowledge_base_id=<id>&q=<query>&kind=<kind>&document_id=<id>&limit=<n>

The frontend search route reuses the existing Figma-derived Search screen and wires it to this endpoint without introducing a new visual language.
