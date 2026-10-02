from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.models import DocumentVersion, Material, Question, QuestionOption, QuestionSolution, Provenance, KnowledgeBase, Block
from moduleiq.services.ai.orchestrator import AIContext, AIOrchestrator, ContextItem
from moduleiq.services.ai.schemas import QuestionsOutput

def question_context(db: Session, version_id: str) -> AIContext:
    blocks = db.scalars(select(Block).join(Block.page).where(Block.page.has(document_version_id=version_id)).order_by(Block.page_id, Block.ordinal)).all()
    items = tuple(ContextItem(b.text or "", ({"source_kind":"block","source_id":b.id,"page_id":b.page_id},)) for b in blocks if (b.text or "").strip())
    return AIContext(items=items, max_chars=24000)

def generate_questions(db: Session, version_id: str, orchestrator: AIOrchestrator) -> QuestionsOutput:
    version = db.get(DocumentVersion, version_id)
    if version is None: raise ValueError("Document version not found")
    material = db.scalar(select(Material).join(DocumentVersion.document).where(DocumentVersion.id == version_id))
    if material is None: raise ValueError("Material not found")
    output = orchestrator.generate_questions(question_context(db, version_id)).output
    if not isinstance(output, QuestionsOutput): raise TypeError("Question schema mismatch")
    kb_id = material.knowledge_base_id
    for item in output.questions:
        text = item.text.strip()
        if not text or db.scalar(select(Question).where(Question.knowledge_base_id == kb_id, Question.text == text)):
            continue
        ref = item.source_references[0] if item.source_references else None
        block_id = getattr(ref, "block_id", None) or getattr(ref, "source_id", None)
        block = db.get(Block, block_id) if block_id else None
        provenance = Provenance(source_kind="ai_generated", source_document_id=version.document_id,
                                source_page_id=block.page_id if block else None, source_block_id=block.id if block else None,
                                locator="ai:question-generation", confidence=1.0)
        db.add(provenance); db.flush()
        q = Question(knowledge_base_id=kb_id, text=text, question_type=item.question_type, provenance_id=provenance.id)
        db.add(q); db.flush()
        for i, option in enumerate(item.options):
            db.add(QuestionOption(question_id=q.id, ordinal=i, option_text=option))
        if item.answer:
            db.add(QuestionSolution(question_id=q.id, solution_type="ai", body=item.answer))
    db.commit()
    return output
