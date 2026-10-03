from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from moduleiq.core.config import get_settings
from moduleiq.infrastructure.database.models import User
from moduleiq.infrastructure.database.session import get_db
from moduleiq.core.dependencies import oauth2_scheme, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


def verify_password(plain: str, hashed: str | None) -> bool:
    return bool(hashed) and pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(user_id: str) -> tuple[str, int]:
    settings = get_settings()
    expires = max(5, settings.access_token_expire_minutes)
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=expires)
    payload = {"sub": user_id, "exp": expire_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm), expires * 60


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_users = db.scalars(select(User).order_by(User.created_at)).all()
    existing_username = db.scalar(select(User).where(User.username == user_data.username))
    if existing_username:
        raise HTTPException(status_code=409, detail="Username already registered")

    if existing_users:
        # ModuleIQ v1 is intentionally single-user/local-first. Existing local-only
        # records can be upgraded into the authenticated account exactly once.
        if len(existing_users) != 1:
            raise HTTPException(status_code=409, detail="An account already exists")
        user = existing_users[0]
        if user.hashed_password:
            raise HTTPException(status_code=409, detail="An account already exists")
        user.username = user_data.username
        user.email = str(user_data.email)
        user.hashed_password = get_password_hash(user_data.password)
        user.is_active = True
    else:
        user = User(
            username=user_data.username,
            email=str(user_data.email),
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    identifier = form_data.username.strip()
    user = db.scalar(
        select(User).where((User.username == identifier) | (User.email == identifier))
    )
    if not user or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, ttl = create_access_token(user.id)
    return {"access_token": access_token, "token_type": "bearer", "expires_in": ttl}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out", "user_id": current_user.id}
