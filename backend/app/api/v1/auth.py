import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import (
    create_access_token, create_refresh_token, decode_token,
    hash_password, verify_password, get_current_user,
)
from app.models import Organization, User
from app.services.audit import write_audit

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str = Field(..., example="analyst@example.com")
    name: str = Field(..., example="Jane Analyst")
    password: str = Field(..., min_length=8, example="secret-pass")
    role: str = Field(default="Business Analyst")


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    org_id: str
    organization: Optional[dict] = None


async def _user_payload(db: AsyncSession, user: User) -> UserResponse:
    org = await db.get(Organization, user.org_id)
    return UserResponse(
        id=str(user.id), email=user.email, name=user.name, role=user.role,
        org_id=str(user.org_id),
        organization={"id": str(org.id), "name": org.name,
                      "settings": org.settings_json} if org else None)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "An account with this email already exists")
    org = Organization(name=f"{payload.name}'s Workspace", settings_json=_default_org_settings())
    db.add(org)
    await db.flush()
    user = User(
        email=payload.email.lower(), name=payload.name,
        password_hash=hash_password(payload.password),
        role=payload.role, org_id=org.id)
    db.add(user)
    await db.flush()
    await write_audit(db, action="user.registered", entity_type="user",
                      entity_id=str(user.id),
                      actor={"id": str(user.id), "email": user.email})
    await db.commit()
    await db.refresh(user)
    return _token_pair(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    await write_audit(db, action="user.login", entity_type="user",
                      entity_id=str(user.id),
                      actor={"id": str(user.id), "email": user.email})
    await db.commit()
    return _token_pair(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        claims = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc))
    if claims.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token required")
    try:
        user = await db.get(User, uuid.UUID(str(claims["sub"])))
    except (ValueError, KeyError):
        user = None
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return _token_pair(user)


@router.post("/logout")
async def logout(db: AsyncSession = Depends(get_db),
                 user: dict = Depends(get_current_user)):
    # JWTs are stateless; client discards tokens. Audit the event.
    await write_audit(db, action="user.logout", entity_type="user",
                      entity_id=user["id"], actor=user)
    await db.commit()
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
async def me(db: AsyncSession = Depends(get_db),
             claims: dict = Depends(get_current_user)):
    user = await db.get(User, uuid.UUID(str(claims["id"])))
    if not user:
        raise HTTPException(404, "User not found")
    return await _user_payload(db, user)


def _token_pair(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.email, user.role, str(user.org_id)),
        refresh_token=create_refresh_token(str(user.id)),
        user={"id": str(user.id), "email": user.email, "name": user.name,
              "role": user.role, "org_id": str(user.org_id)})


def _default_org_settings() -> dict:
    from app.core.config import settings
    return {
        "weights": dict(settings.SCORE_WEIGHTS),
        "conflict_confidence_threshold": settings.CONFLICT_CONFIDENCE_THRESHOLD,
        "default_analysis_mode": settings.DEFAULT_ANALYSIS_MODE,
        "default_lint_mode": settings.DEFAULT_LINT_MODE,
        "severity_thresholds": {"critical": ["confirmed_conflict"],
                                "high": ["needs_review_conflict", "high_ambiguity"]},
        "vague_lexicon": [],
        "standards": ["ISO/IEC/IEEE 29148", "INCOSE Guide for Writing Requirements"],
    }
