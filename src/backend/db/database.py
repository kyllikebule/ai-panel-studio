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
