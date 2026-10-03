from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash
from jwt import decode, encode
from jwt.exceptions import InvalidTokenError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from moduleiq.core.config import get_settings
from moduleiq.core.security import set_authenticated_user
from moduleiq.infrastructure.database.models import User
from moduleiq.infrastructure.database.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
password_hash = PasswordHash.recommended()


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    display_name: str | None = None
    is_active: bool

    class Config:
        from_attributes = True


def _settings():
    return get_settings()


def _token_for(user: User) -> Token:
    settings = _settings()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user.id, "iat": int(now.timestamp()), "exp": int(expires.timestamp())}
    token = encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return Token(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


def _find_user(db: Session, identity: str) -> User | None:
    return db.scalar(
        select(User).where(or_(User.username == identity, User.email == identity))
    )


def _authenticate(db: Session, identity: str, password: str) -> User | None:
    user = _find_user(db, identity)
    if user is None or not user.is_active or not user.hashed_password:
        return None
    try:
        valid = password_hash.verify(password, user.hashed_password)
    except Exception:
        return None
    return user if valid else None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    settings = _settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            raise credentials_exception
    except InvalidTokenError as exc:
        raise credentials_exception from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    set_authenticated_user(user.id)
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, db: Session = Depends(get_db)):
    existing = db.scalar(
        select(User).where(or_(User.username == body.username, User.email == body.email))
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Username or email already registered")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=password_hash.hash(body.password),
        display_name=body.username,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = _authenticate(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    set_authenticated_user(user.id)
    return _token_for(user)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # Access tokens are short-lived bearer credentials. Client logout removes the token;
    # server-side revocation is intentionally a later phase once refresh-token sessions exist.
    return {"message": "Successfully logged out", "user_id": current_user.id}
