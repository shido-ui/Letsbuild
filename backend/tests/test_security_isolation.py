from uuid import uuid4
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.models import User, Workspace, KnowledgeBase, AIProvider
from moduleiq.core.security import require_local_kb, require_local_provider

def make_engine(tmp_path):
    engine=create_engine(f"sqlite:///{tmp_path / 'security.db'}")
    @event.listens_for(engine,"connect")
    def fk(dbapi_connection,_): dbapi_connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    return engine

def test_foreign_workspace_isolation(tmp_path):
    engine=make_engine(tmp_path)
    with Session(engine) as db:
        local=User(id=str(uuid4()),email="local@moduleiq")
        other=User(id=str(uuid4()),email="other@example.com")
        db.add_all([local,other]); db.flush()
        ws1=Workspace(id=str(uuid4()),owner_id=local.id,name="Local")
        ws2=Workspace(id=str(uuid4()),owner_id=other.id,name="Other")
        db.add_all([ws1,ws2]); db.flush()
        kb1=KnowledgeBase(id=str(uuid4()),workspace_id=ws1.id,name="Local KB")
        kb2=KnowledgeBase(id=str(uuid4()),workspace_id=ws2.id,name="Other KB")
        db.add_all([kb1,kb2]); db.commit()
        assert require_local_kb(db,kb1.id).id==kb1.id
        try: require_local_kb(db,kb2.id)
        except ValueError as exc: assert "not found" in str(exc).lower()
        else: raise AssertionError("foreign knowledge base was accessible")

def test_foreign_provider_isolation(tmp_path):
    engine=make_engine(tmp_path)
    with Session(engine) as db:
        local=User(id=str(uuid4()),email="local@moduleiq")
        other=User(id=str(uuid4()),email="other2@example.com")
        db.add_all([local,other]); db.flush()
        provider=AIProvider(id=str(uuid4()),user_id=other.id,provider_type="local",enabled=True)
        db.add(provider); db.commit()
        try: require_local_provider(db,provider.id)
        except ValueError as exc: assert "not found" in str(exc).lower()
        else: raise AssertionError("foreign provider was accessible")
