"""
AI功能API路由
包括生成智能总结和AI顾问问答
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.services.ai_service import AIService


router = APIRouter(prefix="/api/ai", tags=["AI"])
ai_service = AIService()


# Pydantic 模型定义
class AdvisorRequest(BaseModel):
    """AI顾问问答请求模型"""
    contract_id: str = Field(..., description="合同ID")
    question: str = Field(..., min_length=1, max_length=500, description="问题")


@router.post("/summary/{contract_id}")
async def generate_summary(
    contract_id: str,
    request: Request,
    force_regenerate: bool = Query(False, description="是否强制重新生成(忽略缓存)"),
    db: AsyncSession = Depends(get_db)
):
    """
    生成AI智能总结
    
    智能行为:
    1. 首先检查是否有缓存的总结
    2. 如果有缓存且未过期,直接返回缓存的总结
    3. 如果没有缓存或强制重新生成,触发异步任务并返回任务ID
    
    Args:
        contract_id: 合同ID
        request: FastAPI请求对象
        force_regenerate: 是否强制重新生成(忽略缓存)
        db: 数据库会话
        
    Returns:
        有缓存: 直接返回AI智能总结
        无缓存: 返回任务ID和状态查询URL
    """
    try:
        # 验证认证
        get_current_user(request)
        
        # 1. 检查缓存(除非强制重新生成)
        if not force_regenerate:
            from app.core.redis_client import redis_client
            from sqlalchemy import select
            from app.models.ai_summary import AISummary
            
            cache_key = f"ai:summary:{contract_id}"
            cached = await redis_client.get(cache_key)
            
            if cached:
                # 从数据库获取完整总结
                query = select(AISummary).where(AISummary.contract_id == contract_id)
                result = await db.execute(query)
                summary = result.scalar_one_or_none()
                
                if summary:
                    # 格式化响应
                    summary_data = {
                        "approval_status": summary.approval_status,
                        "completed_count": summary.completed_count,
                        "total_count": summary.total_count,
                        "review_count": summary.review_count,
                        "key_issues": summary.key_issues,
                        "updated_at": summary.updated_at.isoformat()
                    }
                    
                    return {
                        "success": True,
                        "data": {
                            "summary": summary_data,
                            "cached": True
                        }
                    }
        
        # 2. 没有缓存或强制重新生成: 创建异步任务
        from app.tasks.ai_tasks import generate_ai_summary_task
        
        try:
            task = generate_ai_summary_task.apply_async(
                args=[contract_id],
                retry=True
            )
            
            return {
                "success": True,
                "data": {
                    "task_id": task.id,
                    "status": "PENDING",
                    "message": "AI总结生成任务已创建",
                    "status_url": f"/api/ai/summary/task/{task.id}"
                }
            }
        except Exception as task_error:
            # Celery 不可用时的降级处理: 同步生成
            print(f"[WARNING] Celery unavailable, falling back to sync generation: {str(task_error)}")
            
            summary = await ai_service.generate_summary(contract_id, db)
            
            if not summary:
                # 降级处理:返回友好提示
                return {
                    "success": True,
                    "data": {
                        "summary": None,
                        "message": "AI服务暂时不可用,请稍后重试"
                    }
                }
            
            # 格式化响应
            summary_data = {
                "approval_status": summary.approval_status,
                "completed_count": summary.completed_count,
                "total_count": summary.total_count,
                "review_count": summary.review_count,
                "key_issues": summary.key_issues,
                "updated_at": summary.updated_at.isoformat()
            }
            
            return {
                "success": True,
                "data": {
                    "summary": summary_data,
                    "fallback": True,
                    "message": "任务队列不可用,已同步生成总结"
                }
            }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        # 降级处理
        return {
            "success": True,
            "data": {
                "summary": None,
                "message": f"AI服务暂时不可用: {str(e)}"
            }
        }


@router.post("/advisor")
async def ai_advisor(
    request: Request,
    data: AdvisorRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    AI合同顾问问答
    
    Args:
        request: FastAPI请求对象
        data: 问答请求数据
        db: 数据库会话
        
    Returns:
        AI回答
    """
    try:
        # 验证认证并获取当前用户
        current_user = get_current_user(request)
        current_user_id = current_user.get("user_id")
        
        # 获取答案
        answer = await ai_service.answer_question(
            contract_id=data.contract_id,
            question=data.question,
            current_user_id=current_user_id,
            db=db
        )
        
        return {
            "success": True,
            "data": {
                "answer": answer
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        # 降级处理
        return {
            "success": True,
            "data": {
                "answer": "抱歉,AI服务暂时不可用,请稍后重试"
            }
        }


@router.get("/summary/{contract_id}")
async def get_summary(
    contract_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    获取已生成的AI智能总结
    
    Args:
        contract_id: 合同ID
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        AI智能总结
    """
    try:
        # 验证认证
        get_current_user(request)
        
        # 从数据库获取总结
        from sqlalchemy import select
        from app.models.ai_summary import AISummary
        
        query = select(AISummary).where(AISummary.contract_id == contract_id)
        result = await db.execute(query)
        summary = result.scalar_one_or_none()
        
        if not summary:
            return {
                "success": True,
                "data": {
                    "summary": None
                }
            }
        
        # 格式化响应
        summary_data = {
            "approval_status": summary.approval_status,
            "completed_count": summary.completed_count,
            "total_count": summary.total_count,
            "review_count": summary.review_count,
            "key_issues": summary.key_issues,
            "updated_at": summary.updated_at.isoformat()
        }
        
        return {
            "success": True,
            "data": {
                "summary": summary_data
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取AI总结失败: {str(e)}"
        )


@router.get("/summary/task/{task_id}")
async def get_task_status(
    task_id: str,
    request: Request
):
    """
    获取异步任务状态
    
    Args:
        task_id: Celery 任务ID
        request: FastAPI请求对象
        
    Returns:
        任务状态和结果
    """
    try:
        # 验证认证
        get_current_user(request)
        
        # 获取任务结果
        from celery.result import AsyncResult
        from app.celery_app import celery_app
        
        task_result = AsyncResult(task_id, app=celery_app)
        
        # 构建响应
        response = {
            "task_id": task_id,
            "status": task_result.state,
        }
        
        if task_result.state == 'PENDING':
            response["message"] = "任务正在等待执行"
        elif task_result.state == 'STARTED':
            response["message"] = "任务正在执行中"
        elif task_result.state == 'RETRY':
            response["message"] = "任务执行失败,正在重试"
            if task_result.info:
                response["retry_count"] = task_result.info.get('retry_count', 0)
                response["error"] = task_result.info.get('error')
        elif task_result.state == 'SUCCESS':
            response["message"] = "任务执行成功"
            response["result"] = task_result.result
        elif task_result.state == 'FAILURE':
            response["message"] = "任务执行失败"
            if task_result.info:
                response["error"] = str(task_result.info) if isinstance(task_result.info, Exception) else task_result.info.get('error')
                response["timeout"] = task_result.info.get('timeout', False) if isinstance(task_result.info, dict) else False
                response["max_retries_reached"] = task_result.info.get('max_retries_reached', False) if isinstance(task_result.info, dict) else False
        else:
            response["message"] = f"未知状态: {task_result.state}"
        
        return {
            "success": True,
            "data": response
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取任务状态失败: {str(e)}"
        )
