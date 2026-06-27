# DDD 阶段实施计划

> **日期:** 2026-06-27
> **基于:** `docs/ddd_design.md`
> **总任务数:** 14, **预计产出文件:** ~32

**Goal:** 搭建 FastAPI 后端分层骨架 + Vue3 前端演播厅 3 页面

**Architecture:** FastAPI 5层骨架（core/db/api/services）→ 前端 Vite 工程 → UI UX Pro Max 设计系统 → 3 页面逐页开发

**Tech Stack:** Python 3.11+ / FastAPI / SQLAlchemy / SQLite | Vue 3 / Element Plus / Pinia / Vue Router / Vite

## Global Constraints

- 后端仅搭建分层骨架，不写 AI 业务逻辑（services/ 层只定义函数签名，WS 只定义框架）
- 前端所有页面必须先调用 UI UX Pro Max 技能生成 `docs/ui_design_spec.md`，再写 Vue 代码
- 每子任务完成必须 Git 分段提交，格式 `[DDD-子任务] 描述`
- 固定产出目录：`src/backend/` `src/frontend/` `docs/`

---

### Task 1: 项目依赖文件

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `src/backend/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.30
pydantic>=2.7.0
pydantic-settings>=2.2.0
aiosqlite>=0.20.0
httpx>=0.27.0
python-dotenv>=1.0.1
```

- [ ] **Step 2: 创建 .env.example**

```
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DATABASE_URL=sqlite:///./data/ai_panel.db
```

- [ ] **Step 3: 创建 src/backend/__init__.py**（空文件）

- [ ] **Step 4: 安装依赖**

```bash
pip install -r requirements.txt
```

Expected: 全部安装成功，无报错

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env.example src/backend/__init__.py
git commit -m "[DDD-依赖] FastAPI+SQLAlchemy+httpx依赖配置"
```

---

### Task 2: Core 配置层

**Files:**
- Create: `src/backend/core/__init__.py`
- Create: `src/backend/core/config.py`

**Interfaces:**
- Produces: `Settings` 类 (pydantic BaseSettings)，字段 `llm_provider`, `deepseek_api_key`, `deepseek_base_url`, `database_url`

- [ ] **Step 1: 创建 core/__init__.py**（空文件）

- [ ] **Step 2: 创建 core/config.py**

```python
"""应用配置，从 .env / 环境变量读取。"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: str = "deepseek"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    database_url: str = "sqlite:///./data/ai_panel.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

- [ ] **Step 3: 验证配置可导入**

```bash
python -c "from src.backend.core.config import settings; print(settings.llm_provider)"
```

Expected: 输出 `deepseek`

- [ ] **Step 4: Commit**

```bash
git add src/backend/core/__init__.py src/backend/core/config.py
git commit -m "[DDD-配置] pydantic-settings配置+env读取"
```

---

### Task 3: DeepSeek SDK 封装

**Files:**
- Create: `src/backend/core/deepseek.py`

**Interfaces:**
- Produces: `deepseek_chat(messages, model, stream, max_retries)` → dict / Generator
- Produces: `deepseek_chat_json(messages, model)` → dict (parsed JSON response)
- Produces: `get_deepseek_client()` → httpx.AsyncClient

**Dependencies:** Task 2 (`settings`)

- [ ] **Step 1: 创建 core/deepseek.py**

```python
"""DeepSeek API 全功能 SDK：同步/流式/重试/速率限制。"""
import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from .config import settings

# === 速率限制：简单 token bucket ===
class RateLimiter:
    def __init__(self, rpm: int = 30):
        self.rpm = rpm
        self._last_call = 0.0

    async def wait(self):
        now = time.monotonic()
        min_interval = 60.0 / self.rpm
        wait_time = min_interval - (now - self._last_call)
        if wait_time > 0:
            import asyncio
            await asyncio.sleep(wait_time)
        self._last_call = time.monotonic()

rate_limiter = RateLimiter(rpm=30)


# === 客户端工厂 ===
def get_deepseek_client(timeout: float = 120.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.deepseek_base_url,
        headers={
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        },
        timeout=httpx.Timeout(timeout),
    )


# === 同步调用 ===
async def deepseek_chat(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    max_retries: int = 3,
    stream: bool = False,
) -> Dict[str, Any]:
    """通用 DeepSeek Chat Completions 调用（同步或流式）。"""

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }

    await rate_limiter.wait()

    client = get_deepseek_client()
    last_error = None

    for attempt in range(max_retries):
        try:
            response = await client.post("/v1/chat/completions", json=payload)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                import asyncio
                await asyncio.sleep(retry_after)
                continue

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            last_error = e
            if attempt < max_retries - 1:
                import asyncio
                await asyncio.sleep(2 ** attempt)
            continue
        finally:
            await client.aclose()

    raise RuntimeError(f"DeepSeek API failed after {max_retries} retries. Last error: {last_error}")


# === 流式调用 ===
async def deepseek_chat_stream(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    max_retries: int = 3,
) -> AsyncGenerator[str, None]:
    """流式 DeepSeek Chat Completions，逐 token yield delta content。"""

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    await rate_limiter.wait()

    client = get_deepseek_client(timeout=300.0)

    try:
        async with client.stream("POST", "/v1/chat/completions", json=payload) as response:
            if response.status_code == 429:
                import asyncio
                await asyncio.sleep(5)
                raise RuntimeError("Rate limited on stream request")

            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
    finally:
        await client.aclose()


# === JSON 模式调用 ===
async def deepseek_chat_json(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    temperature: float = 0.3,
    max_tokens: int = 1024,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """调用 DeepSeek 并强制解析 JSON 响应。"""

    result = await deepseek_chat(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
        stream=False,
    )

    content = result["choices"][0]["message"]["content"]

    # 尝试提取 JSON 块
    content = content.strip()
    if content.startswith("```"):
        # 去掉 markdown 代码块标记
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"DeepSeek 返回内容无法解析为 JSON: {content[:200]}")
```

- [ ] **Step 2: 验证模块导入**

```bash
python -c "from src.backend.core.deepseek import deepseek_chat, deepseek_chat_stream, deepseek_chat_json, get_deepseek_client; print('All functions importable')"
```

Expected: `All functions importable`

- [ ] **Step 3: Commit**

```bash
git add src/backend/core/deepseek.py
git commit -m "[DDD-DeepSeek] 全功能SDK: 同步/流式/重试/限速/JSON解析"
```

---

### Task 4: 数据库层

**Files:**
- Create: `src/backend/db/__init__.py`
- Create: `src/backend/db/database.py`
- Create: `src/backend/db/models.py`

**Interfaces:**
- Produces: `engine` (SQLAlchemy AsyncEngine), `async_session` (async_sessionmaker), `init_db()`
- Produces: ORM 类 `Host`, `Discussion`, `Guest`, `DiscussionGuest`, `Message`, `Opinion`

**Dependencies:** Task 2 (`settings`)

- [ ] **Step 1: 创建 db/__init__.py**（空文件）

- [ ] **Step 2: 创建 db/database.py**

```python
"""SQLite 数据库引擎、会话工厂、初始化。"""
import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from ..core.config import settings

# SQLite 使用 aiosqlite 驱动
DATABASE_URL = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """执行建表脚本并创建默认数据目录。"""
    # 确保 data 目录存在
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    async with engine.begin() as conn:
        # 读取并执行 init_sqlite.sql
        schema_path = Path(__file__).parent.parent.parent.parent / "schema" / "init_sqlite.sql"
        sql_content = schema_path.read_text(encoding="utf-8")

        # 逐条执行（跳过注释行）
        for statement in sql_content.split(";"):
            stmt = statement.strip()
            if stmt and not stmt.startswith("--"):
                await conn.execute(text(stmt))
```

- [ ] **Step 3: 创建 db/models.py**

```python
"""SQLAlchemy ORM 模型 —— 6 实体映射。"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float, ForeignKey, CheckConstraint,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Host(Base):
    __tablename__ = "host"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=False)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    discussions = relationship("Discussion", back_populates="host", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="host")


