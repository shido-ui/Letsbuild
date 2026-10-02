from uuid import uuid4
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.models import User, Workspace, KnowledgeBase, Material, Document, DocumentVersion, ProcessingJob, ProcessingStage
from moduleiq.services.ingestion import recover_ingestion_job

def test_failed_ingestion_job_can_be_recovered(tmp_path):
    engine=create_engine(f"sqlite:///{tmp_path / 'recovery.db'}")
    @event.listens_for(engine,"connect")
    def fk(dbapi_connection,_): dbapi_connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user=User(id=str(uuid4()),email="local@moduleiq"); db.add(user); db.flush()
        ws=Workspace(id=str(uuid4()),owner_id=user.id,name="Local"); db.add(ws); db.flush()
        kb=KnowledgeBase(id=str(uuid4()),workspace_id=ws.id,name="KB"); db.add(kb); db.flush()
        material=Material(id=str(uuid4()),knowledge_base_id=kb.id,name="x.pdf",media_type="application/pdf"); db.add(material); db.flush()
        doc=Document(id=str(uuid4()),material_id=material.id,title="x"); db.add(doc); db.flush()
        version=DocumentVersion(id=str(uuid4()),document_id=doc.id,version_number=1,storage_uri="/tmp/x.pdf",processing_status="failed"); db.add(version); db.flush()
        job=ProcessingJob(id=str(uuid4()),document_version_id=version.id,status="failed",attempts=3,error_message="boom"); db.add(job); db.flush()
        db.add(ProcessingStage(id=str(uuid4()),processing_job_id=job.id,stage_name="extraction",ordinal=3,status="failed",progress=0,error_message="boom"))
        db.commit()
        recovered=recover_ingestion_job(db,job.id)
        assert recovered.status=="queued" and recovered.attempts==0
        assert db.get(DocumentVersion,version.id).processing_status=="queued"
