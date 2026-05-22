"""
钉钉通讯录代理路由
- GET /api/dingtalk/users  拉取整个组织成员列表 (用于发起合同时选评审人/抄送人)
"""
import time
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.dingtalk_contact_service import dingtalk_contact_service

router = APIRouter(prefix="/api/dingtalk", tags=["钉钉通讯录"])
logger = logging.getLogger(__name__)


@router.get("/users")
async def list_dingtalk_users(
    refresh: bool = Query(default=False, description="是否强制刷新, 跳过本地缓存"),
    db: AsyncSession = Depends(get_db),
):
    """
    返回组织内全部成员, 字段格式与 /api/users/list 兼容,
    其中 id 是本地 users 表的 UUID (已 upsert), 可直接用于创建合同.
    """
    try:
        users = await dingtalk_contact_service.get_users_for_form(
            db, force_refresh=refresh
        )
        return {
            "success": True,
            "data": {"users": users, "total": len(users)},
        }
    except RuntimeError as e:
        # 配置或钉钉接口业务错误
        raise HTTPException(status_code=502, detail=f"钉钉通讯录获取失败: {e}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"内部错误: {e}")


@router.get("/contacts")
async def list_dingtalk_contacts(
    refresh: bool = Query(default=False, description="是否强制刷新, 跳过本地缓存"),
    db: AsyncSession = Depends(get_db),
):
    """
    返回完整通讯录: 部门树 + 全部成员
    {
        "departments": [{"id": 1, "name": "全公司", "children": [...]}],
        "users": [{"id": uuid, "name": "张三", "dept_ids": [1, 2], ...}]
    }
    用于发起合同时的"钉钉体"选人弹窗 (部门树 + 搜索).
    """
    start = time.time()
    try:
        data = await dingtalk_contact_service.get_contacts_for_form(
            db, force_refresh=refresh
        )
        elapsed = (time.time() - start) * 1000
        logger.info("/api/dingtalk/contacts 耗时 %.1fms, users=%d, refresh=%s",
                    elapsed, len(data.get("users", [])), refresh)
        return {"success": True, "data": data}
    except RuntimeError as e:
        elapsed = (time.time() - start) * 1000
        logger.warning("/api/dingtalk/contacts 失败 耗时 %.1fms: %s", elapsed, e)
        raise HTTPException(status_code=502, detail=f"钉钉通讯录获取失败: {e}")
    except Exception as e:  # noqa: BLE001
        elapsed = (time.time() - start) * 1000
        logger.error("/api/dingtalk/contacts 异常 耗时 %.1fms: %s", elapsed, e)
        raise HTTPException(status_code=500, detail=f"内部错误: {e}")
