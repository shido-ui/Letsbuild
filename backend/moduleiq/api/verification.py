from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.session import get_db
from moduleiq.core.security import require_local_provider, require_local_question
from moduleiq.services.ai.errors import AIProviderError, InvalidCredentialError
from moduleiq.services.ai.orchestrator import AIOrchestrator
from moduleiq.services.ai.registry import build_provider
from moduleiq.services.verification import assess_question

router = APIRouter(prefix="/verification", tags=["verification"])

@router.post("/questions/{question_id}")
def assess(question_id: str, provider_id: str, db: Session = Depends(get_db)):
    try:
        require_local_question(db, question_id)
        require_local_provider(db, provider_id)
        return assess_question(db, question_id, AIOrchestrator(build_provider(db, provider_id)))
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except (AIProviderError, InvalidCredentialError) as exc:
        raise HTTPException(400, str(exc)) from exc