class Discussion(Base):
    __tablename__ = "discussion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    max_rounds = Column(Integer, nullable=False, default=5)
    current_round = Column(Integer, nullable=False, default=0)
    host_id = Column(Integer, ForeignKey("host.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    __table_args__ = (
        CheckConstraint("status IN ('pending','active','paused','completed')", name="ck_discussion_status"),
    )

    host = relationship("Host", back_populates="discussions")
    discussion_guests = relationship("DiscussionGuest", back_populates="discussion", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="discussion", cascade="all, delete-orphan")


class Guest(Base):
    __tablename__ = "guest"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    avatar = Column(String)
    persona = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    speak_style = Column(String)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    discussion_guests = relationship("DiscussionGuest", back_populates="guest", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="guest")


class DiscussionGuest(Base):
    __tablename__ = "discussion_guest"

    discussion_id = Column(Integer, ForeignKey("discussion.id", ondelete="CASCADE"), primary_key=True)
    guest_id = Column(Integer, ForeignKey("guest.id", ondelete="CASCADE"), primary_key=True)
    stance_override = Column(Text)
    is_active = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("discussion_id", "guest_id", name="uq_discussion_guest"),
    )

    discussion = relationship("Discussion", back_populates="discussion_guests")
    guest = relationship("Guest", back_populates="discussion_guests")


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discussion_id = Column(Integer, ForeignKey("discussion.id", ondelete="CASCADE"), nullable=False)
    host_id = Column(Integer, ForeignKey("host.id", ondelete="SET NULL"))
    guest_id = Column(Integer, ForeignKey("guest.id", ondelete="SET NULL"))
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    seq_num = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    __table_args__ = (
        CheckConstraint("role IN ('host','guest','system')", name="ck_message_role"),
        CheckConstraint(
            "host_id IS NOT NULL OR guest_id IS NOT NULL",
            name="ck_message_sender"
        ),
        Index("idx_message_discussion_seq", "discussion_id", "seq_num"),
    )

    discussion = relationship("Discussion", back_populates="messages")
    host = relationship("Host", back_populates="messages")
    guest = relationship("Guest", back_populates="messages")
    opinion = relationship("Opinion", back_populates="message", uselist=False, cascade="all, delete-orphan")


class Opinion(Base):
    __tablename__ = "opinion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("message.id", ondelete="CASCADE"), nullable=False, unique=True)
    stance_summary = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    confidence = Column(Float)
    evidence = Column(Text)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    __table_args__ = (
        CheckConstraint(
            "category IN ('consensus','disagreement','neutral')",
            name="ck_opinion_category"
        ),
        Index("idx_opinion_message", "message_id"),
    )

    message = relationship("Message", back_populates="opinion")
```

- [ ] **Step 4: 验证 ORM 可导入且无语法错误**

```bash
python -c "from src.backend.db.models import Host, Discussion, Guest, DiscussionGuest, Message, Opinion; print('6 ORM models OK')"
```

Expected: `6 ORM models OK`

- [ ] **Step 5: Commit**

```bash
git add src/backend/db/
git commit -m "[DDD-数据库] SQLAlchemy ORM 6实体+异步引擎+init_db"
```

---

### Task 5: API 路由 — 嘉宾模板 CRUD

**Files:**
- Create: `src/backend/api/__init__.py`
- Create: `src/backend/api/routes/__init__.py`
- Create: `src/backend/api/routes/guests.py`

**Interfaces:**
- Produces: `router` (APIRouter, prefix="/api/guests", tags=["guests"])
- Endpoints: `GET /` `POST /` `PATCH /{id}` `DELETE /{id}`

**Dependencies:** Task 4 (models + db session)

- [ ] **Step 1: 创建 api/__init__.py**（空文件）

- [ ] **Step 2: 创建 api/routes/__init__.py**（空文件）

- [ ] **Step 3: 创建 api/routes/guests.py**

```python
"""嘉宾模板 CRUD API。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ...db.database import async_session
from ...db.models import Guest

router = APIRouter(prefix="/api/guests", tags=["guests"])


# === 请求/响应 Schema ===
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

    class Config:
        from_attributes = True


# === 依赖：获取 DB 会话 ===
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


# === 路由 ===
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
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
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
```

- [ ] **Step 4: 验证路由模块可导入**

```bash
python -c "from src.backend.api.routes.guests import router; print('Guest router OK:', router.prefix)"
```

Expected: `Guest router OK: /api/guests`

- [ ] **Step 5: Commit**

```bash
git add src/backend/api/
git commit -m "[DDD-API-嘉宾] Guest CRUD路由+Pydantic Schema"
```

---

### Task 6: API 路由 — 讨论 CRUD

**Files:**
- Create: `src/backend/api/routes/discussions.py`

**Interfaces:**
- Produces: `router` (APIRouter, prefix="/api/discussions", tags=["discussions"])
- Endpoints: `GET /` `POST /` `GET /{id}` `PATCH /{id}` `DELETE /{id}`
- Sub-routes: `POST /{id}/guests` `DELETE /{id}/guests/{guest_id}`
- Sub-routes: `GET /{id}/messages` `GET /{id}/opinions`

**Dependencies:** Task 4, Task 5

- [ ] **Step 1: 创建 api/routes/discussions.py**

```python
"""讨论 CRUD + 讨论内嘉宾管理 API。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from ...db.database import async_session
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


