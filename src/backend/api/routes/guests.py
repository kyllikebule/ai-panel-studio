"""嘉宾模板 CRUD 路由。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.dependencies import get_db
from ...db.models import Guest

router = APIRouter(prefix="/api/guests", tags=["guests"])


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    persona: str
    system_prompt: str
    speak_style: str
    avatar: str | None
    created_at: str


@router.get("/", response_model=list[GuestResponse])
async def list_guests(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Guest).order_by(Guest.id.desc()))
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
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(guest, k, v)
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
