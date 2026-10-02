from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.session import get_db
from moduleiq.services.ai.orchestrator import AIOrchestrator
from moduleiq.services.ai.registry import build_provider
from moduleiq.services.ai.errors import AIProviderError, InvalidCredentialError
from moduleiq.services.knowledge import infer_knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.post("/infer/{version_id}")
def infer(version_id: str, provider_id: str, db: Session = Depends(get_db)):
    try:
        provider = build_provider(db, provider_id)
        result = infer_knowledge(db, version_id, AIOrchestrator(provider))
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except (AIProviderError, InvalidCredentialError) as exc:
        raise HTTPException(400, str(exc)) from exc