# === 依赖 ===
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


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
```

- [ ] **Step 2: 验证路由模块可导入**

```bash
python -c "from src.backend.api.routes.discussions import router; print('Discussion router OK:', router.prefix)"
```

Expected: `Discussion router OK: /api/discussions`

- [ ] **Step 3: Commit**

```bash
git add src/backend/api/routes/discussions.py
git commit -m "[DDD-API-讨论] Discussion CRUD+嘉宾关联+消息/观点查询"
```

---

### Task 7: WebSocket 框架 + 服务层空桩 + FastAPI 入口

**Files:**
- Create: `src/backend/api/ws/__init__.py`
- Create: `src/backend/api/ws/studio.py`
- Create: `src/backend/services/__init__.py`
- Create: `src/backend/services/discussion_service.py`
- Create: `src/backend/services/guest_service.py`
- Create: `src/backend/main.py`

**Interfaces:**
- Produces: WS endpoint `/ws/discussion/{id}`
- Produces: `discussion_service.py` 空桩函数 `create_discussion()`, `update_discussion_status()`, `start_discussion_flow()`（均为 `raise NotImplementedError`）
- Produces: `guest_service.py` 空桩函数 `get_orchestration_context()`（`raise NotImplementedError`）
- Produces: `main.py` FastAPI app, CORS, mount routers + WS

**Dependencies:** Task 5, Task 6

- [ ] **Step 1: 创建 api/ws/__init__.py**（空文件）

- [ ] **Step 2: 创建 api/ws/studio.py**

```python
"""演播厅 WebSocket — 框架层（不含 AI 编排逻辑）。"""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# 连接池：{discussion_id: [websocket, ...]}
active_connections: dict[int, list[WebSocket]] = {}


async def broadcast(discussion_id: int, event: str, payload: dict):
    """向讨论室所有客户端广播消息。"""
    connections = active_connections.get(discussion_id, [])
    message = json.dumps({"event": event, **payload}, ensure_ascii=False)
    disconnected = []
    for ws in connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        connections.remove(ws)


@router.websocket("/ws/discussion/{discussion_id}")
async def studio_ws(websocket: WebSocket, discussion_id: int):
    await websocket.accept()

    # 加入连接池
    active_connections.setdefault(discussion_id, []).append(websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "event": "error",
                    "code": "INVALID_JSON",
                    "message": "消息格式无效，需要 JSON",
                }, ensure_ascii=False))
                continue

            action = data.get("action", "")

            # === DDD 阶段：仅回显 + 框架占位，不写 AI 逻辑 ===
            if action == "start":
                await websocket.send_text(json.dumps({
                    "event": "system",
                    "message": "讨论启动请求已接收。AI 编排逻辑将在后续版本实现。",
                }, ensure_ascii=False))

            elif action == "pause":
                await broadcast(discussion_id, "system", {
                    "message": "讨论已暂停",
                })

            elif action == "resume":
                await broadcast(discussion_id, "system", {
                    "message": "讨论已恢复",
                })

            elif action == "stop":
                await broadcast(discussion_id, "system", {
                    "message": "讨论已结束",
                })
                # 后期在此补充 discussion_end 事件 + summary

            else:
                await websocket.send_text(json.dumps({
                    "event": "error",
                    "code": "UNKNOWN_ACTION",
                    "message": f"未知操作: {action}",
                }, ensure_ascii=False))

    except WebSocketDisconnect:
        pass
    finally:
        active_connections.get(discussion_id, []).remove(websocket)
```

- [ ] **Step 3: 创建 services/__init__.py**（空文件）

- [ ] **Step 4: 创建 services/discussion_service.py**

```python
"""讨论业务服务 —— DDD阶段仅定义函数签名，不写AI逻辑。"""


async def create_discussion(topic: str, host_name: str, host_prompt: str, guest_ids: list[int]):
    """创建讨论并绑定主持人+嘉宾。"""
    raise NotImplementedError("AI 编排逻辑将在后续版本实现")


async def update_discussion_status(discussion_id: int, status: str):
    """更新讨论状态。"""
    raise NotImplementedError("AI 编排逻辑将在后续版本实现")


async def start_discussion_flow(discussion_id: int):
    """启动讨论编排流程：主持人开场 → 嘉宾自主发言 → 观点提炼 → 总结。"""
    raise NotImplementedError("AI 编排逻辑将在后续版本实现")
```

- [ ] **Step 5: 创建 services/guest_service.py**

```python
"""嘉宾业务服务 —— DDD阶段仅定义函数签名。"""


async def get_orchestration_context(discussion_id: int) -> dict:
    """获取讨论编排上下文（transcript + 嘉宾定义 + 观点列表）。"""
    raise NotImplementedError("AI 编排逻辑将在后续版本实现")
```

- [ ] **Step 6: 创建 main.py**

```python
"""AI Panel Studio — FastAPI 应用入口。"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.guests import router as guest_router
from .api.routes.discussions import router as discussion_router
from .api.ws.studio import router as ws_router
from .db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时初始化数据库。"""
    await init_db()
    yield


