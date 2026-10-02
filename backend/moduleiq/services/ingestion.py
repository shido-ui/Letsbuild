from __future__ import annotations
import hashlib, os, uuid
from pathlib import Path
from typing import BinaryIO
from fastapi import UploadFile
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session
from moduleiq.core.config import get_settings
from moduleiq.infrastructure.database.models import Document, DocumentVersion, KnowledgeBase, Material, ProcessingJob, ProcessingStage, User, Workspace
settings=get_settings()
STAGES=("validation","document_analysis","extraction","normalization","finalization")

class IngestionError(ValueError): pass

def _safe_name(name: str|None)->str:
    value=Path(name or "material.pdf").name.strip()
    return (value if value not in {"",".",".."} else "material.pdf")[:500]

def _ensure_local_workspace(db: Session)->KnowledgeBase:
    user=db.scalar(select(User).where(User.email=="local@moduleiq"))
    if user is None:
        user=User(id=str(uuid.uuid4()),email="local@moduleiq",display_name="Local user"); db.add(user); db.flush()
    workspace=db.scalar(select(Workspace).where(Workspace.owner_id==user.id).order_by(Workspace.created_at))
    if workspace is None:
        workspace=Workspace(id=str(uuid.uuid4()),owner_id=user.id,name="Personal workspace"); db.add(workspace); db.flush()
    kb=db.scalar(select(KnowledgeBase).where(KnowledgeBase.workspace_id==workspace.id).order_by(KnowledgeBase.created_at))
    if kb is None:
        kb=KnowledgeBase(id=str(uuid.uuid4()),workspace_id=workspace.id,name="My Knowledge"); db.add(kb); db.flush()
    return kb

def get_or_create_knowledge_base(db: Session,name: str="My Knowledge")->KnowledgeBase:
    kb=_ensure_local_workspace(db)
    if kb.name==name: return kb
    existing=db.scalar(select(KnowledgeBase).where(KnowledgeBase.workspace_id==kb.workspace_id,KnowledgeBase.name==name))
    if existing: return existing
    kb=KnowledgeBase(id=str(uuid.uuid4()),workspace_id=kb.workspace_id,name=name); db.add(kb); db.flush(); return kb

def _copy_and_hash(src: BinaryIO,destination: Path,max_bytes:int)->tuple[str,int]:
    destination.parent.mkdir(parents=True,exist_ok=True); digest=hashlib.sha256(); total=0
    try:
        with destination.open("wb") as out:
            while True:
                chunk=src.read(1024*1024)
                if not chunk: break
                total+=len(chunk)
                if total>max_bytes: raise IngestionError("File exceeds the configured upload limit.")
                digest.update(chunk); out.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True); raise
    return digest.hexdigest(),total

def _pdf_metadata(path: Path)->tuple[int,dict[str,object]]:
    with path.open("rb") as fh:
        if fh.read(5)!=b"%PDF-": raise IngestionError("The uploaded file is not a valid PDF signature.")
    try:
        reader=PdfReader(str(path),strict=False); pages=len(reader.pages)
        if pages<1: raise IngestionError("The PDF contains no pages.")
        metadata={str(k):str(v) for k,v in (reader.metadata or {}).items() if v is not None}
        return pages,metadata
    except IngestionError: raise
    except Exception as exc: raise IngestionError(f"The PDF could not be parsed: {exc}") from exc

def create_ingestion_job(db: Session,upload: UploadFile,knowledge_base_id: str|None=None,on_duplicate: str="reject")->dict:
    if on_duplicate not in {"reject","reuse"}: raise IngestionError("on_duplicate must be 'reject' or 'reuse'.")
    kb=db.get(KnowledgeBase,knowledge_base_id) if knowledge_base_id else get_or_create_knowledge_base(db)
    if kb is None: raise IngestionError("Knowledge base not found.")
    filename=_safe_name(upload.filename); declared=(upload.content_type or "").lower()
    if declared and declared not in {"application/pdf","application/octet-stream"}: raise IngestionError("Only PDF material is supported in Phase 4.")
    temporary=Path(settings.storage_root)/".incoming"/f"{uuid.uuid4()}.upload"
    try:
        sha,size=_copy_and_hash(upload.file,temporary,settings.max_upload_bytes)
        if size==0: raise IngestionError("The uploaded file is empty.")
        pages,pdf_meta=_pdf_metadata(temporary)
        existing=db.scalar(select(Material).where(Material.knowledge_base_id==kb.id,Material.sha256==sha,Material.media_type=="application/pdf"))
        if existing:
            temporary.unlink(missing_ok=True)
            if on_duplicate=="reuse":
                document=db.scalar(select(Document).where(Document.material_id==existing.id).order_by(Document.created_at))
                job=db.scalar(select(ProcessingJob).join(DocumentVersion).where(DocumentVersion.document_id==document.id).order_by(ProcessingJob.created_at.desc())) if document else None
                return {"duplicate":True,"material_id":existing.id,"document_id":document.id if document else None,"processing_job_id":job.id if job else None}
            raise IngestionError("This exact file already exists in the selected knowledge base.")
        final_path=Path(settings.storage_root)/kb.workspace_id/kb.id/f"{sha}.pdf"; final_path.parent.mkdir(parents=True,exist_ok=True); os.replace(temporary,final_path)
        material=Material(id=str(uuid.uuid4()),knowledge_base_id=kb.id,name=filename,media_type="application/pdf",size_bytes=size,sha256=sha,metadata_json={"original_filename":filename,"content_type":declared or "application/pdf","page_count":pages,"pdf_metadata":pdf_meta}); db.add(material); db.flush()
        document=Document(id=str(uuid.uuid4()),material_id=material.id,title=Path(filename).stem,metadata_json={"page_count":pages}); db.add(document); db.flush()
        version=DocumentVersion(id=str(uuid.uuid4()),document_id=document.id,version_number=1,storage_uri=str(final_path),processing_status="queued",metadata_json={"sha256":sha,"page_count":pages}); db.add(version); db.flush()
        job=ProcessingJob(id=str(uuid.uuid4()),document_version_id=version.id,status="queued",attempts=0,metadata_json={"filename":filename,"page_count":pages}); db.add(job); db.flush()
        for ordinal,name in enumerate(STAGES,1): db.add(ProcessingStage(id=str(uuid.uuid4()),processing_job_id=job.id,stage_name=name,ordinal=ordinal,status="pending",progress=0.0))
        db.commit()
        return {"duplicate":False,"knowledge_base_id":kb.id,"material_id":material.id,"document_id":document.id,"document_version_id":version.id,"processing_job_id":job.id,"filename":filename,"size_bytes":size,"sha256":sha,"page_count":pages,"status":"queued"}
    except Exception:
        db.rollback(); temporary.unlink(missing_ok=True); raise
