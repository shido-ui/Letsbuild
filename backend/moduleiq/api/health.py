from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter(tags=["system"])

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "moduleiq-api", "timestamp": datetime.now(timezone.utc).isoformat()}

@router.get("/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready", "service": "moduleiq-api"}
