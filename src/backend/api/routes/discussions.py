"""讨论 CRUD + 讨论内嘉宾管理 API。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ...db.dependencies import get_db
from ...db.models import Discussion, Host, Guest, DiscussionGuest, Message, Opinion

router = APIRouter(prefix="/api/discussions", tags=["discussions"])


# === 请求/响应 Schema ===
class HostCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(..., min_length=1)


class DiscussionCreate(BaseModel):
    topic: str = Field(..., min_length=1)
    host: HostCreate
    max_rounds: int = Field(default=5, ge=1, le=20)


class DiscussionUpdate(BaseModel):
    topic: str | None = None
    status: str | None = None
    current_round: int | None = None
    max_rounds: int | None = Field(None, ge=1, le=20)


class DiscussionResponse(BaseModel):
    id: int
    topic: str
    status: str
    max_rounds: int
    current_round: int
    host_id: int
    created_at: str

    class Config:
        from_attributes = True


class DiscussionDetailResponse(DiscussionResponse):
    host_name: str = ""
    guests: list[dict] = []


class AddGuestRequest(BaseModel):
    guest_id: int
    stance_override: str | None = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    host_id: int | None
    guest_id: int | None
    seq_num: int
    token_count: int
    created_at: str

    class Config:
        from_attributes = True


class OpinionResponse(BaseModel):
    id: int
    message_id: int
    stance_summary: str
    category: str
    confidence: float | None
    evidence: str | None
    created_at: str

    class Config:
        from_attributes = True


# === 讨论 CRUD ===
@router.get("/", response_model=list[DiscussionResponse])
async def list_discussions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Discussion).order_by(Discussion.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=DiscussionDetailResponse, status_code=201)
async def create_discussion(data: DiscussionCreate, db: AsyncSession = Depends(get_db)):
    # 先创建主持人
    host = Host(name=data.host.name, system_prompt=data.host.system_prompt)
    db.add(host)
    await db.flush()

    # 创建讨论
    discussion = Discussion(
        topic=data.topic,
        max_rounds=data.max_rounds,
        host_id=host.id,
    )
    db.add(discussion)
    await db.commit()
    await db.refresh(discussion)

    return DiscussionDetailResponse(
        id=discussion.id,
        topic=discussion.topic,
        status=discussion.status,
        max_rounds=discussion.max_rounds,
        current_round=discussion.current_round,
        host_id=discussion.host_id,
        created_at=discussion.created_at,
        host_name=host.name,
        guests=[],
    )


@router.get("/{discussion_id}", response_model=DiscussionDetailResponse)
async def get_discussion(discussion_id: int, db: AsyncSession = Depends(get_db)):
    discussion = await db.get(Discussion, discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    # 查关联的主持人和嘉宾
    host = await db.get(Host, discussion.host_id)
    result = await db.execute(
        select(DiscussionGuest).where(DiscussionGuest.discussion_id == discussion_id)
    )
    dg_list = result.scalars().all()

    guests = []
    for dg in dg_list:
        guest = await db.get(Guest, dg.guest_id)
        if guest:
            guests.append({
                "guest_id": guest.id,
                "name": guest.name,
                "avatar": guest.avatar,
                "persona": guest.persona,
                "stance_override": dg.stance_override,
                "is_active": bool(dg.is_active),
            })

    return DiscussionDetailResponse(
        id=discussion.id,
        topic=discussion.topic,
        status=discussion.status,
        max_rounds=discussion.max_rounds,
        current_round=discussion.current_round,
        host_id=discussion.host_id,
        created_at=discussion.created_at,
        host_name=host.name if host else "",
        guests=guests,
    )


@router.patch("/{discussion_id}", response_model=DiscussionResponse)
async def update_discussion(
    discussion_id: int, data: DiscussionUpdate, db: AsyncSession = Depends(get_db)
):
    discussion = await db.get(Discussion, discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(discussion, key, value)
    await db.commit()
    await db.refresh(discussion)
    return discussion


@router.delete("/{discussion_id}", status_code=204)
async def delete_discussion(discussion_id: int, db: AsyncSession = Depends(get_db)):
    discussion = await db.get(Discussion, discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    await db.delete(discussion)
    await db.commit()


# === 讨论内嘉宾管理 ===
@router.post("/{discussion_id}/guests", status_code=201)
async def add_guest_to_discussion(
    discussion_id: int, data: AddGuestRequest, db: AsyncSession = Depends(get_db)
):
    discussion = await db.get(Discussion, discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    guest = await db.get(Guest, data.guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    existing = await db.execute(
        select(DiscussionGuest).where(
            DiscussionGuest.discussion_id == discussion_id,
            DiscussionGuest.guest_id == data.guest_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Guest already in discussion")

    dg = DiscussionGuest(
        discussion_id=discussion_id,
        guest_id=data.guest_id,
        stance_override=data.stance_override,
    )
    db.add(dg)
    await db.commit()
    return {"message": "Guest added to discussion", "discussion_id": discussion_id, "guest_id": data.guest_id}


@router.delete("/{discussion_id}/guests/{guest_id}", status_code=204)
async def remove_guest_from_discussion(
    discussion_id: int, guest_id: int, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(DiscussionGuest).where(
            DiscussionGuest.discussion_id == discussion_id,
            DiscussionGuest.guest_id == guest_id,
        )
    )
    dg = result.scalar_one_or_none()
    if not dg:
        raise HTTPException(status_code=404, detail="Guest not in discussion")
    await db.delete(dg)
    await db.commit()


# === 查询：消息 & 观点 ===
@router.get("/{discussion_id}/messages", response_model=list[MessageResponse])
async def list_messages(discussion_id: int, db: AsyncSession = Depends(get_db)):
    discussion = await db.get(Discussion, discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    result = await db.execute(
        select(Message)
        .where(Message.discussion_id == discussion_id)
        .order_by(Message.seq_num.asc())
    )
    return result.scalars().all()


@router.get("/{discussion_id}/opinions", response_model=list[OpinionResponse])
async def list_opinions(discussion_id: int, db: AsyncSession = Depends(get_db)):
    discussion = await db.get(Discussion, discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    result = await db.execute(
        select(Opinion)
        .join(Message)
        .where(Message.discussion_id == discussion_id)
        .order_by(Opinion.created_at.asc())
    )
    return result.scalars().all()
