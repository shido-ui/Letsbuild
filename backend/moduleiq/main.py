from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from moduleiq.api.health import router as health_router
from moduleiq.core.config import settings

app = FastAPI(title="ModuleIQ API", version="0.1.0", docs_url="/api/docs", redoc_url="/api/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api")

@app.get("/api")
async def api_root() -> dict[str, str]:
    return {"service": "moduleiq-api", "status": "ok"}
