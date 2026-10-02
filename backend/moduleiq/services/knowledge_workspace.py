from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.models import (
    Block, Chapter, Concept, Diagram, Document, DocumentVersion, Equation,
    KnowledgeBase, Material, Page, Provenance, Question, QuestionSolution,
    Section, Subtopic, Table, Topic, Verification,
)


def _counts(db: Session, kb_id: str) -> dict:
    material_ids = select(Material.id).where(Material.knowledge_base_id == kb_id)
    document_ids = select(Document.id).where(Document.material_id.in_(material_ids))
    version_ids = select(DocumentVersion.id).where(DocumentVersion.document_id.in_(document_ids))
    page_ids = select(Page.id).where(Page.document_version_id.in_(version_ids))
    return {
        "materials": db.scalar(select(func.count()).select_from(Material).where(Material.knowledge_base_id == kb_id)) or 0,
        "documents": db.scalar(select(func.count()).select_from(Document).where(Document.material_id.in_(material_ids))) or 0,
        "pages": db.scalar(select(func.count()).select_from(Page).where(Page.document_version_id.in_(version_ids))) or 0,
        "blocks": db.scalar(select(func.count()).select_from(Block).where(Block.page_id.in_(page_ids))) or 0,
        "chapters": db.scalar(select(func.count()).select_from(Chapter).where(Chapter.section_id.in_(select(Section.id).where(Section.document_version_id.in_(version_ids))))) or 0,
        "topics": db.scalar(select(func.count()).select_from(Topic).where(Topic.chapter_id.in_(select(Chapter.id).where(Chapter.section_id.in_(select(Section.id).where(Section.document_version_id.in_(version_ids))))))) or 0,
        "concepts": db.scalar(select(func.count()).select_from(Concept).where(Concept.subtopic_id.in_(select(Subtopic.id).where(Subtopic.topic_id.in_(select(Topic.id).where(Topic.chapter_id.in_(select(Chapter.id).where(Chapter.section_id.in_(select(Section.id).where(Section.document_version_id.in_(version_ids))))))))))) or 0,
        "equations": db.scalar(select(func.count()).select_from(Equation).where(Equation.page_id.in_(page_ids))) or 0,
        "tables": db.scalar(select(func.count()).select_from(Table).where(Table.page_id.in_(page_ids))) or 0,
        "diagrams": db.scalar(select(func.count()).select_from(Diagram).where(Diagram.page_id.in_(page_ids))) or 0,
        "questions": db.scalar(select(func.count()).select_from(Question).where(Question.knowledge_base_id == kb_id)) or 0,
        "solutions": db.scalar(select(func.count()).select_from(QuestionSolution).join(Question).where(Question.knowledge_base_id == kb_id)) or 0,
        "verified_solutions": db.scalar(select(func.count()).select_from(QuestionSolution).join(Question).join(Verification, QuestionSolution.verification_id == Verification.id).where(Question.knowledge_base_id == kb_id, Verification.status == "verified")) or 0,
    }


def overview(db: Session, kb_id: str) -> dict:
    kb = db.get(KnowledgeBase, kb_id)
    if kb is None:
        raise ValueError("Knowledge base not found")
    materials = db.scalars(
        select(Material).where(Material.knowledge_base_id == kb_id).order_by(Material.created_at.desc())
    ).all()
    return {
        "id": kb.id,
        "name": kb.name,
        "description": kb.description,
        "counts": _counts(db, kb_id),
        "materials": [
            {
                "id": m.id, "name": m.name, "media_type": m.media_type,
                "size_bytes": m.size_bytes, "sha256": m.sha256,
                "metadata": m.metadata_json,
                "documents": [{"id": d.id, "title": d.title, "current_version_id": d.current_version_id, "metadata": d.metadata_json} for d in m.documents],
            } for m in materials
        ],
    }


