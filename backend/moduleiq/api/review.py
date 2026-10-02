from __future__ import annotations
from typing import Any
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.session import get_db
from moduleiq.services.review import create_review_item,list_review_items,update_review_item
router=APIRouter(prefix="/review",tags=["review"])
class CreateReviewRequest(BaseModel):
    knowledge_base_id:str
    entity_type:str=Field(min_length=1,max_length=50)
    entity_id:str=Field(min_length=1,max_length=36)
    reason:str=Field(min_length=1,max_length=100)
    metadata:dict[str,Any]={}
class UpdateReviewRequest(BaseModel):
    status:str|None=None
    reason:str|None=Field(default=None,min_length=1,max_length=100)
@router.get("/items")
def get_items(knowledge_base_id:str,status:str|None="open",limit:int=100,db:Session=Depends(get_db)):
    try:return {"items":list_review_items(db,knowledge_base_id,status,limit)}
    except ValueError as e:raise HTTPException(400,str(e))
@router.post("/items")
def create_item(p:CreateReviewRequest,db:Session=Depends(get_db)):return create_review_item(db,p.knowledge_base_id,p.entity_type,p.entity_id,p.reason,p.metadata)
@router.patch("/items/{item_id}")
def update_item(item_id:str,p:UpdateReviewRequest,db:Session=Depends(get_db)):
    try:return update_review_item(db,item_id,p.status,p.reason)
    except LookupError as e:raise HTTPException(404,str(e))
    except ValueError as e:raise HTTPException(400,str(e))
