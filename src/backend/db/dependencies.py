"""共享 FastAPI 依赖项。"""
from sqlalchemy.ext.asyncio import AsyncSession

from .database import async_session


async def get_db() -> AsyncSession:
    """获取数据库会话的 FastAPI 依赖项。"""
    async with async_session() as session:
        yield session
