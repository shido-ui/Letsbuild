from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.session import get_db
from moduleiq.infrastructure.database.models import Question
from moduleiq.services.ai.errors import AIProviderError, InvalidCredentialError
from moduleiq.services.ai.orchestrator import AIOrchestrator
from moduleiq.services.ai.registry import build_provider
from moduleiq.services.solution_engine import generate_ai_solution

router = APIRouter(prefix="/solutions", tags=["solutions"])


@router.get("/question/{question_id}")
def get_solutions(question_id: str, db: Session = Depends(get_db)):
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(404, "Question not found")
    return {
        "question_id": question.id,
        "solutions": [
            {
                "id": s.id,
                "type": s.solution_type,
                "body": s.body,
                "confidence": s.confidence,
                "verification_id": s.verification_id,
                "metadata": s.metadata_json,
            }
            for s in question.solutions
        ],
    }


@router.post("/generate/{question_id}")
def generate_solution(question_id: str, provider_id: str, db: Session = Depends(get_db)):
    try:
        return generate_ai_solution(db, question_id, AIOrchestrator(build_provider(db, provider_id)))
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except (AIProviderError, InvalidCredentialError) as exc:
        raise HTTPException(400, str(exc)) from exc
