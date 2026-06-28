"""SQLite 数据库引擎、会话工厂、初始化。"""
import sqlite3
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import settings

# SQLite 使用 aiosqlite 驱动
DATABASE_URL = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _resolve_db_path() -> str:
    """从 DATABASE_URL 解析出实际的文件系统路径。"""
    raw = settings.database_url
    if raw.startswith("sqlite:///./"):
        relative = raw[len("sqlite:///./"):]
        return str(Path(".").resolve() / relative)
    elif raw.startswith("sqlite:///"):
        return raw[len("sqlite:///"):]
    return raw


async def init_db():
    """执行建表脚本并创建默认数据目录。

    使用原生 sqlite3（同步）直接执行 DDL，避免 aiosqlite /
    SQLAlchemy async 引擎对多语句脚本的限制。
    """
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    schema_path = Path(__file__).parent.parent.parent.parent / "schema" / "init_sqlite.sql"
    sql_content = schema_path.read_text(encoding="utf-8")

    db_path = _resolve_db_path()
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(sql_content)
    finally:
        conn.close()
