"""
数据库配置和会话管理
Database configuration and session management
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# 创建异步数据库引擎
# 性能优化配置:
# - pool_size: 连接池大小,根据并发需求调整
# - max_overflow: 最大溢出连接数
# - pool_pre_ping: 连接前检查连接是否有效
# - pool_recycle: 连接回收时间(秒),防止连接过期
# - echo_pool: 是否打印连接池日志(调试用)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_size=20,  # 增加连接池大小以支持更高并发
    max_overflow=40,  # 增加溢出连接数
    pool_recycle=3600,  # 1小时回收连接,防止数据库连接超时
    pool_timeout=30,  # 获取连接的超时时间
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建声明式基类
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    用于 FastAPI 依赖注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
