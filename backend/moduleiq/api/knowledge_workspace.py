from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.session import get_db
from moduleiq.core.security import require_local_block, require_local_document, require_local_kb, require_local_material, require_local_page, require_local_version
from moduleiq.services.knowledge_workspace import hierarchy, overview, related_topics, source_object

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("/{knowledge_base_id}")
def get_workspace(knowledge_base_id: str, db: Session = Depends(get_db)):
    try:
        require_local_kb(db, knowledge_base_id)
        return overview(db, knowledge_base_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/{knowledge_base_id}/hierarchy")
def get_hierarchy(knowledge_base_id: str, db: Session = Depends(get_db)):
    try:
        require_local_kb(db, knowledge_base_id)
        return hierarchy(db, knowledge_base_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/{knowledge_base_id}/relationships")
def get_relationships(knowledge_base_id: str, db: Session = Depends(get_db)):
    try:
        require_local_kb(db, knowledge_base_id)
        return {"knowledge_base_id": knowledge_base_id, "cross_document_topics": related_topics(db, knowledge_base_id)}
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/source/{kind}/{object_id}")
def get_source(kind: str, object_id: str, db: Session = Depends(get_db)):
    try:
        loaders={"document":require_local_document,"version":require_local_version,"page":require_local_page,"block":require_local_block,"material":require_local_material}
        if kind in loaders:
            loaders[kind](db, object_id)
        return source_object(db, kind, object_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
