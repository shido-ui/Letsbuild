from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from huey import SqliteHuey
from sqlalchemy import select
from moduleiq.core.config import get_settings
from moduleiq.infrastructure.database.models import DocumentVersion, ProcessingJob, ProcessingStage
from moduleiq.infrastructure.database.session import SessionLocal
settings=get_settings()
huey=SqliteHuey(filename=str(Path(settings.data_dir)/"huey.db"),immediate=False)

@huey.task(retries=2,retry_delay=5)
def prepare_document(job_id: str)->str:
    with SessionLocal() as db:
        job=db.get(ProcessingJob,job_id)
        if job is None: return job_id
        now=datetime.now(timezone.utc); job.status="processing"; job.attempts+=1; job.started_at=now
        stage=db.scalar(select(ProcessingStage).where(ProcessingStage.processing_job_id==job.id,ProcessingStage.ordinal==1))
        if stage: stage.status="complete"; stage.progress=1.0; stage.started_at=now; stage.finished_at=now
        version=db.get(DocumentVersion,job.document_version_id)
        if version: version.processing_status="ready_for_extraction"
        job.status="ready_for_extraction"; job.finished_at=datetime.now(timezone.utc); db.commit()
    return job_id
