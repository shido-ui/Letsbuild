from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.session import get_db

router = APIRouter(tags=["system"])

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "moduleiq-api", "timestamp": datetime.now(timezone.utc).isoformat()}

@router.get("/ready")
async def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "service": "moduleiq-api"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is not ready") from exc
