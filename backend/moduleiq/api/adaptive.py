from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from moduleiq.core.security import local_user, require_local_kb, require_local_profile
from moduleiq.infrastructure.database.session import get_db
from moduleiq.services.adaptive import get_or_create_profile, mastery, recommendations

router = APIRouter(prefix="/adaptive", tags=["adaptive"])


class ProfileRequest(BaseModel):
    user_id: str | None = None


def _error(exc: ValueError) -> HTTPException:
    return HTTPException(404 if "not found" in str(exc).lower() else 400, str(exc))


@router.post("/profiles")
def profile(request: ProfileRequest, db: Session = Depends(get_db)):
    try:
        user = local_user(db)
        if user is None:
            raise ValueError("Local user not found")
        if request.user_id and request.user_id != user.id:
            raise ValueError("User is not accessible")
        p = get_or_create_profile(db, user.id)
        db.commit()
        return {"id": p.id, "user_id": p.user_id}
    except ValueError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.get("/profiles/{profile_id}/mastery")
def profile_mastery(profile_id: str, knowledge_base_id: str, db: Session = Depends(get_db)):
    try:
        require_local_profile(db, profile_id)
        require_local_kb(db, knowledge_base_id)
        return mastery(db, profile_id, knowledge_base_id)
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/profiles/{profile_id}/recommendations")
def profile_recommendations(
    profile_id: str,
    knowledge_base_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    try:
        require_local_profile(db, profile_id)
        require_local_kb(db, knowledge_base_id)
        return recommendations(db, profile_id, knowledge_base_id, limit)
    except ValueError as exc:
        raise _error(exc) from exc
