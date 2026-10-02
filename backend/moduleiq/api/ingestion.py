from __future__ import annotations
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.models import KnowledgeBase, ProcessingJob, ProcessingStage, DocumentVersion, Document, Material, Workspace, User
from moduleiq.core.security import require_local_kb
from moduleiq.infrastructure.database.session import get_db
from moduleiq.services.ingestion import IngestionError, create_ingestion_job, get_or_create_knowledge_base, recover_ingestion_job
from moduleiq.workers.ingestion import process_document
router=APIRouter(prefix="/ingestion",tags=["ingestion"])

class UploadResponse(BaseModel):
    duplicate: bool
    knowledge_base_id: str|None=None
    material_id: str|None=None
    document_id: str|None=None
    document_version_id: str|None=None
    processing_job_id: str|None=None
    filename: str|None=None
    size_bytes: int|None=None
    sha256: str|None=None
    page_count: int|None=None
    status: str|None=None

@router.get("/knowledge-bases")
def list_knowledge_bases(db: Session=Depends(get_db)):
    return [{"id":kb.id,"workspace_id":kb.workspace_id,"name":kb.name,"description":kb.description} for kb in db.scalars(select(KnowledgeBase).join(Workspace, KnowledgeBase.workspace_id==Workspace.id).join(User, Workspace.owner_id==User.id).where(User.email=="local@moduleiq").order_by(KnowledgeBase.created_at)).all()]

@router.post("/knowledge-bases")
def create_knowledge_base(name: str="My Knowledge",db: Session=Depends(get_db)):
    kb=get_or_create_knowledge_base(db,name.strip() or "My Knowledge"); db.commit()
    return {"id":kb.id,"workspace_id":kb.workspace_id,"name":kb.name}

@router.post("/upload",response_model=UploadResponse,status_code=201)
def upload_material(file: UploadFile=File(...),knowledge_base_id: str|None=None,on_duplicate: str="reject",db: Session=Depends(get_db)):
    try: result=create_ingestion_job(db,file,knowledge_base_id,on_duplicate)
    except IngestionError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except Exception as exc: raise HTTPException(status_code=500,detail=f"Upload failed: {exc}") from exc
    if not result.get("duplicate"): process_document(result["processing_job_id"])
    return result

@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: str, db: Session=Depends(get_db)):
    try:
        job = recover_ingestion_job(db, job_id)
        process_document(job.id)
        return {"id": job.id, "status": "queued", "recovered": True}
    except IngestionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/jobs/{job_id}")
def get_job(job_id: str,db: Session=Depends(get_db)):
    job=db.get(ProcessingJob,job_id)
    if job is None: raise HTTPException(status_code=404,detail="Processing job not found.")
    stages=db.scalars(select(ProcessingStage).where(ProcessingStage.processing_job_id==job.id).order_by(ProcessingStage.ordinal)).all()
    return {"id":job.id,"document_version_id":job.document_version_id,"status":job.status,"attempts":job.attempts,"started_at":job.started_at,"finished_at":job.finished_at,"error":(job.metadata_json or {}).get("error"),"stages":[{"name":s.stage_name,"status":s.status,"progress":s.progress,"error":s.error_message} for s in stages]}