app = FastAPI(
    title="AI Panel Studio",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(guest_router)
app.include_router(discussion_router)
app.include_router(ws_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 7: 验证 FastAPI 应用可启动**

```bash
python -c "from src.backend.main import app; print('FastAPI app OK:', app.title)"
```

Expected: `FastAPI app OK: AI Panel Studio`

- [ ] **Step 8: Commit**

```bash
git add src/backend/main.py src/backend/api/ws/ src/backend/services/
git commit -m "[DDD-入口] FastAPI主入口+WebSocket框架+服务层空桩"
```

---

### Task 8: UI 设计规范文档（UI UX Pro Max）

**Files:**
- Write: `docs/ui_design_spec.md`（当前为空，需填内容）
- Create: `src/frontend/src/styles/variables.css`

**Interfaces:**
- Produces: CSS 变量集合（颜色/间距/字号/阴影/动画），供组件引用

**前置条件：** 必须调用 UI UX Pro Max 技能生成设计系统

- [ ] **Step 1: 调用 UI UX Pro Max 技能**

```bash
Skill: ui-ux-pro-max:design
```

目标关键词：
- 产品类型：dashboard, admin panel
- 风格：科技风直播间 / 圆桌演播厅 / dark mode / glassmorphism / neon glow
- 配色：深色底 + 霓虹强调色（主色 cyan/blue + 角色色卡 gold blue green purple orange）
- 组件：card, button, modal, table, form

- [ ] **Step 2: 根据 UI UX Pro Max 输出填写 `docs/ui_design_spec.md`**

文档至少包含：
```markdown
# AI Panel Studio — UI 设计规范

## 1. 配色方案 (CSS 变量)
--color-bg-primary: #0a0e17
--color-bg-secondary: #111827
--color-bg-card: rgba(17, 24, 39, 0.85)
--color-border-glow: #00d4ff
--color-accent-cyan: #00d4ff
--color-accent-gold: #f0b90b
--color-role-host: #f0b90b
--color-role-guest-a: #3b82f6
--color-role-guest-b: #10b981
--color-role-guest-c: #a855f7
--color-role-guest-d: #f97316
--color-consensus: #10b981
--color-disagreement: #ef4444
--color-neutral: #6b7280
--color-text-primary: #e5e7eb
--color-text-secondary: #9ca3af

## 2. 排版
--font-family: 'Inter', 'PingFang SC', sans-serif
--font-size-title: 20px
--font-size-body: 14px
--font-size-small: 12px

## 3. 卡片组件
...（毛玻璃、圆角12px、发光边框 1px、悬停抬升、发言中脉冲动画）

## 4. 四分区布局
...（2×2 Grid, gap 1px 发光分割线，每区 overflow-y: auto）

## 5. 响应式断点
- ≥1440px: 2×2 Grid
- 768-1439px: 2列布局
- <768px: 单列堆叠
```

- [ ] **Step 3: 从设计规范提取 CSS 变量到 `variables.css`**

```css
/* AI Panel Studio — 全局 CSS 变量（由 docs/ui_design_spec.md 生成） */
:root {
  --color-bg-primary: #0a0e17;
  --color-bg-secondary: #111827;
  --color-bg-card: rgba(17, 24, 39, 0.85);
  --color-border-glow: #00d4ff;
  --color-accent-cyan: #00d4ff;
  --color-accent-gold: #f0b90b;
  --color-role-host: #f0b90b;
  --color-role-guest-a: #3b82f6;
  --color-role-guest-b: #10b981;
  --color-role-guest-c: #a855f7;
  --color-role-guest-d: #f97316;
  --color-consensus: #10b981;
  --color-disagreement: #ef4444;
  --color-neutral: #6b7280;
  --color-text-primary: #e5e7eb;
  --color-text-secondary: #9ca3af;

  --font-family: 'Inter', 'PingFang SC', sans-serif;
  --font-size-title: 20px;
  --font-size-body: 14px;
  --font-size-small: 12px;

  --card-radius: 12px;
  --card-padding: 16px;
  --card-gap: 12px;
  --card-border: 1px solid rgba(0, 212, 255, 0.3);
  --card-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
  --card-backdrop: blur(12px);

  --grid-gap: 1px;
  --grid-divider: 1px solid rgba(0, 212, 255, 0.15);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: var(--font-family);
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  background: var(--color-bg-primary);
}
```

- [ ] **Step 4: Commit**

```bash
git add docs/ui_design_spec.md src/frontend/src/styles/variables.css
git commit -m "[DDD-设计规范] UI UX Pro Max 生成科技风演播厅设计系统+CSS变量"
```

---

### Task 9: 前端项目脚手架

**Files:**
- Create: `src/frontend/package.json`
- Create: `src/frontend/vite.config.ts`
- Create: `src/frontend/tsconfig.json`
- Create: `src/frontend/tsconfig.node.json`
- Create: `src/frontend/index.html`
- Create: `src/frontend/src/main.ts`
- Create: `src/frontend/src/App.vue`
- Create: `src/frontend/src/env.d.ts`
- Create: `src/frontend/src/router/index.ts`
- Create: `src/frontend/src/stores/discussion.ts`
- Create: `src/frontend/src/stores/guest.ts`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "ai-panel-studio",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.3.0",
    "pinia": "^2.1.0",
    "element-plus": "^2.7.0",
    "@element-plus/icons-vue": "^2.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "vue-tsc": "^2.0.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

- [ ] **Step 3: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "jsx": "preserve",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "noEmit": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"]
}
```

- [ ] **Step 4: 创建 tsconfig.node.json** `{"compilerOptions": {"composite": true, "module": "ESNext", "moduleResolution": "bundler", "allowSyntheticDefaultImports": true}, "include": ["vite.config.ts"]}`

- [ ] **Step 5: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Panel Studio — 演播厅</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

- [ ] **Step 6: 创建 src/main.ts**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './styles/variables.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
```

- [ ] **Step 7: 创建 src/App.vue**

```vue
<template>
  <router-view />
</template>

<script setup lang="ts">
</script>
```

- [ ] **Step 8: 创建 src/env.d.ts**

```typescript
/// <reference types="vite/client" />
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
```

- [ ] **Step 9: 创建 src/router/index.ts**

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomePage.vue'),
    },
    {
      path: '/config/:discussionId?',
      name: 'config',
      component: () => import('@/views/GuestConfigPage.vue'),
    },
    {
      path: '/studio/:discussionId',
      name: 'studio',
      component: () => import('@/views/StudioPage.vue'),
    },
  ],
})

export default router
```

- [ ] **Step 10: 创建 src/stores/discussion.ts**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Discussion {
  id: number
  topic: string
  status: string
  host_name: string
  max_rounds: number
  current_round: number
  created_at: string
  guest_count?: number
}

export const useDiscussionStore = defineStore('discussion', () => {
  const discussions = ref<Discussion[]>([])
  const currentDiscussion = ref<Discussion | null>(null)
  const messages = ref<any[]>([])
  const opinions = ref<any[]>([])

  async function fetchDiscussions() {
    const res = await fetch('/api/discussions')
    discussions.value = await res.json()
  }

  async function createDiscussion(data: any) {
    const res = await fetch('/api/discussions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    currentDiscussion.value = await res.json()
    return currentDiscussion.value
  }

  async function loadDiscussion(id: number) {
    const res = await fetch(`/api/discussions/${id}`)
    currentDiscussion.value = await res.json()
  }

  return { discussions, currentDiscussion, messages, opinions, fetchDiscussions, createDiscussion, loadDiscussion }
})
```

- [ ] **Step 11: 创建 src/stores/guest.ts**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface GuestTemplate {
  id: number
  name: string
  persona: string
  system_prompt: string
  speak_style: string
  avatar: string | null
}

