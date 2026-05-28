"""
合规检查 Celery 异步任务
Compliance check async Celery task
"""
import asyncio
import logging
import uuid
from typing import Optional

from celery import Task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, selectinload

from app.celery_app import celery_app
from app.core.config import settings
from app.core.minio_client import minio_client
from app.models.compliance import (
    ComplianceCheckResult,
    ComplianceCheckStatus,
    ComplianceRule,
    ComplianceRuleSet,
)
from app.services.ai_service import AIService, ComplianceAIError, ComplianceAIInvalidResponseError
from app.services.text_extractor import TextExtractor, TextExtractionError

logger = logging.getLogger(__name__)

# Celery worker 独立的数据库连接（不复用 FastAPI 的 get_db）
# 注意：不在模块级别创建 engine，避免 asyncio event loop 冲突
# 每次任务执行时通过 _get_db_session() 按需创建


def _make_session_factory():
    """每次调用创建新的 engine + sessionmaker，避免跨 event loop 的连接池冲突。"""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=5,
    )
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class AsyncTask(Task):
    """支持 async def task 的基类（复用 ai_tasks.py 的模式）"""
    def __call__(self, *args, **kwargs):
        result = self.run(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result


@celery_app.task(
    base=AsyncTask,
    bind=True,
    name="app.tasks.compliance_tasks.run_compliance_check_task",
    max_retries=0,          # AI 检查不自动重试，失败直接标 failed
    soft_time_limit=300,    # 5 分钟软超时
    time_limit=360,         # 6 分钟硬超时
    acks_late=True,
    reject_on_worker_lost=True,
)
async def run_compliance_check_task(self, check_id: str) -> None:
    """
    异步执行合规检查：文本抽取 + AI 调用 + 写回结果。

    路由层已完成：频控、校验、MinIO 上传、插入 pending 记录。
    本 task 负责：从 MinIO 拉文件 → 文本抽取 → 查规则 → 调 AI → 写回 DB。

    失败时将 check_result.status 置为 FAILED 并记录 error_message，不抛异常。
    """
    logger.info(f"[compliance_task] start check_id={check_id}")

    async with _make_session_factory()() as db:
        # ── 1. 读取 pending 记录 ──────────────────────────────────────────────
        result = await db.execute(
            select(ComplianceCheckResult).where(
                ComplianceCheckResult.id == uuid.UUID(check_id)
            )
        )
        check = result.scalar_one_or_none()
        if check is None:
            logger.error(f"[compliance_task] check_id={check_id} not found in DB")
            return

        # ── 2. 从 MinIO 拉取文件 ─────────────────────────────────────────────
        # Celery worker 是独立进程，minio_client 需要在使用前确保已连接
        if minio_client.client is None:
            minio_client.connect()

        file_data = minio_client.get_file(check.file_storage_key)
        if file_data is None:
            logger.error(f"[compliance_task] file not found in MinIO: {check.file_storage_key}")
            check.status = ComplianceCheckStatus.FAILED
            check.error_message = "file_extraction_failed"
            await db.commit()
            return

        # ── 3. 文本抽取 ───────────────────────────────────────────────────────
        extractor = TextExtractor()
        try:
            extracted_text, text_truncated = await asyncio.to_thread(
                extractor.extract,
                file_data=file_data,
                mime_type=check.file_mime_type,
            )
        except TextExtractionError as e:
            logger.error(f"[compliance_task] text extraction failed: {e}")
            check.status = ComplianceCheckStatus.FAILED
            check.error_message = "file_extraction_failed"
            await db.commit()
            return

        if not extracted_text.strip():
            logger.warning(f"[compliance_task] empty extracted text for check_id={check_id}")
            check.status = ComplianceCheckStatus.FAILED
            check.error_message = "empty_extracted_text"
            await db.commit()
            return

        check.extracted_text = extracted_text
        check.text_truncated = text_truncated

        # ── 4. 查询规则列表 ───────────────────────────────────────────────────
        rules_result = await db.execute(
            select(ComplianceRule)
            .where(ComplianceRule.rule_set_id == check.rule_set_id)
            .order_by(ComplianceRule.rule_type, ComplianceRule.order, ComplianceRule.created_at)
        )
        rules = list(rules_result.scalars().all())

        # ── 5. 调用 AI ────────────────────────────────────────────────────────
        ai_service = AIService()
        try:
            ai_result = await ai_service.check_compliance(
                rules=rules,
                extracted_text=extracted_text,
                text_truncated=text_truncated,
                number_draft=check.number_draft,
                name_draft=check.name_draft,
                description_draft=check.description_draft,
            )
        except asyncio.TimeoutError:
            logger.error(f"[compliance_task] AI timeout for check_id={check_id}")
            check.status = ComplianceCheckStatus.FAILED
            check.error_message = "ai_timeout"
            await db.commit()
            return
        except ComplianceAIError as e:
            logger.error(f"[compliance_task] AI error for check_id={check_id}: {e}")
            check.status = ComplianceCheckStatus.FAILED
            check.error_message = str(e)
            await db.commit()
            return
        except ComplianceAIInvalidResponseError:
            logger.error(f"[compliance_task] AI invalid response for check_id={check_id}")
            check.status = ComplianceCheckStatus.FAILED
            check.error_message = "ai_invalid_response"
            await db.commit()
            return
        except Exception as e:
            logger.error(f"[compliance_task] unexpected error for check_id={check_id}: {type(e).__name__}: {e}")
            check.status = ComplianceCheckStatus.FAILED
            check.error_message = f"unexpected_error: {type(e).__name__}"
            await db.commit()
            return

        # ── 6. 写回 completed ─────────────────────────────────────────────────
        from datetime import datetime
        check.status = ComplianceCheckStatus.COMPLETED
        check.violations = ai_result["violations"]
        check.suggested_name = ai_result["suggested_name"]
        check.suggested_description = ai_result["suggested_description"]
        check.compliance_score = ai_result["compliance_score"]
        check.completed_at = datetime.utcnow()
        await db.commit()

        logger.info(f"[compliance_task] completed check_id={check_id}, score={check.compliance_score}")
