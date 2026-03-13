"""User profile API endpoints."""

import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import UserProfile

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileResponse(BaseModel):
    id: int
    company_name: str | None = None
    offerings: list[str] = []
    target_markets: list[str] = []
    strengths: list[str] = []
    contact_info: dict = {}
    raw_notes: str | None = None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    company_name: str | None = None
    offerings: list[str] | None = None
    target_markets: list[str] | None = None
    strengths: list[str] | None = None
    contact_info: dict | None = None


@router.get("", response_model=ProfileResponse | None)
async def get_profile(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).limit(1))
    profile = result.scalar_one_or_none()
    if not profile:
        return None

    return ProfileResponse(
        id=profile.id,
        company_name=profile.company_name,
        offerings=json.loads(profile.offerings_json) if profile.offerings_json else [],
        target_markets=json.loads(profile.target_markets_json) if profile.target_markets_json else [],
        strengths=json.loads(profile.strengths_json) if profile.strengths_json else [],
        contact_info=json.loads(profile.contact_info_json) if profile.contact_info_json else {},
        raw_notes=profile.raw_notes,
    )


@router.put("", response_model=ProfileResponse)
async def update_profile(data: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).limit(1))
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile()
        db.add(profile)

    if data.company_name is not None:
        profile.company_name = data.company_name
    if data.offerings is not None:
        profile.offerings_json = json.dumps(data.offerings, ensure_ascii=False)
    if data.target_markets is not None:
        profile.target_markets_json = json.dumps(data.target_markets, ensure_ascii=False)
    if data.strengths is not None:
        profile.strengths_json = json.dumps(data.strengths, ensure_ascii=False)
    if data.contact_info is not None:
        profile.contact_info_json = json.dumps(data.contact_info, ensure_ascii=False)

    await db.commit()
    await db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        company_name=profile.company_name,
        offerings=json.loads(profile.offerings_json) if profile.offerings_json else [],
        target_markets=json.loads(profile.target_markets_json) if profile.target_markets_json else [],
        strengths=json.loads(profile.strengths_json) if profile.strengths_json else [],
        contact_info=json.loads(profile.contact_info_json) if profile.contact_info_json else {},
        raw_notes=profile.raw_notes,
    )