def hierarchy(db: Session, kb_id: str) -> dict:
    kb = db.get(KnowledgeBase, kb_id)
    if kb is None:
        raise ValueError("Knowledge base not found")
    version_ids = select(DocumentVersion.id).where(
        DocumentVersion.document_id.in_(
            select(Document.id).where(Document.material_id.in_(select(Material.id).where(Material.knowledge_base_id == kb_id)))
        )
    )
    sections = db.scalars(select(Section).where(Section.document_version_id.in_(version_ids)).order_by(Section.title)).all()
    section_out = []
    for section in sections:
        chapters = db.scalars(select(Chapter).where(Chapter.section_id == section.id).order_by(Chapter.ordinal, Chapter.title)).all()
        chapter_out = []
        for chapter in chapters:
            topics = db.scalars(select(Topic).where(Topic.chapter_id == chapter.id).order_by(Topic.name)).all()
            topic_out = []
            for topic in topics:
                subs = db.scalars(select(Subtopic).where(Subtopic.topic_id == topic.id).order_by(Subtopic.name)).all()
                topic_out.append({
                    "id": topic.id, "name": topic.name, "metadata": topic.metadata_json,
                    "subtopics": [{
                        "id": sub.id, "name": sub.name,
                        "concepts": [{"id": c.id, "name": c.name, "definition": c.definition} for c in
                                     db.scalars(select(Concept).where(Concept.subtopic_id == sub.id).order_by(Concept.name)).all()]
                    } for sub in subs]
                })
            chapter_out.append({"id": chapter.id, "title": chapter.title, "topics": topic_out})
        section_out.append({"id": section.id, "title": section.title, "level": section.level, "chapters": chapter_out})
    return {"knowledge_base_id": kb.id, "sections": section_out}


def source_object(db: Session, kind: str, object_id: str) -> dict:
    loaders = {
        "document": Document, "version": DocumentVersion, "page": Page,
        "block": Block, "equation": Equation, "table": Table, "diagram": Diagram,
        "material": Material,
    }
    model = loaders.get(kind)
    if model is None:
        raise ValueError("Unsupported source object type")
    obj = db.get(model, object_id)
    if obj is None:
        raise ValueError("Source object not found")
    result = {"type": kind, "id": obj.id}
    for field in ("title", "name", "page_number", "text", "latex", "caption", "source_text", "media_type", "storage_uri"):
        if hasattr(obj, field):
            result[field] = getattr(obj, field)
    if hasattr(obj, "data_json"):
        result["data"] = obj.data_json
    if hasattr(obj, "metadata_json"):
        result["metadata"] = obj.metadata_json
    if isinstance(obj, Block):
        result["page_id"] = obj.page_id
        result["bbox"] = obj.bbox_json
    elif isinstance(obj, Page):
        result["document_version_id"] = obj.document_version_id
    elif isinstance(obj, DocumentVersion):
        result["document_id"] = obj.document_id
    elif isinstance(obj, Document):
        result["material_id"] = obj.material_id
    elif isinstance(obj, Material):
        result["knowledge_base_id"] = obj.knowledge_base_id
    return result


def related_topics(db: Session, kb_id: str) -> list[dict]:
    rows = db.execute(
        select(Topic.id, Topic.name, Topic.metadata_json, DocumentVersion.id.label("version_id"), Document.id.label("document_id"), Material.id.label("material_id"), Material.name.label("material_name"))
        .join(Chapter, Topic.chapter_id == Chapter.id)
        .join(Section, Chapter.section_id == Section.id)
        .join(DocumentVersion, Section.document_version_id == DocumentVersion.id)
        .join(Document, DocumentVersion.document_id == Document.id)
        .join(Material, Document.material_id == Material.id)
        .where(Material.knowledge_base_id == kb_id)
        .order_by(Topic.name, Material.name)
    ).all()
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row.name.lower().strip(), []).append({
            "topic_id": row.id, "name": row.name, "document_id": row.document_id,
            "material_id": row.material_id, "material_name": row.material_name,
        })
    return [
        {"name": entries[0]["name"], "documents": entries}
        for entries in grouped.values() if len({e["document_id"] for e in entries}) > 1
    ]
