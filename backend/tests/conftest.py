"""
Pytest configuration and fixtures
"""

import sys
from pathlib import Path
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from uuid import uuid4
import jwt
from datetime import datetime, timedelta

# Add the backend directory to Python path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.models.contract import Contract
from app.models.review import Review, ReviewStatus
from app.models.comment import Comment


# 测试数据库 URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """创建测试数据库会话"""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(db_session):
    """创建异步测试客户端"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """创建测试用户"""
    user = User(
        id=uuid4(),
        dingtalk_user_id=f"test_user_{uuid4()}",
        name="测试用户",
        role="法务",
        email="test@example.com"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_contract(db_session: AsyncSession, test_user: User):
    """创建测试合同"""
    contract = Contract(
        id=uuid4(),
        name="测试合同",
        description="测试合同描述",
        status="progress",
        initiator_id=test_user.id,
        cc_users=[]
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)
    return contract


@pytest_asyncio.fixture
async def test_review(db_session: AsyncSession, test_user: User, test_contract: Contract):
    """创建测试评审记录"""
    review = Review(
        id=uuid4(),
        contract_id=test_contract.id,
        reviewer_id=test_user.id,
        role="法务",
        step="法务初审",
        opinion="测试评审意见",
        status=ReviewStatus.PENDING,
        likes=0,
        liked_by=[]
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    return review


@pytest_asyncio.fixture
async def test_comment(db_session: AsyncSession, test_user: User, test_contract: Contract, test_review: Review):
    """创建测试评论"""
    comment = Comment(
        id=uuid4(),
        contract_id=test_contract.id,
        review_id=test_review.id,
        author_id=test_user.id,
        content="测试评论内容",
        likes=0,
        liked_by=[]
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    return comment


@pytest.fixture
def auth_headers(test_user: User):
    """创建认证请求头"""
    # 生成 JWT Token
    payload = {
        "user_id": str(test_user.id),
        "dingtalk_user_id": test_user.dingtalk_user_id,
        "name": test_user.name,
        "role": test_user.role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    return {
        "Authorization": f"Bearer {token}"
    }
