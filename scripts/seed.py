from __future__ import annotations
import sys
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"backend"))
from sqlalchemy import select
from moduleiq.infrastructure.database.models import User,Workspace,KnowledgeBase,LearnerProfile
from moduleiq.infrastructure.database.session import SessionLocal

def main():
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email=="local@moduleiq"))
        if user is None:
            users=db.scalars(select(User).order_by(User.created_at)).all()
            user=users[0] if len(users)==1 else None
        if user is None:
            user=User(id=str(uuid4()),email="local@moduleiq",display_name="Local account",is_active=True)
            db.add(user);db.flush()
        ws=db.scalar(select(Workspace).where(Workspace.owner_id==user.id).order_by(Workspace.created_at))
        if ws is None:
            ws=Workspace(id=str(uuid4()),owner_id=user.id,name="Personal workspace");db.add(ws);db.flush()
        kb=db.scalar(select(KnowledgeBase).where(KnowledgeBase.workspace_id==ws.id).order_by(KnowledgeBase.created_at))
        if kb is None:
            kb=KnowledgeBase(id=str(uuid4()),workspace_id=ws.id,name="My Knowledge");db.add(kb)
        profile=db.scalar(select(LearnerProfile).where(LearnerProfile.user_id==user.id))
        if profile is None:db.add(LearnerProfile(id=str(uuid4()),user_id=user.id))
        db.commit()
        print("ModuleIQ seed ready")
if __name__=="__main__":main()
