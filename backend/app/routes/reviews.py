"""
评审管理API路由
包括获取评审记录、同意评审、添加评论、点赞等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.services.review_service import ReviewService


router = APIRouter(prefix="/api", tags=["评审"])
review_service = ReviewService()


# Pydantic 模型定义
class ApproveReviewRequest(BaseModel):
    """同意评审请求模型"""
    opinion: str = Field(..., min_length=1, max_length=2000, description="评审意见")


class AddCommentRequest(BaseModel):
    """添加评论请求模型"""
    content: str = Field(..., min_length=1, max_length=2000, description="评论内容")
    review_id: Optional[str] = Field(None, description="评审ID(回复评审意见时提供)")
    parent_comment_id: Optional[str] = Field(None, description="父评论ID(嵌套回复时提供)")


@router.get("/contracts/{contract_id}/reviews")
async def get_contract_reviews(
    contract_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    获取合同的所有评审记录和AI智能总结
    
    Args:
        contract_id: 合同ID
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        评审记录列表和AI智能总结
    """
    try:
        # 验证认证
        get_current_user(request)
        
        # 获取评审记录 + 顶层游离评论 (service 返回已序列化的 dict)
        review_payload = await review_service.get_contract_reviews(contract_id, db)
        raw_reviews = review_payload.get("reviews", [])
        raw_top_comments = review_payload.get("top_level_comments", [])
        
        # reviews: 将服务层的 comments 重命名为前端期望的 replies
        reviews_data = []
        for r in raw_reviews:
            reviews_data.append({
                **r,
                "opinion": r.get("opinion") or "参与了讨论",
                "replies": r.get("comments", []),
            })
        
        # 获取AI智能总结
        ai_summary_data = await review_service.get_ai_summary(contract_id, db)
        
        return {
            "success": True,
            "data": {
                "reviews": reviews_data,
                "topLevelComments": raw_top_comments,
                "aiSummary": ai_summary_data
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取评审记录失败: {str(e)}"
        )


@router.post("/contracts/{contract_id}/reviews/{review_id}/approve")
async def approve_review(
    contract_id: str,
    review_id: str,
    request: Request,
    data: ApproveReviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    同意评审
    
    Args:
        contract_id: 合同ID
        review_id: 评审ID
        request: FastAPI请求对象
        data: 评审意见
        db: 数据库会话
        
    Returns:
        更新后的评审记录
    """
    try:
        # 获取当前用户
        current_user = get_current_user(request)
        
        # 同意评审
        review = await review_service.approve_review(
            review_id=review_id,
            reviewer_id=current_user["user_id"],
            opinion=data.opinion,
            db=db
        )
        
        return {
            "success": True,
            "data": {
                "review": {
                    "id": review.id,
                    "status": review.status,
                    "opinion": review.opinion,
                    "updated_at": review.updated_at.isoformat()
                }
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
            detail=f"同意评审失败: {str(e)}"
        )


@router.post("/contracts/{contract_id}/comments")
async def add_comment(
    contract_id: str,
    request: Request,
    data: AddCommentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    添加评论
    
    Args:
        contract_id: 合同ID
        request: FastAPI请求对象
        data: 评论数据
        db: 数据库会话
        
    Returns:
        创建的评论
    """
    try:
        # 获取当前用户
        current_user = get_current_user(request)
        
        # 添加评论
        comment = await review_service.add_comment(
            contract_id=contract_id,
            author_id=current_user["user_id"],
            content=data.content,
            review_id=data.review_id,
            parent_comment_id=data.parent_comment_id,
            db=db
        )
        
        return {
            "success": True,
            "data": {
                "comment": {
                    "id": comment.id,
                    "content": comment.content,
                    "created_at": comment.created_at.isoformat()
                }
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"添加评论失败: {str(e)}"
        )


@router.post("/reviews/{review_id}/like")
async def like_review(
    review_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    点赞/取消点赞评审意见
    
    Args:
        review_id: 评审ID
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        更新后的点赞数
    """
    try:
        # 获取当前用户
        current_user = get_current_user(request)
        
        # 点赞
        review = await review_service.like_review(
            review_id=review_id,
            user_id=current_user["user_id"],
            db=db
        )
        
        return {
            "success": True,
            "data": {
                "likes": review.likes
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"点赞失败: {str(e)}"
        )


@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    点赞/取消点赞评论
    
    Args:
        comment_id: 评论ID
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        更新后的点赞数
    """
    try:
        # 获取当前用户
        current_user = get_current_user(request)
        
        # 点赞
        comment = await review_service.like_comment(
            comment_id=comment_id,
            user_id=current_user["user_id"],
            db=db
        )
        
        return {
            "success": True,
            "data": {
                "likes": comment.likes
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"点赞失败: {str(e)}"
        )
