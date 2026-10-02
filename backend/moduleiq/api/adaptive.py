from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.session import get_db
from moduleiq.services.adaptive import get_or_create_profile, mastery, recommendations

router = APIRouter(prefix="/adaptive", tags=["adaptive"])


class ProfileRequest(BaseModel):
    user_id: str


@router.post("/profiles")
def profile(request: ProfileRequest, db: Session = Depends(get_db)):
    try:
        p = get_or_create_profile(db, request.user_id)
        db.commit()
        return {"id": p.id, "user_id": p.user_id}
    except Exception as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc


@router.get("/profiles/{profile_id}/mastery")
def profile_mastery(profile_id: str, knowledge_base_id: str, db: Session = Depends(get_db)):
    return mastery(db, profile_id, knowledge_base_id)


@router.get("/profiles/{profile_id}/recommendations")
def profile_recommendations(profile_id: str, knowledge_base_id: str, limit: int = 10, db: Session = Depends(get_db)):
    return recommendations(db, profile_id, knowledge_base_id, limit)
