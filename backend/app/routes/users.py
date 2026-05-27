"""
用户路由
User routes
"""
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.user import User
from app.core.auth_middleware import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
async def search_users(
    request: Request,
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    搜索用户列表（支持 ?search= 模糊匹配）

    Args:
        search: 按用户姓名模糊搜索（可选）
        limit: 返回数量上限，默认 20，最大 100

    Returns:
        用户列表
    """
    # JWT 认证验证
    get_current_user(request)

    # 构建查询
    query = select(User).order_by(User.name)
    if search:
        query = query.where(User.name.ilike(f"%{search}%"))
    query = query.limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "success": True,
        "data": {
            "users": [
                {
                    "id": str(user.id),
                    "name": user.name,
                    "avatar": user.avatar,
                    "department": user.department,
                    "role": user.role,
                }
                for user in users
            ]
        }
    }


@router.get("/list")
async def get_users(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表
    
    Returns:
        用户列表
    """
    # 查询所有用户
    query = select(User).order_by(User.name)
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 返回用户列表
    return {
        "success": True,
        "data": {
            "users": [
                {
                    "id": str(user.id),
                    "name": user.name,
                    "role": user.role,
                    "email": user.email,
                    "mobile": user.mobile,
                    "department": user.department,
                }
                for user in users
            ]
        }
    }
