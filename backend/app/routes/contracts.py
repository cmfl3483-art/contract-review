"""
合同管理API路由
包括创建合同、获取列表、获取详情等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.models.contract import Contract, ContractStatus
from app.models.review import Review
from app.models.user import User
from app.services.contract_service import ContractService
from app.services.comment_service import CommentService


router = APIRouter(prefix="/api/contracts", tags=["合同"])
contract_service = ContractService()
comment_service = CommentService()


def _serialize_contract(contract: Contract) -> dict:
    """将 Contract ORM 对象序列化为 API 响应字典"""
    status_value = (
        contract.status.value
        if isinstance(contract.status, ContractStatus)
        else str(contract.status)
    )

    initiator = getattr(contract, "initiator", None)
    initiator_data = None
    if initiator is not None:
        initiator_data = {
            "id": str(initiator.id),
            "name": initiator.name,
            "avatar": getattr(initiator, "avatar", None),
        }

    return {
        "id": str(contract.id),
        "name": contract.name,
        "contract_number": contract.contract_number,
        "description": contract.description,
        "status": status_value,
        "initiator": initiator_data,
        "cc_users": list(contract.cc_users or []),
        "version": contract.version,
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
        "updated_at": contract.updated_at.isoformat() if contract.updated_at else None,
    }


# Pydantic 模型定义
class ReviewerInput(BaseModel):
    """评审人输入模型"""
    user_id: str = Field(..., description="用户ID")
    role: str = Field(default="业务", description="角色")
    step: str = Field(default="评审", description="评审步骤")


class CreateContractRequest(BaseModel):
    """创建合同请求模型"""
    name: str = Field(..., min_length=1, max_length=200, description="合同名称")
    contract_number: str = Field(..., min_length=1, max_length=100, description="合同编号")
    description: Optional[str] = Field(None, max_length=2000, description="合同描述")
    reviewers: List[ReviewerInput] = Field(..., min_items=1, description="评审人列表")
    cc_users: Optional[List[str]] = Field(default=[], description="抄送人ID列表")


@router.post("")
async def create_contract(
    request: Request,
    data: CreateContractRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建合同
    
    Args:
        request: FastAPI请求对象
        data: 合同创建数据
        db: 数据库会话
        
    Returns:
        创建的合同ID
    """
    try:
        # 获取当前用户
        current_user = get_current_user(request)
        
        # 验证评审人列表
        if not data.reviewers:
            raise HTTPException(
                status_code=400,
                detail="至少需要一个评审人"
            )
        
        # 转换评审人数据
        reviewers = [
            {
                "user_id": r.user_id,
                "role": r.role,
                "step": r.step
            }
            for r in data.reviewers
        ]
        
        # 创建合同
        contract = await contract_service.create_contract(
            name=data.name,
            contract_number=data.contract_number,
            initiator_id=current_user["user_id"],
            reviewers=reviewers,
            description=data.description,
            cc_users=data.cc_users,
            db=db
        )
        
        return {
            "success": True,
            "data": {
                "contractId": contract.id
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"创建合同失败: {str(e)}"
        )


@router.get("")
async def get_contract_list(
    request: Request,
    filter: str = Query(default="all", description="筛选类型"),
    search: Optional[str] = Query(default=None, description="搜索关键词"),
    page: int = Query(default=1, ge=1, description="页码"),
    limit: int = Query(default=20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取合同列表
    
    Args:
        request: FastAPI请求对象
        filter: 筛选类型 (all/进行中/已完成/待我处理/抄送我/我发起的)
        search: 搜索关键词
        page: 页码
        limit: 每页数量
        db: 数据库会话
        
    Returns:
        合同列表、总数和待办数量
    """
    try:
        # 获取当前用户
        current_user = get_current_user(request)
        
        # 获取合同列表
        result = await contract_service.get_contract_list(
            user_id=current_user["user_id"],
            filter_type=filter,
            search_keyword=search,
            page=page,
            limit=limit,
            db=db
        )
        
        # service 已经返回格式化的数据,直接使用
        return {
            "success": True,
            "data": {
                "contracts": result["contracts"],
                "total": result["total"],
                "page": result["page"],
                "limit": result["limit"],
                "pendingCount": result["pending_count"]
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取合同列表失败: {str(e)}"
        )


@router.get("/{contract_id}")
async def get_contract_detail(
    contract_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    获取合同详情
    
    Args:
        contract_id: 合同ID
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        合同详细信息
    """
    try:
        # 获取当前用户(验证认证)
        get_current_user(request)
        
        # 获取合同详情
        result = await contract_service.get_contract_detail(contract_id, db)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="合同不存在"
            )
        
        contract = result["contract"]
        
        # 格式化响应数据
        contract_data = {
            "id": contract.id,
            "name": contract.name,
            "contract_number": contract.contract_number,
            "description": contract.description,
            "status": contract.status,
            "initiator": {
                "id": contract.initiator.id,
                "name": contract.initiator.name,
                "avatar": contract.initiator.avatar
            },
            "cc_users": contract.cc_users,
            "created_at": contract.created_at.isoformat(),
            "updated_at": contract.updated_at.isoformat()
        }
        
        # 格式化附件数据
        attachments_data = [
            {
                "file_name": group["file_name"],
                "version_count": group["version_count"],
                "versions": [
                    {
                        "id": v.id,
                        "version": v.version,
                        "file_size": v.file_size,
                        "mime_type": v.mime_type,
                        "uploader": {
                            "id": v.uploader.id,
                            "name": v.uploader.name
                        },
                        "created_at": v.created_at.isoformat()
                    }
                    for v in group["versions"]
                ]
            }
            for group in result["attachments"]
        ]
        
        # 格式化评审人数据 - 扁平化结构
        reviewers_data = [
            {
                "id": r["id"],
                "userId": str(r["reviewer"]["id"]),
                "name": r["reviewer"]["name"],
                "role": r["reviewer"]["role"],
                "avatar": r["reviewer"]["avatar"],
                "status": r["status"],
                "step": r["step"],
                "updated_at": r["updated_at"].isoformat() if hasattr(r["updated_at"], 'isoformat') else r["updated_at"]
            }
            for r in result["reviewers"]
        ]
        
        return {
            "success": True,
            "data": {
                "contract": contract_data,
                "attachments": attachments_data,
                "reviewers": reviewers_data
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取合同详情失败: {str(e)}"
        )


class ReviseContractRequest(BaseModel):
    """合同修改请求模型 - 仅 Initiator 在 progress 阶段可调用"""
    name: Optional[str] = Field(None, max_length=200, description="新合同名称")
    contract_number: Optional[str] = Field(None, max_length=100, description="新合同编号")
    description: Optional[str] = Field(None, max_length=5000, description="新合同描述")


@router.patch("/{contract_id}")
async def revise_contract(
    contract_id: str,
    request: Request,
    data: ReviseContractRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    合同发起人在 progress 阶段修改 name / description，触发重审流程。

    业务约束（详见需求 1.1 ~ 1.4）：
    - 仅 Initiator 可调用，否则 403
    - status 必须为 progress，否则 409
    - name 去除首尾空白后长度 1-200，description 长度 ≤ 5000，否则 422
    - 实际值变更才会重置 reviews / 写审计日志（由 contract_service 处理）

    Returns:
        { "success": True, "data": { "contract": <serialized> } }
    """
    current_user = get_current_user(request)

    try:
        contract = await contract_service.revise_contract(
            contract_id=contract_id,
            user_id=current_user["user_id"],
            new_name=data.name,
            new_contract_number=data.contract_number,
            new_description=data.description,
            attachment_added=False,
            db=db,
        )

        return {
            "success": True,
            "data": {
                "contract": _serialize_contract(contract),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ROUTE ERROR] revise_contract failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"修改合同失败: {type(e).__name__}: {str(e)}")


@router.get("/{contract_id}/mentionable-users")
async def get_mentionable_users(
    contract_id: str,
    request: Request,
    search: Optional[str] = Query(None, description="按姓名子串过滤(去除首尾空白后长度1-50)"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前合同的可 @ 提及用户列表。

    业务约束（详见需求 2.1 ~ 2.3、2.7 ~ 2.9）：
    - 候选范围 = {Initiator} ∪ {所有 Reviewer} ∪ {所有 CC_User}（按 ID 去重）
    - 仅相关人员可调用，否则 403；合同不存在 404；未认证 401
    - search 去除首尾空白后长度 1-50：按 name 不区分大小写子串匹配；空或未提供则返回全部
    - 结果按 name 升序，最多 100 条
    - 返回字段：id / name / avatar / department

    Returns:
        { "success": True, "data": { "users": [...] } }
    """
    current_user = get_current_user(request)
    user_id = str(current_user["user_id"])

    # 1. 加载合同（带 reviews + reviewer），不存在则 404
    stmt = (
        select(Contract)
        .options(selectinload(Contract.reviews).selectinload(Review.reviewer))
        .where(Contract.id == contract_id)
    )
    contract = (await db.execute(stmt)).scalar_one_or_none()

    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")

    # 2. 收集相关用户 ID（initiator + reviewers + cc_users），按 ID 去重
    related_ids: set[str] = set()
    related_ids.add(str(contract.initiator_id))
    for review in contract.reviews or []:
        related_ids.add(str(review.reviewer_id))
    for cc_id in contract.cc_users or []:
        if cc_id:
            related_ids.add(str(cc_id))

    # 3. 权限：当前用户必须在相关人员集合中
    if user_id not in related_ids:
        raise HTTPException(status_code=403, detail="您不是该合同的相关人员")

    # 4. 批量加载 User 信息
    if related_ids:
        users_stmt = select(User).where(User.id.in_(list(related_ids)))
        users = (await db.execute(users_stmt)).scalars().all()
    else:
        users = []

    # 5. 应用 search 过滤：strip 后长度 1-50 时按 name 不区分大小写子串匹配；
    #    空字符串或未提供则返回完整并集
    search_value = (search or "").strip()
    if 1 <= len(search_value) <= 50:
        lower = search_value.lower()
        users = [u for u in users if lower in (u.name or "").lower()]

    # 6. 按 name 升序排序，截断至最多 100 条
    users = sorted(users, key=lambda u: (u.name or ""))
    users = users[:100]

    return {
        "success": True,
        "data": {
            "users": [
                {
                    "id": str(u.id),
                    "name": u.name,
                    "avatar": u.avatar,
                    "department": u.department,
                }
                for u in users
            ],
        },
    }


class AddCommentRequest(BaseModel):
    """添加评论请求模型"""
    content: str = Field(..., min_length=1, max_length=5000, description="评论内容")
    review_id: Optional[str] = Field(None, description="评审ID(回复评审意见时提供)")
    parent_comment_id: Optional[str] = Field(None, description="父评论ID(嵌套回复时提供)")
    mentioned_user_ids: Optional[List[str]] = Field(default=[], description="被@提及的用户ID列表，最多10个")

    @field_validator("mentioned_user_ids")
    @classmethod
    def validate_mentioned_user_ids(cls, v):
        if v and len(v) > 10:
            raise ValueError("被@提及的用户ID列表最多10个")
        return v or []


@router.post("/{contract_id}/comments")
async def add_comment(
    contract_id: str,
    request: Request,
    data: AddCommentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    添加评论
    
    支持三种场景:
    1. 直接评论合同(不提供review_id和parent_comment_id)
    2. 回复评审意见(提供review_id)
    3. 嵌套回复(提供parent_comment_id)
    
    Args:
        contract_id: 合同ID
        request: FastAPI请求对象
        data: 评论数据
        db: 数据库会话
        
    Returns:
        创建的评论信息
    """
    try:
        # 获取当前用户
        current_user = get_current_user(request)
        
        # 创建评论
        comment = await comment_service.create_comment(
            contract_id=contract_id,
            author_id=current_user["user_id"],
            content=data.content,
            review_id=data.review_id,
            parent_comment_id=data.parent_comment_id,
            mentioned_user_ids=data.mentioned_user_ids,
            db=db
        )
        
        # 格式化响应数据
        comment_data = {
            "id": str(comment.id),
            "contract_id": str(comment.contract_id),
            "review_id": str(comment.review_id) if comment.review_id else None,
            "parent_comment_id": str(comment.parent_comment_id) if comment.parent_comment_id else None,
            "author": {
                "id": str(comment.author.id),
                "name": comment.author.name,
                "avatar": comment.author.avatar
            },
            "content": comment.content,
            "likes": comment.likes,
            "liked_by": comment.liked_by,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat()
        }
        
        return {
            "success": True,
            "data": {
                "comment": comment_data
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"添加评论失败: {str(e)}"
        )
