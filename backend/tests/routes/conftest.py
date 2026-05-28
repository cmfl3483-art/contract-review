"""
Routes 测试专用 conftest.py
覆盖父级 conftest.py 的 db_engine fixture，使用独立的临时文件数据库
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import Base


@pytest_asyncio.fixture
async def db_engine():
    """
    创建独立的 SQLite 测试引擎。
    使用唯一临时文件路径，避免与父级 conftest.py 的 :memory: 数据库冲突。
    先 drop_all 再 create_all 确保干净状态（处理 User 模型的重复索引问题）。
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_url = f"sqlite+aiosqlite:///{tmp.name}"

    engine = create_async_engine(db_url, poolclass=NullPool, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    try:
        os.unlink(tmp.name)
    except OSError:
        pass
