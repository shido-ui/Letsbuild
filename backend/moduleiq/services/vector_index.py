from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.models import Concept,Question,Topic,Material,Document,DocumentVersion,Page,Block
from moduleiq.infrastructure.database.vector_store import VectorStore,pack
from moduleiq.services.ai.embeddings import EmbeddingService

def _records(db:Session,kb_id:str):
    questions=db.scalars(select(Question).where(Question.knowledge_base_id==kb_id)).all()
    topics=db.scalars(select(Topic).join(Topic.chapter).join(__import__("moduleiq.infrastructure.database.models",fromlist=["Section"]).Section).join( __import__("moduleiq.infrastructure.database.models",fromlist=["DocumentVersion"]).DocumentVersion).join(__import__("moduleiq.infrastructure.database.models",fromlist=["Document"]).Document).join(Material).where(Material.knowledge_base_id==kb_id)).all()
    concepts=db.scalars(select(Concept).join(Concept.subtopic).join(Topic).join(__import__("moduleiq.infrastructure.database.models",fromlist=["Chapter"]).Chapter).join(__import__("moduleiq.infrastructure.database.models",fromlist=["Section"]).Section).join(__import__("moduleiq.infrastructure.database.models",fromlist=["DocumentVersion"]).DocumentVersion).join(__import__("moduleiq.infrastructure.database.models",fromlist=["Document"]).Document).join(Material).where(Material.knowledge_base_id==kb_id)).all()
    return [(q,"question",q.text) for q in questions]+[(t,"topic",t.name) for t in topics]+[(c,"concept",c.name+" "+(c.definition or "")) for c in concepts]

def index_knowledge_base(db:Session,kb_id:str,service:EmbeddingService,store:VectorStore)->dict:
    rows=_records(db,kb_id)
    embedded=service.embed([text for _,_,text in rows]) if rows else []
    ids=[];vectors=[];docs=[];metas=[]
    for (obj,kind,text_value),result in zip(rows,embedded):
        ids.append(kind+":"+obj.id);vectors.append(result.vector);docs.append(text_value);metas.append({"kb":kb_id,"kind":kind,"object_id":obj.id})
        obj.embedding=pack(result.vector)
    if ids:store.upsert("kb-"+kb_id,ids,vectors,docs,metas)
    db.commit()
    return {"knowledge_base_id":kb_id,"indexed":len(ids),"model":service.model_name}

def semantic_query(service:EmbeddingService,store:VectorStore,kb_id:str,q:str,limit:int=10):
    query=service.embed_one(q).vector
    return store.query("kb-"+kb_id,query,limit=max(1,min(limit,50)))
