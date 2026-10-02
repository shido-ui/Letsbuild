from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.models import Block, Chapter, Concept, DocumentVersion, Prerequisite, Section, Subtopic, Topic
from moduleiq.services.ai.orchestrator import AIContext, AIOrchestrator, ContextItem
from moduleiq.services.ai.schemas import KnowledgeOutput

def build_knowledge_context(db: Session, version_id: str, max_blocks: int = 120) -> AIContext:
    blocks = db.scalars(select(Block).join(Block.page).where(Block.page.has(document_version_id=version_id)).order_by(Block.page_id, Block.ordinal).limit(max_blocks)).all()
    items = tuple(ContextItem(b.text or "", ({"source_kind":"block","source_id":b.id,"page_id":b.page_id},)) for b in blocks if (b.text or "").strip())
    return AIContext(items=items, max_chars=24000)

def _section(db, version, title):
    row = db.scalar(select(Section).where(Section.document_version_id == version.id, Section.title == title))
    if row: return row
    row = Section(document_version_id=version.id, title=title, level=1)
    db.add(row); db.flush(); return row

def infer_knowledge(db: Session, version_id: str, orchestrator: AIOrchestrator) -> KnowledgeOutput:
    version = db.get(DocumentVersion, version_id)
    if version is None: raise ValueError("Document version not found")
    result = orchestrator.infer_knowledge(build_knowledge_context(db, version_id))
    output = result.output
    if not isinstance(output, KnowledgeOutput): raise TypeError("Knowledge schema mismatch")
    title = output.chapter or output.section or "General"
    section = _section(db, version, output.section or title)
    chapter = db.scalar(select(Chapter).where(Chapter.section_id == section.id, Chapter.title == title))
    if chapter is None:
        chapter = Chapter(section_id=section.id, title=title, ordinal=1); db.add(chapter); db.flush()
    concepts = {}
    for topic_data in output.topics:
        topic = db.scalar(select(Topic).where(Topic.chapter_id == chapter.id, Topic.name == topic_data.name))
        if topic is None:
            topic = Topic(chapter_id=chapter.id, name=topic_data.name); db.add(topic); db.flush()
        topic.metadata_json = {**(topic.metadata_json or {}), "subject": output.subject, "source_document_version_id": version.id}
        for sub_data in topic_data.subtopics:
            sub = db.scalar(select(Subtopic).where(Subtopic.topic_id == topic.id, Subtopic.name == sub_data.name))
            if sub is None:
                sub = Subtopic(topic_id=topic.id, name=sub_data.name); db.add(sub); db.flush()
            for name in sub_data.concepts:
                concept = db.scalar(select(Concept).where(Concept.subtopic_id == sub.id, Concept.name == name))
                if concept is None:
                    concept = Concept(subtopic_id=sub.id, name=name); db.add(concept); db.flush()
                concepts[name] = concept
    for rel in output.prerequisites:
        a, b = concepts.get(rel.prerequisite), concepts.get(rel.dependent)
        if a and b and a.id != b.id and db.scalar(select(Prerequisite).where(Prerequisite.prerequisite_concept_id == a.id, Prerequisite.dependent_concept_id == b.id)) is None:
            db.add(Prerequisite(prerequisite_concept_id=a.id, dependent_concept_id=b.id, strength=rel.strength))
    version.metadata_json = {**(version.metadata_json or {}), "knowledge_engine": {"subject": output.subject, "confidence": output.confidence, "attempts": result.attempts, "provider": result.provider, "model": result.model}}
    db.commit()
    return output
