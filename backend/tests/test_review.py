from pathlib import Path
from sqlalchemy import create_engine,event
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database import models_import
from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database.models import KnowledgeBase,User,Workspace
from moduleiq.services.review import create_review_item,list_review_items,update_review_item
def test_review_queue(tmp_path:Path):
 e=create_engine(f"sqlite:///{tmp_path/'review.db'}")
 @event.listens_for(e,"connect")
 def fk(conn,_): conn.execute("PRAGMA foreign_keys=ON")
 Base.metadata.create_all(e)
 with Session(e) as db:
  db.add(User(id="u1",email="review@example.com"));db.commit()
  db.add(Workspace(id="w1",owner_id="u1",name="Workspace"));db.commit()
  db.add(KnowledgeBase(id="kb1",workspace_id="w1",name="Physics"));db.commit()
  a=create_review_item(db,"kb1","question","q1","Flagged for review",{"source":"user"})
  b=create_review_item(db,"kb1","question","q1","Still needs review");db.commit()
  assert a["id"]==b["id"] and len(list_review_items(db,"kb1"))==1
  assert update_review_item(db,a["id"],status="resolved")["status"]=="resolved";db.commit()
  assert list_review_items(db,"kb1")==[] and len(list_review_items(db,"kb1",status=None))==1
