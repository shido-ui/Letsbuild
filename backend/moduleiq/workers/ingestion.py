from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from huey import SqliteHuey
from sqlalchemy import select
from moduleiq.core.config import get_settings
from moduleiq.infrastructure.database.models import DocumentVersion, ProcessingJob, ProcessingStage
from moduleiq.infrastructure.database.session import SessionLocal
from moduleiq.infrastructure.document_engine.mineru_adapter import MinerUUnavailable, extract_with_mineru
from moduleiq.services.normalization import normalize_middle_json

settings=get_settings()
huey=SqliteHuey(filename=str(Path(settings.data_dir)/"huey.db"),immediate=False)

def _set_stage(db,job_id: str,ordinal: int,status: str,progress: float,error: str|None=None)->None:
    stage=db.scalar(select(ProcessingStage).where(ProcessingStage.processing_job_id==job_id,ProcessingStage.ordinal==ordinal))
    if stage:
        now=datetime.now(timezone.utc)
        if status=="processing" and stage.started_at is None: stage.started_at=now
        if status in {"complete","failed"}: stage.finished_at=now
        stage.status=status; stage.progress=progress; stage.error_message=error

@huey.task(retries=2,retry_delay=5)
def process_document(job_id: str)->str:
    with SessionLocal() as db:
        job=db.get(ProcessingJob,job_id)
        if job is None: return job_id
        version=db.get(DocumentVersion,job.document_version_id)
        if version is None:
            job.status="failed"; job.metadata_json={**(job.metadata_json or {}),"error":"Document version not found."}; db.commit(); return job_id
        job.status="processing"; job.attempts+=1; job.started_at=datetime.now(timezone.utc)
        version.processing_status="processing"
        _set_stage(db,job.id,1,"complete",1.0); _set_stage(db,job.id,2,"processing",0.0); db.commit()
        try:
            output_dir=Path(settings.storage_root)/"extractions"/version.id
            result=extract_with_mineru(Path(version.storage_uri),output_dir,tier=settings.mineru_tier,ocr_mode=settings.mineru_ocr_mode,image_analysis=settings.mineru_image_analysis)
            job.metadata_json={**(job.metadata_json or {}),"engine":result.engine,"engine_version":result.engine_version,"extraction_dir":str(result.output_dir),"page_count":result.page_count,"middle_json":str(result.middle_json_path),"markdown":str(result.markdown_path),"structured_content":str(result.structured_content_path)}
            version.metadata_json={**(version.metadata_json or {}),"extraction_engine":result.engine,"extraction_engine_version":result.engine_version,"extraction_dir":str(result.output_dir)}
            _set_stage(db,job.id,2,"complete",1.0); _set_stage(db,job.id,3,"complete",1.0)
            _set_stage(db,job.id,4,"processing",0.0); db.commit()
            counts=normalize_middle_json(db,version,result.middle_json_path,result.output_dir)
            job.metadata_json={**(job.metadata_json or {}),"normalized_counts":counts}
            _set_stage(db,job.id,4,"complete",1.0); _set_stage(db,job.id,5,"processing",0.0); _set_stage(db,job.id,5,"complete",1.0)
            version.processing_status="ready"; job.status="complete"; job.finished_at=datetime.now(timezone.utc); db.commit()
        except MinerUUnavailable as exc:
            _set_stage(db,job.id,2,"failed",0.0,str(exc)); version.processing_status="engine_unavailable"; job.status="failed"; job.metadata_json={**(job.metadata_json or {}),"error":str(exc)}; job.finished_at=datetime.now(timezone.utc); db.commit(); raise
        except Exception as exc:
            _set_stage(db,job.id,2,"failed",0.0,str(exc)); version.processing_status="extraction_failed"; job.status="retrying"; job.error_message=str(exc); db.commit(); raise
    return job_id
