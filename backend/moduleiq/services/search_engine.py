from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.models import (
    Block,
    Chapter,
    Concept,
    Diagram,
    Document,
    DocumentVersion,
    Equation,
    Material,
    Page,
    Provenance,
    Question,
    QuestionSolution,
    Section,
    Subtopic,
    Table,
    Topic,
)

TOKEN_RE = re.compile(r"[\\w'-]+", re.UNICODE)


@dataclass(frozen=True)
class SearchEntry:
    kind: str
    object_id: str
    title: str
    content: str
    source_document_id: str | None = None
    source_page_id: str | None = None


SEARCHABLE_MODELS = (
    Document,
    Page,
    Block,
    Section,
    Chapter,
    Topic,
    Subtopic,
    Concept,
    Equation,
    Table,
    Diagram,
    Question,
    QuestionSolution,
)


def _json(value: Any) -> str:
    if value is None:
        return ""
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return str(value)


def _tokens(value: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(value or "") if len(t) > 1]


def _fingerprint(db: Session, kb_id: str) -> str:
    parts: list[str] = []
    for model in SEARCHABLE_MODELS:
        if model is QuestionSolution:
            count, latest = db.execute(
                select(func.count(QuestionSolution.id), func.max(QuestionSolution.updated_at))
                .join(Question, QuestionSolution.question_id == Question.id)
                .where(Question.knowledge_base_id == kb_id)
            ).one()
        elif model is Document:
            count, latest = db.execute(
                select(func.count(Document.id), func.max(Document.updated_at))
                .join(Material, Document.material_id == Material.id)
                .where(Material.knowledge_base_id == kb_id)
            ).one()
        elif model is Page:
            count, latest = db.execute(
                select(func.count(Page.id), func.max(Page.updated_at))
                .join(DocumentVersion, Page.document_version_id == DocumentVersion.id)
                .join(Document, DocumentVersion.document_id == Document.id)
                .join(Material, Document.material_id == Material.id)
                .where(Material.knowledge_base_id == kb_id)
            ).one()
        elif model is Block:
            count, latest = db.execute(
                select(func.count(Block.id), func.max(Block.updated_at))
                .join(Page, Block.page_id == Page.id)
                .join(DocumentVersion, Page.document_version_id == DocumentVersion.id)
                .join(Document, DocumentVersion.document_id == Document.id)
                .join(Material, Document.material_id == Material.id)
                .where(Material.knowledge_base_id == kb_id)
            ).one()
        elif model is Section:
            count, latest = db.execute(
                select(func.count(Section.id), func.max(Section.updated_at))
                .join(DocumentVersion, Section.document_version_id == DocumentVersion.id)
                .join(Document, DocumentVersion.document_id == Document.id)
                .join(Material, Document.material_id == Material.id)
                .where(Material.knowledge_base_id == kb_id)
            ).one()
        elif model is Chapter:
            count, latest = db.execute(
                select(func.count(Chapter.id), func.max(Chapter.updated_at))
                .join(Section, Chapter.section_id == Section.id)
                .join(DocumentVersion, Section.document_version_id == DocumentVersion.id)
                .join(Document, DocumentVersion.document_id == Document.id)
                .join(Material, Document.material_id == Material.id)
                .where(Material.knowledge_base_id == kb_id)
            ).one()
        elif model is Topic:
            count, latest = db.execute(
                select(func.count(Topic.id), func.max(Topic.updated_at))
                .join(Chapter, Topic.chapter_id == Chapter.id)
                .join(Section, Chapter.section_id == Section.id)
                .join(DocumentVersion, Section.document_version_id == DocumentVersion.id)
                .join(Document, DocumentVersion.document_id == Document.id)
                .join(Material, Document.material_id == Material.id)
                .where(Material.knowledge_base_id == kb_id)
            ).one()
        elif model is Subtopic:
            count, latest = db.execute(
                select(func.count(Subtopic.id), func.max(Subtopic.updated_at))
                .join(Topic, Subtopic.topic_id == Topic.id)
                .join(Chapter, Topic.chapter_id == Chapter.id)
                .join(Section, Chapter.section_id == Section.id)
                .join(DocumentVersion, Section.document_version_id == DocumentVersion.id)
                .join(Document, DocumentVersion.document_id == Document.id)
                .join(Material, Document.material_id == Material.id)
                .where(Material.knowledge_base_id == kb_id)
            ).one()
        elif model is Concept:
            count, latest = db.execute(
                select(func.count(Concept.id), func.max(Concept.updated_at))
                .join(Subtopic, Concept.subtopic_id == Subtopic.id)
                .join(Topic, Subtopic.topic_id == Topic.id)
                .join(Chapter, Topic.chapter_id == Chapter.id)
                .join(Section, Chapter.section_id == Section.id)
                .join(DocumentVersion, Section.document_version_id == DocumentVersion.id)
                .join(Document, DocumentVersion.document_id == Document.id)
                .join(Material, Document.material_id == Material.id)
                .where(Material.knowledge_base_id == kb_id)
            ).one()
        elif model in (Equation, Table, Diagram):
            cls = model
            count, latest = db.execute(
                select(func.count(cls.id), func.max(cls.updated_at))
                .join(Page, cls.page_id == Page.id)
                .join(DocumentVersion, Page.document_version_id == DocumentVersion.id)
                .join(Document, DocumentVersion.document_id == Document.id)
                .join(Material, Document.material_id == Material.id)
                .where(Material.knowledge_base_id == kb_id)
            ).one()
        else:
            count, latest = db.execute(
                select(func.count(Question.id), func.max(Question.updated_at))
                .where(Question.knowledge_base_id == kb_id)
            ).one()
        parts.append(f"{model.__tablename__}:{count}:{latest.isoformat() if latest else ''}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def _collect_entries(db: Session, kb_id: str) -> list[SearchEntry]:
    material_ids = set(db.scalars(select(Material.id).where(Material.knowledge_base_id == kb_id)).all())
    documents = db.scalars(select(Document).where(Document.material_id.in_(material_ids))).all()
    document_ids = {d.id for d in documents}
    versions = db.scalars(select(DocumentVersion).where(DocumentVersion.document_id.in_(document_ids))).all()
    version_to_doc = {v.id: v.document_id for v in versions}
    pages = db.scalars(select(Page).where(Page.document_version_id.in_(version_to_doc))).all()
    page_to_doc = {p.id: version_to_doc[p.document_version_id] for p in pages}
    page_ids = {p.id for p in pages}

    sections = db.scalars(select(Section).where(Section.document_version_id.in_(version_to_doc))).all()
    section_to_doc = {s.id: version_to_doc[s.document_version_id] for s in sections}
    section_ids = {s.id for s in sections}
    chapters = db.scalars(select(Chapter).where(Chapter.section_id.in_(section_ids))).all()
    chapter_to_doc = {c.id: section_to_doc[c.section_id] for c in chapters}
    chapter_ids = {c.id for c in chapters}
    topics = db.scalars(select(Topic).where(Topic.chapter_id.in_(chapter_ids))).all()
    topic_to_doc = {t.id: chapter_to_doc[t.chapter_id] for t in topics}
    topic_ids = {t.id for t in topics}
    subtopics = db.scalars(select(Subtopic).where(Subtopic.topic_id.in_(topic_ids))).all()
    subtopic_to_doc = {s.id: topic_to_doc[s.topic_id] for s in subtopics}
    subtopic_ids = {s.id for s in subtopics}
    concepts = db.scalars(select(Concept).where(Concept.subtopic_id.in_(subtopic_ids))).all()

    blocks = db.scalars(select(Block).where(Block.page_id.in_(page_ids))).all()
    equations = db.scalars(select(Equation).where(Equation.page_id.in_(page_ids))).all()
    tables = db.scalars(select(Table).where(Table.page_id.in_(page_ids))).all()
    diagrams = db.scalars(select(Diagram).where(Diagram.page_id.in_(page_ids))).all()
    questions = db.scalars(select(Question).where(Question.knowledge_base_id == kb_id)).all()
    question_ids = {q.id for q in questions}
    solutions = db.scalars(select(QuestionSolution).where(QuestionSolution.question_id.in_(question_ids))).all()

    entries: list[SearchEntry] = []
    for d in documents:
        entries.append(SearchEntry("document", d.id, d.title or "Untitled document", f"{d.title or ''} {_json(d.metadata_json)}", d.id))
    for p in pages:
        entries.append(SearchEntry("page", p.id, f"Page {p.page_number}", f"Page {p.page_number} {_json(p.metadata_json)}", page_to_doc[p.id], p.id))
    for b in blocks:
        entries.append(SearchEntry("block", b.id, f"Block {b.ordinal}", b.text or "", page_to_doc[b.page_id], b.page_id))
    for s in sections:
        entries.append(SearchEntry("section", s.id, s.title, f"{s.title} {_json(s.metadata_json)}", section_to_doc[s.id]))
    for c in chapters:
        entries.append(SearchEntry("chapter", c.id, c.title, f"{c.title} {_json(c.metadata_json)}", chapter_to_doc[c.id]))
    for t in topics:
        entries.append(SearchEntry("topic", t.id, t.name, f"{t.name} {_json(t.metadata_json)}", topic_to_doc[t.id]))
    for s in subtopics:
        entries.append(SearchEntry("subtopic", s.id, s.name, s.name, subtopic_to_doc[s.id]))
    concept_to_doc = {c.id: subtopic_to_doc.get(c.subtopic_id) for c in concepts}
    for c in concepts:
        entries.append(SearchEntry("concept", c.id, c.name, f"{c.name} {c.definition or ''}", concept_to_doc.get(c.id)))
    for e in equations:
        entries.append(SearchEntry("equation", e.id, "Equation", f"{e.latex} {e.source_text or ''}", page_to_doc.get(e.page_id), e.page_id))
    for t in tables:
        entries.append(SearchEntry("table", t.id, t.caption or "Table", f"{t.caption or ''} {_json(t.data_json)}", page_to_doc.get(t.page_id), t.page_id))
    for d in diagrams:
        entries.append(SearchEntry("diagram", d.id, d.caption or "Diagram", d.caption or "Diagram", page_to_doc.get(d.page_id), d.page_id))

    provenance_ids = {q.provenance_id for q in questions if q.provenance_id}
    provenance = {
        p.id: p for p in db.scalars(select(Provenance).where(Provenance.id.in_(provenance_ids))).all()
    }
    question_to_source = {
        q.id: (provenance[q.provenance_id].source_document_id, provenance[q.provenance_id].source_page_id)
        for q in questions if q.provenance_id in provenance
    }
    for q in questions:
        doc_id, page_id = question_to_source.get(q.id, (None, None))
        entries.append(SearchEntry("question", q.id, "Question", f"{q.text} {q.question_type}", doc_id, page_id))
    for s in solutions:
        doc_id, page_id = question_to_source.get(s.question_id, (None, None))
        entries.append(SearchEntry("solution", s.id, f"{s.solution_type.title()} solution", f"{s.body} {s.solution_type}", doc_id, page_id))
    return entries


def ensure_index(db: Session, kb_id: str) -> None:
    fingerprint = _fingerprint(db, kb_id)
    state = db.execute(
        text("SELECT source_fingerprint FROM search_index_state WHERE knowledge_base_id = :kb"),
        {"kb": kb_id},
    ).scalar_one_or_none()
    if state == fingerprint:
        return

    entries = _collect_entries(db, kb_id)
    db.execute(text("DELETE FROM search_entries WHERE knowledge_base_id = :kb"), {"kb": kb_id})
    try:
        db.execute(text("DELETE FROM search_entries_fts WHERE knowledge_base_id = :kb"), {"kb": kb_id})
    except Exception:
        pass

    for entry in entries:
        entry_id = f"{entry.kind}:{entry.object_id}"
        payload = {
            "id": entry_id,
            "kb": kb_id,
            "kind": entry.kind,
            "object_id": entry.object_id,
            "title": entry.title,
            "content": entry.content,
            "doc": entry.source_document_id,
            "page": entry.source_page_id,
        }
        db.execute(
            text(
                "INSERT INTO search_entries "
                "(id, knowledge_base_id, kind, object_id, title, content, source_document_id, source_page_id) "
                "VALUES (:id, :kb, :kind, :object_id, :title, :content, :doc, :page)"
            ),
            payload,
        )
        try:
            db.execute(
                text(
                    "INSERT INTO search_entries_fts "
                    "(entry_id, knowledge_base_id, kind, object_id, title, content) "
                    "VALUES (:id, :kb, :kind, :object_id, :title, :content)"
                ),
                payload,
            )
        except Exception:
            pass

    db.execute(
        text(
            "INSERT INTO search_index_state (knowledge_base_id, source_fingerprint, indexed_at) "
            "VALUES (:kb, :fingerprint, :indexed_at) "
            "ON CONFLICT(knowledge_base_id) DO UPDATE SET "
            "source_fingerprint = excluded.source_fingerprint, indexed_at = excluded.indexed_at"
        ),
        {"kb": kb_id, "fingerprint": fingerprint, "indexed_at": datetime.utcnow().isoformat()},
    )
    db.commit()


def _fts_query(query: str) -> str:
    tokens = _tokens(query)
    if not tokens:
        return ""
    return " ".join(f'"{token.replace(chr(34), chr(34) + chr(34))}"*' for token in tokens[:16])


def _semantic_expansions(db: Session, kb_id: str, query: str) -> list[str]:
    qtokens = set(_tokens(query))
    if not qtokens:
        return []
    rows = db.execute(
        select(Concept.name, Concept.definition)
        .join(Subtopic, Concept.subtopic_id == Subtopic.id)
        .join(Topic, Subtopic.topic_id == Topic.id)
        .join(Chapter, Topic.chapter_id == Chapter.id)
        .join(Section, Chapter.section_id == Section.id)
        .join(DocumentVersion, Section.document_version_id == DocumentVersion.id)
        .join(Document, DocumentVersion.document_id == Document.id)
        .join(Material, Document.material_id == Material.id)
        .where(Material.knowledge_base_id == kb_id)
        .limit(2000)
    ).all()
    matches: list[tuple[int, str]] = []
    for name, definition in rows:
        overlap = len(qtokens & set(_tokens(f"{name} {definition or ''}")))
        if overlap:
            matches.append((overlap, name))
    matches.sort(reverse=True)
    return [name for _, name in matches[:5]]


def search(
    db: Session,
    kb_id: str,
    query: str,
    *,
    kind: str | None = None,
    document_id: str | None = None,
    limit: int = 20,
) -> dict:
    from moduleiq.infrastructure.database.models import KnowledgeBase

    if db.get(KnowledgeBase, kb_id) is None:
        raise ValueError("Knowledge base not found")
    clean_query = query.strip()
    if not clean_query:
        return {"query": query, "results": [], "related_concepts": []}

    ensure_index(db, kb_id)
    fts = _fts_query(clean_query)
    expansions = _semantic_expansions(db, kb_id, clean_query)
    params: dict[str, Any] = {"kb": kb_id, "limit": max(1, min(limit, 100))}
    kind_filter = " AND e.kind = :kind" if kind else ""
    doc_filter = " AND e.source_document_id = :document_id" if document_id else ""
    if kind:
        params["kind"] = kind
    if document_id:
        params["document_id"] = document_id

    rows: list[tuple[Any, ...]] = []
    if fts:
        try:
            params["fts"] = fts
            rows = db.execute(
                text(
                    "SELECT e.kind, e.object_id, e.title, e.content, e.source_document_id, e.source_page_id, "
                    "bm25(search_entries_fts) AS rank, "
                    "snippet(search_entries_fts, 5, '[', ']', '…', 22) AS snippet "
                    "FROM search_entries_fts "
                    "JOIN search_entries e ON e.id = search_entries_fts.entry_id "
                    "WHERE search_entries_fts MATCH :fts AND e.knowledge_base_id = :kb"
                    + kind_filter + doc_filter +
                    " ORDER BY rank ASC LIMIT :limit"
                ),
                params,
            ).all()
        except Exception:
            rows = []

    if not rows:
        like = f"%{clean_query}%"
        params["like"] = like
        rows = db.execute(
            text(
                "SELECT kind, object_id, title, content, source_document_id, source_page_id, 0.0 AS rank, "
                "substr(content, 1, 180) AS snippet FROM search_entries "
                "WHERE knowledge_base_id = :kb AND (title LIKE :like OR content LIKE :like)"
                + kind_filter.replace("e.", "") + doc_filter.replace("e.", "") +
                " ORDER BY CASE WHEN lower(title) = lower(:exact) THEN 0 ELSE 1 END, title LIMIT :limit"
            ),
            {**params, "exact": clean_query},
        ).all()

    if expansions and len(rows) < params["limit"]:
        seen = {(r[0], r[1]) for r in rows}
        for expansion in expansions:
            exp_fts = _fts_query(expansion)
            if not exp_fts:
                continue
            try:
                more = db.execute(
                    text(
                        "SELECT e.kind, e.object_id, e.title, e.content, e.source_document_id, e.source_page_id, "
                        "bm25(search_entries_fts) AS rank, "
                        "snippet(search_entries_fts, 5, '[', ']', '…', 22) AS snippet "
                        "FROM search_entries_fts JOIN search_entries e ON e.id = search_entries_fts.entry_id "
                        "WHERE search_entries_fts MATCH :fts AND e.knowledge_base_id = :kb"
                        + kind_filter + doc_filter + " ORDER BY rank ASC LIMIT :limit"
                    ),
                    {**params, "fts": exp_fts, "limit": params["limit"]},
                ).all()
            except Exception:
                more = []
            rows.extend(r for r in more if (r[0], r[1]) not in seen)
            seen.update((r[0], r[1]) for r in more)
            if len(rows) >= params["limit"]:
                break

    tokens = set(_tokens(clean_query))
    exact = clean_query.lower()
    results = []
    for r in rows[: params["limit"]]:
        title, content = (r[2] or "").lower(), (r[3] or "").lower()
        score = 1.0 / (1.0 + max(0.0, float(r[6] or 0.0)))
        if exact in title:
            score += 2.0
        elif exact in content:
            score += 1.0
        if tokens and tokens.issubset(set(_tokens(title + " " + content))):
            score += 0.5
        results.append(
            {
                "kind": r[0],
                "id": r[1],
                "title": r[2],
                "snippet": r[7] or (r[3] or "")[:180],
                "score": round(score, 6),
                "source": {"document_id": r[4], "page_id": r[5]},
            }
        )
    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "query": query,
        "results": results[: params["limit"]],
        "related_concepts": [{"name": name} for name in expansions],
    }
