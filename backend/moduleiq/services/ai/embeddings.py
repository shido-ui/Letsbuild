from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

@dataclass
class EmbeddingResult:
    model:str
    vector:list[float]

class EmbeddingService:
    """Lazy local sentence-transformer embeddings with an explicit model directory."""
    def __init__(self,model_name:str="all-MiniLM-L6-v2",cache_dir:str="./data/models/embeddings"):
        self.model_name=model_name;self.cache_dir=Path(cache_dir);self.cache_dir.mkdir(parents=True,exist_ok=True);self._model=None

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError("Install the local-ai extra to enable semantic embeddings.") from exc
            self._model=SentenceTransformer(self.model_name,cache_folder=str(self.cache_dir))
        return self._model

    def embed(self,texts:Sequence[str])->list[EmbeddingResult]:
        if not texts:return []
        model=self._load()
        vectors=model.encode(list(texts),normalize_embeddings=True).tolist()
        return [EmbeddingResult(self.model_name,[float(x) for x in vector]) for vector in vectors]

    def embed_one(self,text:str)->EmbeddingResult:
        return self.embed([text])[0]
