from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.session import get_db
from moduleiq.services.search_engine import search

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def global_search(
    knowledge_base_id: str,
    q: str = Query(..., min_length=1, max_length=500),
    kind: str | None = Query(default=None),
    document_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        return search(
            db,
            knowledge_base_id,
            q,
            kind=kind,
            document_id=document_id,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
