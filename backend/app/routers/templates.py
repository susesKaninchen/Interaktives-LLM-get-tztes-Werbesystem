"""Template CRUD endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import Template

router = APIRouter(prefix="/api/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    name: str
    category: str  # email, landing_page, phone_script
    content: str
    variables_json: str | None = None


class TemplateUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    content: str | None = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    category: str
    content: str
    variables_json: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TemplateResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template).order_by(Template.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(data: TemplateCreate, db: AsyncSession = Depends(get_db)):
    template = Template(
        name=data.name,
        category=data.category,
        content=data.content,
        variables_json=data.variables_json,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: int, data: TemplateUpdate, db: AsyncSession = Depends(get_db)):
    template = await db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if data.name is not None:
        template.name = data.name
    if data.category is not None:
        template.category = data.category
    if data.content is not None:
        template.content = data.content
    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=204)
async def delete_template(template_id: int, db: AsyncSession = Depends(get_db)):
    template = await db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(template)
    await db.commit()
