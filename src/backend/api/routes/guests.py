"""嘉宾模板 CRUD API + AI 生成。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.dependencies import get_db
from ...db.models import Guest

router = APIRouter(prefix="/api/guests", tags=["guests"])


# === Schema ===
class GuestCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    persona: str = Field(..., min_length=1)
    system_prompt: str = Field(..., min_length=1)
    speak_style: str = ""
    avatar: str = ""


class GuestUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    persona: str | None = None
    system_prompt: str | None = None
    speak_style: str | None = None
    avatar: str | None = None


class GuestResponse(BaseModel):
    id: int
    name: str
    persona: str
    system_prompt: str
    speak_style: str
    avatar: str | None
    created_at: str

    model_config = {"from_attributes": True}


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=4, max_length=200)
    count: int = Field(default=4, ge=2, le=6)


class GuestItem(BaseModel):
    name: str
    persona: str
    speak_style: str
    system_prompt: str


class GenerateResponse(BaseModel):
    guests: list[GuestItem]


# === CRUD ===
@router.get("/", response_model=list[GuestResponse])
async def list_guests(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Guest).order_by(Guest.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=GuestResponse, status_code=201)
async def create_guest(data: GuestCreate, db: AsyncSession = Depends(get_db)):
    guest = Guest(**data.model_dump())
    db.add(guest)
    await db.commit()
    await db.refresh(guest)
    return guest


@router.patch("/{guest_id}", response_model=GuestResponse)
async def update_guest(guest_id: int, data: GuestUpdate, db: AsyncSession = Depends(get_db)):
    guest = await db.get(Guest, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(guest, key, value)
    await db.commit()
    await db.refresh(guest)
    return guest


@router.delete("/{guest_id}", status_code=204)
async def delete_guest(guest_id: int, db: AsyncSession = Depends(get_db)):
    guest = await db.get(Guest, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    await db.delete(guest)
    await db.commit()


# === AI 生成 ===
@router.post("/generate", response_model=GenerateResponse)
async def generate_guests_endpoint(data: GenerateRequest):
    from src.logic.guest_generator import generate_guests
    from src.backend.core.deepseek import deepseek_chat_json

    class LLMClient:
        async def chat_json(self, prompt: str) -> dict:
            return await deepseek_chat_json([{"role": "user", "content": prompt}])

    try:
        guests = await generate_guests(data.topic, data.count, LLMClient())
        return GenerateResponse(guests=[
            GuestItem(name=g.name, persona=g.persona, speak_style=g.speak_style, system_prompt=g.system_prompt)
            for g in guests
        ])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
