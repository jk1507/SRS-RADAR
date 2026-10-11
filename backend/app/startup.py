"""Idempotent default seed: organization + demo user (PRD 14 DevEx)."""
from __future__ import annotations

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.core.security import hash_password
from app.models import Organization, User

DEMO_EMAIL = "jack@requirement-radar.dev"
DEMO_PASSWORD = "radar-demo-2026"


async def seed_defaults() -> None:
    async with AsyncSessionLocal() as db:
        org = (await db.execute(
            select(Organization).where(Organization.name == "Radar Labs"))).scalars().first()
        if org is None:
            from app.api.v1.auth import _default_org_settings
            org = Organization(name="Radar Labs", settings_json=_default_org_settings())
            db.add(org)
            await db.flush()

        user = (await db.execute(
            select(User).where(User.email == DEMO_EMAIL))).scalars().first()
        if user is None:
            db.add(User(
                email=DEMO_EMAIL, name="Jack", role="Lead Architect",
                password_hash=hash_password(DEMO_PASSWORD), org_id=org.id))
        await db.commit()
