"""
通知管理API路由
包括获取通知列表、未读数、标记已读等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.services.notification_service_v2 import notification_service_v2


router = APIRouter(prefix="/api/notifications", tags=["通知"])


@router.get("")
async def get_notifications(
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取通知列表

    Args:
        request: FastAPI请求对象
        page: 页码
        page_size: 每页数量
        db: 数据库会话

    Returns:
        通知列表、总数、页码和每页数量
    """
    try:
        current_user = get_current_user(request)

        result = await notification_service_v2.get_notifications(
            current_user["user_id"], page, page_size, db
        )

        return {
            "success": True,
            "data": {
                "notifications": result["notifications"],
                "total": result["total"],
                "page": result["page"],
                "page_size": result["page_size"],
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取通知列表失败: {str(e)}"
        )


@router.get("/unread-count")
async def get_unread_count(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    获取未读通知数量

    Args:
        request: FastAPI请求对象
        db: 数据库会话

    Returns:
        未读通知数量
    """
    try:
        current_user = get_current_user(request)

        count = await notification_service_v2.get_unread_count(
            current_user["user_id"], db
        )

        return {
            "success": True,
            "data": {
                "count": count
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取未读数失败: {str(e)}"
        )


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    标记单条通知为已读

    Args:
        notification_id: 通知ID
        request: FastAPI请求对象
        db: 数据库会话

    Returns:
        标记结果
    """
    try:
        current_user = get_current_user(request)

        success = await notification_service_v2.mark_as_read(
            notification_id, current_user["user_id"], db
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="通知不存在或无权操作"
            )

        return {
            "success": True,
            "data": {
                "id": notification_id,
                "is_read": True
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"标记已读失败: {str(e)}"
        )


@router.post("/read-all")
async def mark_all_as_read(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    将所有通知标记为已读

    Args:
        request: FastAPI请求对象
        db: 数据库会话

    Returns:
        更新的通知数量
    """
    try:
        current_user = get_current_user(request)

        updated_count = await notification_service_v2.mark_all_as_read(
            current_user["user_id"], db
        )

        return {
            "success": True,
            "data": {
                "updated_count": updated_count
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"全部标记已读失败: {str(e)}"
        )
