from __future__ import annotations
from huey import SqliteHuey
from pathlib import Path
from moduleiq.core.config import get_settings
from moduleiq.infrastructure.database.session import SessionLocal
from moduleiq.infrastructure.database.vector_store import VectorStore
from moduleiq.services.ai.embeddings import EmbeddingService
from moduleiq.services.vector_index import index_knowledge_base
settings=get_settings()
huey=SqliteHuey(filename=str(Path(settings.data_dir)/"huey.db"),immediate=False)

@huey.task(retries=1,retry_delay=10)
def embed_knowledge_base(kb_id:str)->dict:
    with SessionLocal() as db:
        return index_knowledge_base(db,kb_id,EmbeddingService(cache_dir=str(Path(settings.data_dir)/"models/embeddings")),VectorStore(settings.storage_root))