export const useGuestStore = defineStore('guest', () => {
  const guestTemplates = ref<GuestTemplate[]>([])
  const activeGuests = ref<GuestTemplate[]>([])

  async function fetchGuests() {
    const res = await fetch('/api/guests')
    guestTemplates.value = await res.json()
  }

  async function createGuest(data: Partial<GuestTemplate>) {
    const res = await fetch('/api/guests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    const guest = await res.json()
    guestTemplates.value.unshift(guest)
    return guest
  }

  async function deleteGuest(id: number) {
    await fetch(`/api/guests/${id}`, { method: 'DELETE' })
    guestTemplates.value = guestTemplates.value.filter(g => g.id !== id)
  }

  return { guestTemplates, activeGuests, fetchGuests, createGuest, deleteGuest }
})
```

- [ ] **Step 12: 安装前端依赖**

```bash
cd src/frontend && npm install
```

Expected: 依赖全部安装成功

- [ ] **Step 13: Commit**

```bash
git add src/frontend/
git commit -m "[DDD-前端脚手架] Vite+Vue3+Router+Pinia+ElementPlus工程搭建"
```

---

### Task 10: 首页 — 讨论列表页

**Files:**
- Create: `src/frontend/src/views/HomePage.vue`

**Interfaces:**
- Consumes: `useDiscussionStore` (from Task 9)
- Produces: 讨论列表页面，含新建按钮、历史列表、状态标签

- [ ] **Step 1: 创建 HomePage.vue**

```vue
<template>
  <div class="home-page">
    <header class="home-header">
      <h1 class="home-title">AI Panel Studio</h1>
      <p class="home-subtitle">圆桌演播厅 · 专家讨论</p>
      <el-button type="primary" size="large" @click="$router.push('/config')">
        <el-icon><Plus /></el-icon> 新建讨论
      </el-button>
    </header>

    <section class="discussion-list" v-loading="loading">
      <div
        class="discussion-card"
        v-for="d in store.discussions"
        :key="d.id"
        @click="$router.push(`/studio/${d.id}`)"
      >
        <div class="card-left">
          <h3 class="card-topic">{{ d.topic }}</h3>
          <div class="card-meta">
            <span>主持人：{{ d.host_name }}</span>
            <span>轮次：{{ d.current_round }}/{{ d.max_rounds }}</span>
          </div>
        </div>
        <div class="card-right">
          <el-tag
            :type="statusMap[d.status]?.type"
            size="small"
          >
            {{ statusMap[d.status]?.label }}
          </el-tag>
          <span class="card-time">{{ formatTime(d.created_at) }}</span>
        </div>
      </div>
      <el-empty v-if="!loading && store.discussions.length === 0" description="暂无讨论，点击上方按钮创建" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useDiscussionStore } from '@/stores/discussion'

const store = useDiscussionStore()
const loading = ref(false)

const statusMap: Record<string, { label: string; type: 'info' | 'warning' | 'success' }> = {
  pending: { label: '待开始', type: 'info' },
  active: { label: '进行中', type: 'warning' },
  paused: { label: '已暂停', type: 'info' },
  completed: { label: '已完成', type: 'success' },
}

function formatTime(ts: string) {
  return new Date(ts).toLocaleDateString('zh-CN')
}

onMounted(async () => {
  loading.value = true
  await store.fetchDiscussions()
  loading.value = false
})
</script>

<style scoped>
.home-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 24px;
}

.home-header {
  text-align: center;
  margin-bottom: 40px;
}

.home-title {
  font-size: 32px;
  color: var(--color-accent-cyan);
  margin: 0 0 8px;
}

.home-subtitle {
  color: var(--color-text-secondary);
  margin: 0 0 24px;
}

.discussion-list {
  display: flex;
  flex-direction: column;
  gap: var(--card-gap);
}

.discussion-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--card-padding);
  background: var(--color-bg-card);
  backdrop-filter: var(--card-backdrop);
  border: var(--card-border);
  border-radius: var(--card-radius);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.discussion-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 24px rgba(0, 212, 255, 0.25);
}

.card-topic {
  margin: 0 0 8px;
  font-size: 16px;
}

.card-meta {
  display: flex;
  gap: 16px;
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}

.card-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.card-time {
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}
</style>
```

- [ ] **Step 2: 验证前端编译通过**

```bash
cd src/frontend && npx vue-tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add src/frontend/src/views/HomePage.vue
git commit -m "[DDD-首页] 讨论列表页: 卡片列表+状态标签+新建入口"
```

---

### Task 11: 嘉宾配置页

**Files:**
- Create: `src/frontend/src/views/GuestConfigPage.vue`

**Interfaces:**
- Consumes: `useDiscussionStore`, `useGuestStore` (from Task 9)
- Produces: 议题输入、嘉宾人数选择、嘉宾预览 UI

- [ ] **Step 1: 创建 GuestConfigPage.vue**

```vue
<template>
  <div class="config-page">
    <header class="config-header">
      <el-button text @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <h1>配置讨论</h1>
    </header>

    <el-form :model="form" label-position="top" class="config-form">
      <!-- 议题输入 -->
      <el-form-item label="讨论议题">
        <el-input
          v-model="form.topic"
          placeholder="输入讨论主题，如：AI 是否应该被严格监管？"
          size="large"
        />
      </el-form-item>

      <!-- 主持人配置 -->
      <el-form-item label="主持人名称">
        <el-input v-model="form.hostName" placeholder="如：张主持人" />
      </el-form-item>
      <el-form-item label="主持风格 Prompt">
        <el-input
          v-model="form.hostPrompt"
          type="textarea"
          :rows="2"
          placeholder="描述主持人的风格..."
        />
      </el-form-item>

      <!-- 轮次 -->
      <el-form-item label="讨论轮次">
        <el-slider v-model="form.maxRounds" :min="2" :max="10" show-stops :marks="roundMarks" />
      </el-form-item>

      <!-- 嘉宾选择 -->
      <el-form-item label="选择嘉宾">
        <div class="guest-grid">
          <div
            class="guest-select-card"
            v-for="g in guestStore.guestTemplates"
            :key="g.id"
            :class="{ selected: selectedGuestIds.includes(g.id) }"
            @click="toggleGuest(g.id)"
          >
            <div class="guest-avatar">{{ g.name[0] }}</div>
            <div class="guest-name">{{ g.name }}</div>
            <div class="guest-style">{{ g.speak_style || g.persona }}</div>
          </div>
        </div>
      </el-form-item>

      <!-- 已选嘉宾预览 -->
      <el-form-item label="已选嘉宾 ({{ selectedGuestIds.length }}人)">
        <div class="preview-list">
          <div class="preview-card" v-for="g in selectedGuests" :key="g.id">
            <span class="preview-name">{{ g.name }}</span>
            <span class="preview-persona">{{ g.persona }}</span>
            <el-button text type="danger" size="small" @click.stop="toggleGuest(g.id)">移除</el-button>
          </div>
        </div>
      </el-form-item>

      <!-- 提交 -->
      <el-button
        type="primary"
        size="large"
        :disabled="!canStart"
        :loading="submitting"
        @click="startDiscussion"
      >
        进入演播厅
      </el-button>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useDiscussionStore } from '@/stores/discussion'
import { useGuestStore } from '@/stores/guest'

const router = useRouter()
const discussionStore = useDiscussionStore()
const guestStore = useGuestStore()
const submitting = ref(false)
const selectedGuestIds = ref<number[]>([])

