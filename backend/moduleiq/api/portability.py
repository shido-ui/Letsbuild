from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.session import get_db
from moduleiq.services.portability import export_bundle, import_bundle, validate_bundle

router = APIRouter(prefix="/portability", tags=["portability"])


class ImportRequest(BaseModel):
    bundle: dict[str, Any]
    name: str | None = Field(default=None, max_length=200)


@router.get("/export")
def export_data(knowledge_base_id: str, db: Session = Depends(get_db)):
    try:
        bundle = export_bundle(db, knowledge_base_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    body = json.dumps(bundle, ensure_ascii=False, indent=2)
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=moduleiq-export.json"},
    )


@router.post("/validate")
def validate_data(bundle: dict[str, Any]):
    try:
        return validate_bundle(bundle)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import", status_code=201)
def import_data(request: ImportRequest, db: Session = Depends(get_db)):
    try:
        return import_bundle(db, request.bundle, name=request.name)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Import failed safely; no partial import was committed.") from exc
