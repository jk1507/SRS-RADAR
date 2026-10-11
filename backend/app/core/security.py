"""
Auth per PRD Section 12: JWT access (HS256) + refresh, PBKDF2 password
hashing, RBAC enforced in the backend on every protected route.

Implemented with the standard library only (hmac/hashlib/base64) so the
stack runs with zero additional dependencies; tokens are standard JWS
compact signatures (compatible with jwt libraries on the client).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db

PBKDF2_ITERATIONS = 260_000


# ---------------------------------------------------------------- passwords
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt_hex, hash_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


# ---------------------------------------------------------------- JWT (HS256)
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _sign(payload: Dict[str, Any], expires_in: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    body = {**payload, "iat": int(time.time()), "exp": int(time.time()) + expires_in}
    signing_input = f"{_b64url(json.dumps(header).encode())}.{_b64url(json.dumps(body).encode())}"
    sig = hmac.new(settings.JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(sig)}"


def create_access_token(user_id: str, email: str, role: str, org_id: str) -> str:
    return _sign({"sub": user_id, "email": email, "role": role, "org_id": org_id,
                  "type": "access"},
                 settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


def create_refresh_token(user_id: str) -> str:
    return _sign({"sub": user_id, "type": "refresh"},
                 settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)


def decode_token(token: str) -> Dict[str, Any]:
    """Verify signature + expiry; raise ValueError on failure."""
    try:
        header_b64, body_b64, sig_b64 = token.split(".")
    except ValueError:
        raise ValueError("malformed token")
    signing_input = f"{header_b64}.{body_b64}"
    expected = hmac.new(settings.JWT_SECRET.encode(), signing_input.encode(),
                        hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
        raise ValueError("bad signature")
    body = json.loads(_b64url_decode(body_b64))
    if body.get("exp", 0) < time.time():
        raise ValueError("token expired")
    return body


# ---------------------------------------------------------------- dependencies
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db),
                            token: Optional[str] = None) -> Dict[str, Any]:
    """Bearer header (preferred) or ?token= query (EventSource cannot send headers)."""
    auth = request.headers.get("Authorization", "")
    raw = auth[7:].strip() if auth.startswith("Bearer ") else (token or "")
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Missing bearer token")
    try:
        claims = decode_token(raw)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    if claims.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Access token required")
    from app.models import User
    import uuid as _uuid
    try:
        user_uuid = _uuid.UUID(str(claims["sub"]))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token subject")
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found or disabled")
    return {
        "id": str(user.id), "email": user.email, "name": user.name,
        "role": user.role, "org_id": str(user.org_id),
    }


def require_role(*roles: str):
    async def dependency(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Requires role: {'/'.join(roles)}")
        return user
    return dependency


async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[Dict[str, Any]]:
    """Auth when a token is present; anonymous falls back to the demo user."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            return await get_current_user(request, db)
        except HTTPException:
            return None
    return None
