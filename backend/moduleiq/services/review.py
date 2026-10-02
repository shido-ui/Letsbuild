from __future__ import annotations
from typing import Any
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.models import ReviewItem

VALID_STATUSES={"open","resolved","dismissed"}

def _serialize(x: ReviewItem)->dict[str,Any]:
    return {"id":x.id,"knowledge_base_id":x.knowledge_base_id,"entity_type":x.entity_type,"entity_id":x.entity_id,"reason":x.reason,"status":x.status,"metadata":x.metadata_json or {},"created_at":x.created_at.isoformat() if x.created_at else None,"updated_at":x.updated_at.isoformat() if x.updated_at else None}

def list_review_items(db:Session, knowledge_base_id:str, status:str|None="open", limit:int=100)->list[dict[str,Any]]:
    if status and status not in VALID_STATUSES: raise ValueError(f"Invalid review status: {status}")
    stmt=select(ReviewItem).where(ReviewItem.knowledge_base_id==knowledge_base_id)
    if status: stmt=stmt.where(ReviewItem.status==status)
    return [_serialize(x) for x in db.scalars(stmt.order_by(ReviewItem.created_at.desc()).limit(max(1,min(limit,200)))).all()]

def create_review_item(db:Session, knowledge_base_id:str, entity_type:str, entity_id:str, reason:str, metadata:dict[str,Any]|None=None)->dict[str,Any]:
    x=db.scalar(select(ReviewItem).where(ReviewItem.knowledge_base_id==knowledge_base_id,ReviewItem.entity_type==entity_type,ReviewItem.entity_id==entity_id,ReviewItem.status=="open"))
    if x:
        x.reason=reason; x.metadata_json={**(x.metadata_json or {}),**(metadata or {})}; db.flush(); return _serialize(x)
    x=ReviewItem(id=str(uuid4()),knowledge_base_id=knowledge_base_id,entity_type=entity_type,entity_id=entity_id,reason=reason,status="open",metadata_json=metadata or {})
    db.add(x); db.flush(); return _serialize(x)

def update_review_item(db:Session,item_id:str,status:str|None=None,reason:str|None=None)->dict[str,Any]:
    x=db.get(ReviewItem,item_id)
    if not x: raise LookupError("Review item not found")
    if status is not None:
        if status not in VALID_STATUSES: raise ValueError(f"Invalid review status: {status}")
        x.status=status
    if reason is not None: x.reason=reason
    db.flush(); return _serialize(x)
