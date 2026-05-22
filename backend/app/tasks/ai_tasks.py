"""
AI 相关的 Celery 异步任务
AI-related Celery async tasks
"""
import asyncio
from typing import Optional
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.core.config import settings
from app.services.ai_service import AIService


# 创建异步数据库引擎和会话工厂
# 注意: Celery worker 需要独立的数据库连接
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class AsyncTask(Task):
    """
    自定义异步任务基类
    支持异步函数的执行
    """
    def __call__(self, *args, **kwargs):
        """
        执行任务
        如果任务是协程函数,使用 asyncio.run 执行
        """
        result = self.run(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result


@celery_app.task(
    base=AsyncTask,
    bind=True,
    name="app.tasks.ai_tasks.generate_ai_summary_task",
    max_retries=3,  # 最大重试次数
    default_retry_delay=60,  # 重试延迟(秒)
    soft_time_limit=300,  # 软超时限制(5分钟)
    time_limit=360,  # 硬超时限制(6分钟)
    acks_late=True,  # 任务完成后才确认
    reject_on_worker_lost=True,  # worker丢失时拒绝任务
)
async def generate_ai_summary_task(
    self,
    contract_id: str
) -> Optional[dict]:
    """
    异步生成 AI 智能总结任务
    
    Args:
        self: Celery 任务实例
        contract_id: 合同ID
        
    Returns:
        生成的总结数据字典,如果失败返回 None
        
    Raises:
        SoftTimeLimitExceeded: 任务超时
        Exception: 其他异常会触发重试
    """
    async with async_session_factory() as db:
        try:
            # 创建 AI 服务实例
            ai_service = AIService()
            
            # 生成智能总结
            summary = await ai_service.generate_summary(contract_id, db)
            
            if not summary:
                # 如果生成失败,记录日志并返回 None
                self.update_state(
                    state='FAILURE',
                    meta={
                        'contract_id': contract_id,
                        'error': 'Failed to generate summary'
                    }
                )
                return None
            
            # 返回总结数据
            summary_data = {
                "contract_id": str(summary.contract_id),
                "approval_status": summary.approval_status,
                "completed_count": summary.completed_count,
                "total_count": summary.total_count,
                "review_count": summary.review_count,
                "key_issues": summary.key_issues,
                "updated_at": summary.updated_at.isoformat()
            }
            
            # 更新任务状态为成功
            self.update_state(
                state='SUCCESS',
                meta={
                    'contract_id': contract_id,
                    'summary': summary_data
                }
            )
            
            return summary_data
            
        except SoftTimeLimitExceeded:
            # 任务超时处理
            error_msg = f"AI summary generation timed out for contract {contract_id}"
            print(f"[ERROR] {error_msg}")
            
            # 更新任务状态
            self.update_state(
                state='FAILURE',
                meta={
                    'contract_id': contract_id,
                    'error': 'Task timed out',
                    'timeout': True
                }
            )
            
            # 不重试超时任务
            raise
            
        except Exception as exc:
            # 其他异常处理 - 触发重试
            error_msg = f"Error generating AI summary for contract {contract_id}: {str(exc)}"
            print(f"[ERROR] {error_msg}")
            
            # 更新任务状态
            self.update_state(
                state='RETRY',
                meta={
                    'contract_id': contract_id,
                    'error': str(exc),
                    'retry_count': self.request.retries
                }
            )
            
            # 如果还有重试次数,则重试
            if self.request.retries < self.max_retries:
                # 指数退避: 60秒 * 2^重试次数
                retry_delay = self.default_retry_delay * (2 ** self.request.retries)
                
                print(f"[INFO] Retrying in {retry_delay} seconds (attempt {self.request.retries + 1}/{self.max_retries})")
                
                # 抛出重试异常
                raise self.retry(exc=exc, countdown=retry_delay)
            else:
                # 达到最大重试次数,标记为失败
                print(f"[ERROR] Max retries reached for contract {contract_id}")
                
                self.update_state(
                    state='FAILURE',
                    meta={
                        'contract_id': contract_id,
                        'error': str(exc),
                        'max_retries_reached': True
                    }
                )
                
                return None


@celery_app.task(
    name="app.tasks.ai_tasks.cleanup_old_summaries",
    soft_time_limit=600,  # 10分钟
    time_limit=660  # 11分钟
)
def cleanup_old_summaries():
    """
    清理过期的 AI 总结缓存
    定期任务,可以通过 Celery Beat 调度
    
    Returns:
        清理的缓存数量
    """
    from app.core.redis_client import redis_client
    import asyncio
    
    async def _cleanup():
        try:
            # 获取所有 AI 总结缓存键
            pattern = "ai:summary:*"
            keys = []
            
            # 使用 scan 迭代器避免阻塞
            cursor = 0
            while True:
                cursor, batch = await redis_client.redis.scan(
                    cursor,
                    match=pattern,
                    count=100
                )
                keys.extend(batch)
                if cursor == 0:
                    break
            
            # 检查每个键的 TTL
            expired_keys = []
            for key in keys:
                ttl = await redis_client.redis.ttl(key)
                # TTL < 0 表示键已过期或不存在
                if ttl < 0:
                    expired_keys.append(key)
            
            # 删除过期键
            if expired_keys:
                await redis_client.redis.delete(*expired_keys)
            
            print(f"[INFO] Cleaned up {len(expired_keys)} expired AI summary caches")
            return len(expired_keys)
            
        except Exception as e:
            print(f"[ERROR] Failed to cleanup old summaries: {str(e)}")
            return 0
    
    return asyncio.run(_cleanup())
