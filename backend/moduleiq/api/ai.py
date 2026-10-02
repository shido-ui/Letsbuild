from __future__ import annotations
import hashlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.models import AIProvider, Credential
from moduleiq.infrastructure.database.session import get_db
from moduleiq.services.ai.crypto import CredentialCipher
from moduleiq.services.ai.errors import AIProviderError
from moduleiq.services.ai.provider_switching import active_provider, activate_provider, disconnect_provider, list_user_providers
from moduleiq.services.ai.providers import GeminiProvider, LocalModelProvider, OpenAICompatibleProvider

router=APIRouter(prefix="/ai",tags=["ai"])

class ProviderIn(BaseModel):
    provider_type: str=Field(pattern="^(gemini|openai_compatible|local)$")
    model_name: str|None=None
    base_url: str|None=None
    api_key: str|None=None

class ProviderOut(BaseModel):
    id:str
    provider_type:str
    model_name:str|None
    base_url:str|None
    enabled:bool
    active:bool
    connected:bool
    key_fingerprint:str|None

def _provider(row, secret):
    if row.provider_type=="gemini": return GeminiProvider(secret,row.model_name or "gemini-2.5-flash")
    if row.provider_type=="openai_compatible": return OpenAICompatibleProvider(secret,row.model_name or "gpt-5",row.base_url or "https://api.openai.com/v1")
    return LocalModelProvider(row.base_url or "http://127.0.0.1:8080/v1",row.model_name or "local")

def _user(db:Session):
    from moduleiq.infrastructure.database.models import User
    return db.scalar(select(User).order_by(User.created_at))

def _out(db, row):
    fingerprint=db.scalar(select(Credential.key_fingerprint).where(Credential.ai_provider_id==row.id))
    return ProviderOut(id=row.id,provider_type=row.provider_type,model_name=row.model_name,base_url=row.base_url,enabled=row.enabled,active=row.enabled,connected=fingerprint is not None,key_fingerprint=fingerprint)

@router.get("/providers",response_model=list[ProviderOut])
def list_providers(db:Session=Depends(get_db)):
    user=_user(db)
    if user is None: return []
    return [_out(db,r) for r in list_user_providers(db,user.id)]

@router.get("/providers/active",response_model=ProviderOut|None)
def get_active_provider(db:Session=Depends(get_db)):
    user=_user(db)
    if user is None: return None
    row=active_provider(db,user.id)
    if row is None: return None
    return _out(db,row)

@router.post("/providers",response_model=ProviderOut)
def connect_provider(body:ProviderIn,db:Session=Depends(get_db)):
    user=_user(db)
    if user is None: raise HTTPException(409,"No local user exists")
    if body.provider_type!="local" and not body.api_key: raise HTTPException(400,"api_key is required")
    secret=body.api_key or "local"
    row=AIProvider(id=__import__("uuid").uuid4().hex,user_id=user.id,provider_type=body.provider_type,model_name=body.model_name,base_url=body.base_url,enabled=False)
    db.add(row); db.flush()
    try: _provider(row,secret).test_connection()
    except AIProviderError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    db.add(Credential(ai_provider_id=row.id,secret_ciphertext=CredentialCipher().encrypt(secret),key_fingerprint=hashlib.sha256(secret.encode()).hexdigest()))
    db.commit()
    row=activate_provider(db,user.id,row.id)
    return _out(db,row)

@router.post("/providers/{provider_id}/activate",response_model=ProviderOut)
def activate(provider_id:str,db:Session=Depends(get_db)):
    user=_user(db)
    if user is None: raise HTTPException(409,"No local user exists")
    try: row=activate_provider(db,user.id,provider_id)
    except ValueError as exc: raise HTTPException(400,str(exc)) from exc
    return _out(db,row)

@router.post("/providers/{provider_id}/disconnect",response_model=ProviderOut)
def disconnect(provider_id:str,db:Session=Depends(get_db)):
    user=_user(db)
    if user is None: raise HTTPException(409,"No local user exists")
    try: row=disconnect_provider(db,user.id,provider_id)
    except ValueError as exc: raise HTTPException(404,str(exc)) from exc
    return _out(db,row)

@router.post("/providers/{provider_id}/test")
def test_provider(provider_id:str,db:Session=Depends(get_db)):
    row=db.get(AIProvider,provider_id)
    cred=db.scalar(select(Credential).where(Credential.ai_provider_id==provider_id))
    if not row or not cred: raise HTTPException(404,"Provider not found")
    try: _provider(row,CredentialCipher().decrypt(cred.secret_ciphertext or "")).test_connection()
    except AIProviderError as exc: raise HTTPException(400,str(exc)) from exc
    return {"ok":True}

@router.delete("/providers/{provider_id}")
def delete_provider(provider_id:str,db:Session=Depends(get_db)):
    row=db.get(AIProvider,provider_id)
    if not row: raise HTTPException(404,"Provider not found")
    db.delete(row)
    db.commit()
    return {"deleted":True}