const form = reactive({
  topic: '',
  hostName: '张主持人',
  hostPrompt: '你是专业讨论主持人，保持中立，用标准中文开场、追问、串联、总结。',
  maxRounds: 5,
})

const roundMarks = {
  2: '2轮',
  5: '5轮',
  8: '8轮',
  10: '10轮',
}

const canStart = computed(() => form.topic.trim() && selectedGuestIds.value.length >= 2)

const selectedGuests = computed(() =>
  guestStore.guestTemplates.filter(g => selectedGuestIds.value.includes(g.id))
)

function toggleGuest(id: number) {
  const idx = selectedGuestIds.value.indexOf(id)
  if (idx >= 0) {
    selectedGuestIds.value.splice(idx, 1)
  } else {
    selectedGuestIds.value.push(id)
  }
}

async function startDiscussion() {
  submitting.value = true
  try {
    const discussion = await discussionStore.createDiscussion({
      topic: form.topic,
      host: {
        name: form.hostName,
        system_prompt: form.hostPrompt,
      },
      max_rounds: form.maxRounds,
    })
    // 逐个添加嘉宾
    for (const guestId of selectedGuestIds.value) {
      await fetch(`/api/discussions/${discussion.id}/guests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guest_id: guestId }),
      })
    }
    router.push(`/studio/${discussion.id}`)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  guestStore.fetchGuests()
})
</script>

<style scoped>
.config-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 24px;
}

.config-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.config-header h1 {
  margin: 0;
  font-size: 24px;
}

.config-form {
  background: var(--color-bg-card);
  backdrop-filter: var(--card-backdrop);
  border: var(--card-border);
  border-radius: var(--card-radius);
  padding: 32px;
}

.guest-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  width: 100%;
}

.guest-select-card {
  text-align: center;
  padding: 16px 12px;
  border: 2px solid transparent;
  border-radius: var(--card-radius);
  background: rgba(0, 212, 255, 0.05);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.guest-select-card.selected {
  border-color: var(--color-accent-cyan);
  background: rgba(0, 212, 255, 0.15);
}

.guest-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-accent-gold);
  color: #000;
  font-size: 20px;
  font-weight: bold;
  line-height: 48px;
  margin: 0 auto 8px;
}

.guest-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.guest-style {
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}

.preview-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.preview-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(0, 212, 255, 0.08);
  border-radius: 8px;
}

.preview-name {
  font-weight: 600;
  min-width: 80px;
}

.preview-persona {
  flex: 1;
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}
</style>
```

- [ ] **Step 2: 验证前端编译**

```bash
cd src/frontend && npx vue-tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add src/frontend/src/views/GuestConfigPage.vue
git commit -m "[DDD-配置页] 嘉宾配置: 议题输入+主持人+嘉宾选择+预览"
```

---

### Task 12: 演播厅组件 — GuestCard + ChatMessage

**Files:**
- Create: `src/frontend/src/components/GuestCard.vue`
- Create: `src/frontend/src/components/ChatMessage.vue`

**Interfaces:**
- GuestCard Props: `guest: {id, name, avatar, persona, speak_style}`, `isActive: boolean`, `isSpeaking: boolean`, `colorTheme: string`
- ChatMessage Props: `message: {id, role, content, sender_name, seq_num, token_count}`, `senderColor: string`, `isStreaming: boolean`

- [ ] **Step 1: 创建 GuestCard.vue**

```vue
<template>
  <div
    class="guest-card"
    :class="{ active: isActive, speaking: isSpeaking }"
    :style="{ '--card-color': colorTheme }"
  >
    <div class="guest-card-avatar">{{ guest.name[0] }}</div>
    <div class="guest-card-info">
      <div class="guest-card-name">{{ guest.name }}</div>
      <div class="guest-card-role">{{ guest.speak_style || guest.persona }}</div>
    </div>
    <div v-if="isSpeaking" class="speaking-indicator">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
    <el-tag v-if="!isActive" size="small" type="info">离线</el-tag>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  guest: { id: number; name: string; avatar?: string | null; persona: string; speak_style?: string }
  isActive: boolean
  isSpeaking: boolean
  colorTheme: string
}>()
</script>

<style scoped>
.guest-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px var(--card-padding);
  border-radius: var(--card-radius);
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.04);
  transition: border-color 0.3s, box-shadow 0.3s;
}

.guest-card.active {
  border-color: var(--card-color);
  background: color-mix(in srgb, var(--card-color) 8%, transparent);
}

.guest-card.speaking {
  border-color: var(--card-color);
  box-shadow: 0 0 16px color-mix(in srgb, var(--card-color) 40%, transparent);
  animation: pulse-glow 1.5s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 8px color-mix(in srgb, var(--card-color) 20%, transparent); }
  50% { box-shadow: 0 0 20px color-mix(in srgb, var(--card-color) 50%, transparent); }
}

.guest-card-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--card-color);
  color: #000;
  font-weight: bold;
  font-size: 18px;
  line-height: 40px;
  text-align: center;
  flex-shrink: 0;
}

.guest-card-info {
  flex: 1;
  min-width: 0;
}

.guest-card-name {
  font-weight: 600;
  font-size: 14px;
}

.guest-card-role {
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.speaking-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--card-color);
  animation: blink 1s ease-in-out infinite;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
</style>
```

- [ ] **Step 2: 创建 ChatMessage.vue**

```vue
<template>
  <div class="chat-message" :class="{ host: message.role === 'host', streaming: isStreaming }">
    <div class="msg-header">
      <span class="msg-sender" :style="{ color: senderColor }">
        {{ message.sender_name || (message.role === 'host' ? '主持人' : '嘉宾') }}
      </span>
      <span class="msg-seq">#{{ message.seq_num }}</span>
    </div>
    <div class="msg-content">{{ message.content }}<span v-if="isStreaming" class="cursor-blink">|</span></div>
    <div class="msg-footer">
      <span class="msg-tokens">{{ message.token_count }} tokens</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message: {
    id: number
    role: string
    content: string
    sender_name?: string
    seq_num: number
    token_count?: number
  }
  senderColor: string
  isStreaming: boolean
}>()
</script>

<style scoped>
.chat-message {
  padding: 12px var(--card-padding);
  margin-bottom: 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border-left: 3px solid transparent;
}

.chat-message.host {
  border-left-color: var(--color-role-host);
  background: rgba(240, 185, 11, 0.06);
}

.chat-message.streaming {
  border-left-color: var(--color-accent-cyan);
}

.msg-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.msg-sender {
  font-weight: 600;
  font-size: var(--font-size-small);
}

.msg-seq {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.msg-content {
  font-size: var(--font-size-body);
  line-height: 1.6;
  color: var(--color-text-primary);
}

.cursor-blink {
  animation: blink 1s step-end infinite;
  color: var(--color-accent-cyan);
}

.msg-footer {
  margin-top: 8px;
}

.msg-tokens {
  font-size: 11px;
  color: var(--color-text-secondary);
}
</style>
```

- [ ] **Step 3: 验证组件编译**

```bash
cd src/frontend && npx vue-tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
git add src/frontend/src/components/GuestCard.vue src/frontend/src/components/ChatMessage.vue
git commit -m "[DDD-组件] GuestCard发言动画+ChatMessage消息卡片"
```

---

### Task 13: 演播厅组件 — OpinionPanel

**Files:**
- Create: `src/frontend/src/components/OpinionPanel.vue`

**Interfaces:**
- Props: `opinions: {id, stance_summary, category, confidence, evidence}[]`, `loading: boolean`

- [ ] **Step 1: 创建 OpinionPanel.vue**

```vue
<template>
  <div class="opinion-panel">
    <h4 class="panel-title">观点汇总</h4>
    <div v-if="loading" class="loading">分析中...</div>
    <div v-else-if="opinions.length === 0" class="empty">暂无观点</div>
    <div
      v-for="op in opinions"
      :key="op.id"
      class="opinion-item"
      :class="'category-' + op.category"
    >
      <div class="opinion-header">
        <el-tag
          :type="categoryTagType(op.category)"
          size="small"
        >
          {{ categoryLabel(op.category) }}
        </el-tag>
        <span v-if="op.confidence" class="confidence">
          置信度 {{ (op.confidence * 100).toFixed(0) }}%
        </span>
      </div>
      <p class="opinion-summary">{{ op.stance_summary }}</p>
      <blockquote v-if="op.evidence" class="opinion-evidence">
        "{{ op.evidence }}"
      </blockquote>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  opinions: Array<{
    id: number
    stance_summary: string
    category: string
    confidence: number | null
    evidence: string | null
  }>
  loading: boolean
}>()

function categoryLabel(cat: string) {
  const map: Record<string, string> = {
    consensus: '共识',
    disagreement: '分歧',
    neutral: '中立',
  }
  return map[cat] || cat
}

function categoryTagType(cat: string): 'success' | 'danger' | 'info' {
  if (cat === 'consensus') return 'success'
  if (cat === 'disagreement') return 'danger'
  return 'info'
}
</script>

<style scoped>
.opinion-panel {
  height: 100%;
  overflow-y: auto;
  padding: var(--card-padding);
}

.panel-title {
  margin: 0 0 12px;
  font-size: var(--font-size-title);
}

.loading, .empty {
  color: var(--color-text-secondary);
  font-size: var(--font-size-small);
  padding: 24px 0;
  text-align: center;
}

.opinion-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  border-left: 3px solid transparent;
  background: rgba(255, 255, 255, 0.04);
}

.category-consensus {
  border-left-color: var(--color-consensus);
  background: rgba(16, 185, 129, 0.06);
}

.category-disagreement {
  border-left-color: var(--color-disagreement);
  background: rgba(239, 68, 68, 0.06);
}

.category-neutral {
  border-left-color: var(--color-neutral);
  background: rgba(107, 114, 128, 0.06);
}

.opinion-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.confidence {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.opinion-summary {
  margin: 0 0 8px;
  font-size: var(--font-size-body);
  line-height: 1.5;
}

.opinion-evidence {
  margin: 0;
  padding: 6px 10px;
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
  border-left: 2px solid rgba(255, 255, 255, 0.1);
  font-style: italic;
}
</style>
```

- [ ] **Step 2: 验证组件编译**

```bash
cd src/frontend && npx vue-tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add src/frontend/src/components/OpinionPanel.vue
git commit -m "[DDD-观点面板] OpinionPanel共识/分歧/中立三色标签+置信度"
```

---

### Task 14: 演播厅核心页 — StudioPage

**Files:**
- Create: `src/frontend/src/views/StudioPage.vue`

**Interfaces:**
- Consumes: `useDiscussionStore` (Task 9), `GuestCard` (Task 12), `ChatMessage` (Task 12), `OpinionPanel` (Task 13)
- Produces: 2×2 Grid 四分区演播厅

**Dependencies:** Task 9, 12, 13

- [ ] **Step 1: 创建 StudioPage.vue**

```vue
<template>
  <div class="studio-page">
    <!-- 顶部栏 -->
    <header class="studio-topbar">
      <el-button text @click="$router.push('/')">
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <h2 class="studio-topic">{{ store.currentDiscussion?.topic }}</h2>
      <div class="studio-actions">
        <el-button
          v-if="status === 'pending'"
          type="primary"
          @click="sendAction('start')"
        >
          开始讨论
        </el-button>
        <el-button
          v-if="status === 'active'"
          @click="sendAction('pause')"
        >
          暂停
        </el-button>
        <el-button
          v-if="status === 'paused'"
          type="success"
          @click="sendAction('resume')"
        >
          恢复
        </el-button>
        <el-button
          v-if="status === 'active' || status === 'paused'"
          type="danger"
          @click="sendAction('stop')"
        >
          结束
        </el-button>
      </div>
    </header>

    <!-- 2×2 Grid 四分区 -->
    <div class="studio-grid">
      <!-- 左上：圆桌参会面板 -->
      <section class="grid-panel panel-guests">
        <h4 class="panel-title">🎙️ 参会嘉宾</h4>
        <div class="panel-scroll">
          <GuestCard
            v-for="(g, idx) in guests"
            :key="g.id"
            :guest="g"
            :is-active="true"
            :is-speaking="speakingGuestId === g.id"
            :color-theme="guestColors[idx % guestColors.length]"
          />
        </div>
      </section>

      <!-- 右上：主题 & 议题面板 -->
      <section class="grid-panel panel-topics">
        <h4 class="panel-title">📋 讨论议题</h4>
        <div class="panel-scroll">
          <div class="topic-item current">
            <el-tag type="primary" size="small">当前</el-tag>
            <span>{{ store.currentDiscussion?.topic }}</span>
          </div>
          <div class="topic-item">
            <el-tag size="small">轮次 {{ round }}/{{ store.currentDiscussion?.max_rounds }}</el-tag>
          </div>
          <el-empty v-if="!store.currentDiscussion" description="加载中..." :image-size="60" />
        </div>
      </section>

      <!-- 左下：实时对话流 -->
      <section class="grid-panel panel-chat">
        <h4 class="panel-title">💬 讨论记录</h4>
        <div class="panel-scroll" ref="chatScrollRef">
          <ChatMessage
            v-for="msg in store.messages"
            :key="msg.id"
            :message="{
              id: msg.id,
              role: msg.role,
              content: msg.content,
              sender_name: msg.role === 'host' ? '主持人' : ('嘉宾#' + msg.guest_id),
              seq_num: msg.seq_num,
              token_count: msg.token_count,
            }"
            :sender-color="msg.role === 'host' ? '#f0b90b' : '#3b82f6'"
            :is-streaming="false"
          />
          <el-empty v-if="store.messages.length === 0" description="暂无消息" :image-size="60" />
        </div>
      </section>

      <!-- 右下：观点面板 -->
      <section class="grid-panel panel-opinions">
        <h4 class="panel-title">🔍 观点共识 & 分歧</h4>
        <OpinionPanel :opinions="store.opinions" :loading="false" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useDiscussionStore } from '@/stores/discussion'
import GuestCard from '@/components/GuestCard.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import OpinionPanel from '@/components/OpinionPanel.vue'

const route = useRoute()
const router = useRouter()
const store = useDiscussionStore()

const status = ref('pending')
const round = ref(0)
const speakingGuestId = ref<number | null>(null)
const chatScrollRef = ref<HTMLElement | null>(null)
let ws: WebSocket | null = null

const guestColors = [
  '#3b82f6', // blue
  '#10b981', // green
  '#a855f7', // purple
  '#f97316', // orange
  '#ec4899', // pink
  '#06b6d4', // cyan
]

const guests = computed(() => {
  const d = store.currentDiscussion
  if (!d || !('guests' in d)) return []
  return (d as any).guests || []
})

function sendAction(action: string) {
  ws?.send(JSON.stringify({ action }))
}

function connectWS() {
  const discussionId = route.params.discussionId
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${location.host}/ws/discussion/${discussionId}`)

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    switch (data.event) {
      case 'host_speak':
      case 'guest_speak':
        store.messages.push({
          id: Date.now(),
          role: data.event === 'host_speak' ? 'host' : 'guest',
          content: data.content,
          guest_id: data.guest_id,
          seq_num: data.seq_num,
          token_count: 0,
        })
        speakingGuestId.value = data.guest_id || null
        nextTick(() => {
          if (chatScrollRef.value) {
            chatScrollRef.value.scrollTop = chatScrollRef.value.scrollHeight
          }
        })
        break
      case 'speak_done':
        speakingGuestId.value = null
        break
      case 'opinion_extracted':
        store.opinions.push(data)
        break
      case 'round_change':
        round.value = data.round
        break
      case 'discussion_end':
        status.value = 'completed'
        break
      case 'system':
        if (data.message?.includes('已开始')) status.value = 'active'
        if (data.message?.includes('已暂停')) status.value = 'paused'
        if (data.message?.includes('已恢复')) status.value = 'active'
        if (data.message?.includes('已结束')) status.value = 'completed'
        break
    }
  }
}

onMounted(async () => {
  const id = Number(route.params.discussionId)
  await store.loadDiscussion(id)
  await store.fetchDiscussions() // 获取讨论内消息
  connectWS()
})

onUnmounted(() => {
  ws?.close()
})
</script>

<style scoped>
.studio-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
}

