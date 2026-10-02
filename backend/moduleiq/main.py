from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from moduleiq.api.health import router as health_router
from moduleiq.api.ingestion import router as ingestion_router
from moduleiq.api.ai import router as ai_router
from moduleiq.api.knowledge import router as knowledge_router
from moduleiq.api.questions import router as questions_router
from moduleiq.api.verification import router as verification_router
from moduleiq.api.solutions import router as solutions_router
from moduleiq.api.knowledge_workspace import router as knowledge_workspace_router
from moduleiq.api.search import router as search_router
from moduleiq.api.practice import router as practice_router
from moduleiq.api.adaptive import router as adaptive_router
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
app.include_router(ingestion_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(questions_router, prefix="/api")
app.include_router(verification_router, prefix="/api")
app.include_router(solutions_router, prefix="/api")
app.include_router(knowledge_workspace_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(practice_router, prefix="/api")
app.include_router(adaptive_router, prefix="/api")

@app.get("/api")
async def api_root() -> dict[str, str]:
    return {"service": "moduleiq-api", "status": "ok"}
