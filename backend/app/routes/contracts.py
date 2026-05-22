"""
合同管理API路由
包括创建合同、获取列表、获取详情等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.services.contract_service import ContractService
from app.services.comment_service import CommentService


router = APIRouter(prefix="/api/contracts", tags=["合同"])
contract_service = ContractService()
comment_service = CommentService()


# Pydantic 模型定义
class ReviewerInput(BaseModel):
    """评审人输入模型"""
    user_id: str = Field(..., description="用户ID")
    role: str = Field(default="业务", description="角色")
    step: str = Field(default="评审", description="评审步骤")


class CreateContractRequest(BaseModel):
    """创建合同请求模型"""
    name: str = Field(..., min_length=1, max_length=200, description="合同名称")
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


class AddCommentRequest(BaseModel):
    """添加评论请求模型"""
    content: str = Field(..., min_length=1, max_length=5000, description="评论内容")
    review_id: Optional[str] = Field(None, description="评审ID(回复评审意见时提供)")
    parent_comment_id: Optional[str] = Field(None, description="父评论ID(嵌套回复时提供)")


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
