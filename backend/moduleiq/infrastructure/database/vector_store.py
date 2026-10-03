from __future__ import annotations
import math,struct
from pathlib import Path
from typing import Iterable

def pack(vector:Iterable[float])->bytes:
    values=[float(v) for v in vector]
    return struct.pack("<I",len(values))+struct.pack("<"+"f"*len(values),*values) if values else struct.pack("<I",0)

def unpack(blob:bytes|None)->list[float]:
    if not blob or len(blob)<4:return []
    n=struct.unpack("<I",blob[:4])[0]
    expected=4+4*n
    if len(blob)<expected:return []
    return list(struct.unpack("<"+"f"*n,blob[4:expected]))

def cosine(a:list[float],b:list[float])->float:
    if not a or not b or len(a)!=len(b):return 0.0
    dot=sum(x*y for x,y in zip(a,b));na=math.sqrt(sum(x*x for x in a));nb=math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0

class VectorStore:
    """Local vector-store facade. Uses ChromaDB when installed; SQLite BLOBs remain canonical."""
    def __init__(self,root:str):
        self.root=Path(root)/"vectors";self.root.mkdir(parents=True,exist_ok=True)
        self._chroma=None
        try:
            import chromadb
            self._chroma=chromadb.PersistentClient(path=str(self.root/"chroma"))
        except Exception:
            self._chroma=None

    @property
    def chroma_available(self)->bool:return self._chroma is not None

    def collection(self,name:str):
        if not self._chroma:return None
        safe=name.replace("/","_")
        return self._chroma.get_or_create_collection(safe)

    def upsert(self,collection:str,ids:list[str],vectors:list[list[float]],documents:list[str]|None=None,metadatas:list[dict]|None=None)->None:
        col=self.collection(collection)
        if col is not None:
            kwargs={"ids":ids,"embeddings":vectors}
            if documents:kwargs["documents"]=documents
            if metadatas:kwargs["metadatas"]=metadatas
            col.upsert(**kwargs)

    def query(self,collection:str,vector:list[float],limit:int=10)->dict:
        col=self.collection(collection)
        if col is None:return {"ids":[],"distances":[],"documents":[],"metadatas":[]}
        return col.query(query_embeddings=[vector],n_results=max(1,limit))
