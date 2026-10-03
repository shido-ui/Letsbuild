from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from moduleiq.core.security import require_local_provider, require_local_version, require_local_kb
from moduleiq.infrastructure.database.models import Question, QuestionOption, DifficultyAssessment, Classification
from moduleiq.infrastructure.database.session import get_db
from moduleiq.services.ai.errors import AIProviderError, InvalidCredentialError
from moduleiq.services.ai.orchestrator import AIOrchestrator
from moduleiq.services.ai.registry import build_provider
from moduleiq.services.questions import generate_questions

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("")
def list_questions(
    knowledge_base_id: str,
    q: str | None = Query(default=None, max_length=500),
    question_type: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    try:
        require_local_kb(db, knowledge_base_id)
        statement = select(Question).where(Question.knowledge_base_id == knowledge_base_id)
        count_statement = select(func.count()).select_from(Question).where(
            Question.knowledge_base_id == knowledge_base_id
        )
        if q:
            pattern = f"%{q.strip()}%"
            statement = statement.where(Question.text.ilike(pattern))
            count_statement = count_statement.where(Question.text.ilike(pattern))
        if question_type:
            statement = statement.where(Question.question_type == question_type)
            count_statement = count_statement.where(Question.question_type == question_type)
        rows = db.scalars(
            statement.order_by(Question.created_at.desc(), Question.id).offset(offset).limit(limit)
        ).all()
        total = db.scalar(count_statement) or 0
        payload = []
        for question in rows:
            difficulty = db.get(DifficultyAssessment, question.difficulty_id) if question.difficulty_id else None
            classification = db.get(Classification, question.classification_id) if question.classification_id else None
            options = db.scalars(
                select(QuestionOption).where(QuestionOption.question_id == question.id).order_by(QuestionOption.ordinal)
            ).all()
            payload.append({
                "id": question.id,
                "text": question.text,
                "question_type": question.question_type,
                "difficulty": difficulty.overall if difficulty else None,
                "classification": {
                    "subject": classification.subject,
                    "topic": classification.topic,
                    "subtopic": classification.subtopic,
                } if classification else None,
                "options": [{"id": o.id, "ordinal": o.ordinal, "text": o.option_text} for o in options],
                "metadata": question.metadata_json,
            })
        return {"items": payload, "total": total, "limit": limit, "offset": offset}
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/{question_id}")
def get_question(question_id: str, db: Session = Depends(get_db)):
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(404, "Question not found")
    # Ownership is resolved through the knowledge base.
    from moduleiq.core.security import require_local_question
    require_local_question(db, question_id)
    difficulty = db.get(DifficultyAssessment, question.difficulty_id) if question.difficulty_id else None
    classification = db.get(Classification, question.classification_id) if question.classification_id else None
    options = db.scalars(select(QuestionOption).where(QuestionOption.question_id == question.id).order_by(QuestionOption.ordinal)).all()
    return {
        "id": question.id,
        "text": question.text,
        "question_type": question.question_type,
        "difficulty": difficulty.overall if difficulty else None,
        "classification": classification.model_dump() if hasattr(classification, "model_dump") else (
            {"subject": classification.subject, "topic": classification.topic, "subtopic": classification.subtopic}
            if classification else None
        ),
        "options": [{"id": o.id, "ordinal": o.ordinal, "text": o.option_text} for o in options],
        "metadata": question.metadata_json,
    }


@router.post("/generate/{version_id}")
def generate(version_id: str, provider_id: str, db: Session = Depends(get_db)):
    try:
        require_local_version(db, version_id)
        require_local_provider(db, provider_id)
        return generate_questions(db, version_id, AIOrchestrator(build_provider(db, provider_id))).model_dump()
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except (AIProviderError, InvalidCredentialError) as exc:
        raise HTTPException(400, str(exc)) from exc
