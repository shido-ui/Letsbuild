from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.session import get_db
from moduleiq.core.security import require_local_kb
from moduleiq.services.search_engine import search
from moduleiq.services.ai.embeddings import EmbeddingService
from moduleiq.infrastructure.database.vector_store import VectorStore
from moduleiq.services.vector_index import semantic_query
from moduleiq.core.config import get_settings

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
        require_local_kb(db, knowledge_base_id)
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


@router.get("/semantic")
def semantic_search(
    knowledge_base_id: str,
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    try:
        require_local_kb(db, knowledge_base_id)
        result = semantic_query(
            EmbeddingService(cache_dir=f"{get_settings().data_dir}/models/embeddings"),
            VectorStore(get_settings().storage_root),
            knowledge_base_id,
            q,
            limit,
        )
        return result
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
