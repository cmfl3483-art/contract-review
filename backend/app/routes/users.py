"""
用户路由
User routes
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])


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