.studio-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.15);
  background: var(--color-bg-secondary);
  flex-shrink: 0;
}

.studio-topic {
  flex: 1;
  margin: 0;
  font-size: 18px;
  color: var(--color-accent-cyan);
}

.studio-actions {
  display: flex;
  gap: 8px;
}

.studio-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr;
  grid-template-rows: 1fr 1fr;
  gap: var(--grid-gap);
  background: var(--grid-divider);
  overflow: hidden;
}

@media (max-width: 1439px) {
  .studio-grid {
    grid-template-columns: 250px 1fr;
  }
}

@media (max-width: 767px) {
  .studio-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    overflow-y: auto;
  }
}

.grid-panel {
  background: var(--color-bg-primary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-title {
  margin: 0;
  padding: 12px var(--card-padding);
  font-size: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.panel-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.panel-guests .panel-scroll {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.topic-item {
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  gap: 8px;
}

.topic-item.current {
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.2);
}
</style>
```

- [ ] **Step 2: 验证编译**

```bash
cd src/frontend && npx vue-tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add src/frontend/src/views/StudioPage.vue
git commit -m "[DDD-演播厅] 2x2 Grid四分区 StudioPage+WS连接+三子组件集成"
```

---

## 任务执行顺序

```
Task 1 (依赖)  →  Task 2 (配置)  →  Task 3 (DeepSeek)  →  Task 4 (DB)
                                                                    ↓
                                              Task 5 (API-嘉宾)  →  Task 6 (API-讨论)  →  Task 7 (入口+WS+服务)
                                                                    ↓
                                              Task 8 (UI设计规范, 需调用UI UX Pro Max)
                                                                    ↓
                                              Task 9 (前端脚手架)
                                                                    ↓
                                              Task 10 (首页)
                                                                    ↓
                                              Task 11 (配置页)
                                                                    ↓
                                              Task 12 (组件 GuestCard + ChatMessage)
                                                                    ↓
                                              Task 13 (组件 OpinionPanel)
                                                                    ↓
                                              Task 14 (演播厅 StudioPage)
```

---

## 提交记录汇总（14 commits）

| # | 提交信息 |
|---|---------|
| 1 | `[DDD-依赖] FastAPI+SQLAlchemy+httpx依赖配置` |
| 2 | `[DDD-配置] pydantic-settings配置+env读取` |
| 3 | `[DDD-DeepSeek] 全功能SDK: 同步/流式/重试/限速/JSON解析` |
| 4 | `[DDD-数据库] SQLAlchemy ORM 6实体+异步引擎+init_db` |
| 5 | `[DDD-API-嘉宾] Guest CRUD路由+Pydantic Schema` |
| 6 | `[DDD-API-讨论] Discussion CRUD+嘉宾关联+消息/观点查询` |
| 7 | `[DDD-入口] FastAPI主入口+WebSocket框架+服务层空桩` |
| 8 | `[DDD-设计规范] UI UX Pro Max 生成科技风演播厅设计系统+CSS变量` |
| 9 | `[DDD-前端脚手架] Vite+Vue3+Router+Pinia+ElementPlus工程搭建` |
| 10 | `[DDD-首页] 讨论列表页: 卡片列表+状态标签+新建入口` |
| 11 | `[DDD-配置页] 嘉宾配置: 议题输入+主持人+嘉宾选择+预览` |
| 12 | `[DDD-组件] GuestCard发言动画+ChatMessage消息卡片` |
| 13 | `[DDD-观点面板] OpinionPanel共识/分歧/中立三色标签+置信度` |
| 14 | `[DDD-演播厅] 2x2 Grid四分区 StudioPage+WS连接+三子组件集成` |
