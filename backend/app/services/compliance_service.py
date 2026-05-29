"""
合规检查服务层
ComplianceService - 业务编排：频控、文件上传、文本抽取、AI 调用、状态机
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.core.redis_client import redis_client
from app.core.minio_client import minio_client
from app.models.compliance import (
    ComplianceCheckResult,
    ComplianceCheckStatus,
    ComplianceRule,
    ComplianceRuleSet,
)
from app.services.text_extractor import TextExtractionError
from app.services.ai_service import ComplianceAIError, ComplianceAIInvalidResponseError

# ──────────────────────────────────────────────────────────────────────────────
# 模块级常量
# ──────────────────────────────────────────────────────────────────────────────

COMPLIANCE_FILE_PATH_PREFIX = "compliance"
COMPLIANCE_TEXT_MAX_LENGTH = 100_000
COMPLIANCE_RATE_LIMIT_WINDOW = 60
COMPLIANCE_RATE_LIMIT_QUOTA = 10
COMPLIANCE_AI_TIMEOUT = 300
COMPLIANCE_RULES_PER_SET_LIMIT = 200
COMPLIANCE_FILE_SIZE_LIMIT = 50 * 1024 * 1024
COMPLIANCE_FILE_MIME_WHITELIST = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


# ──────────────────────────────────────────────────────────────────────────────
# ComplianceService
# ──────────────────────────────────────────────────────────────────────────────


class ComplianceService:
    """合规检查业务编排服务"""

    def __init__(self, ai_service, text_extractor):
        """
        Args:
            ai_service: AIService 实例，提供 check_compliance 方法
            text_extractor: TextExtractor 实例，提供 extract 方法
        """
        self.ai = ai_service
        self.extractor = text_extractor

    # ──────────────────────────────────────────────────────────────────────────
    # 内部辅助方法
    # ──────────────────────────────────────────────────────────────────────────

    async def _resolve_active_rule_set(self, db: AsyncSession) -> ComplianceRuleSet | None:
        """
        获取当前生效的规则集合。

        先读 Redis key ``compliance:active-rule-set``；
        缓存 miss 则查询数据库 ``compliance_rule_sets WHERE is_active = true``，
        找到后将规则集合 id 缓存到 Redis（TTL 与 COMPLIANCE_RATE_LIMIT_WINDOW 无关，
        此处使用 5 分钟，写操作时由调用方主动清除）。

        Returns:
            ComplianceRuleSet 实例，或 None（无生效规则集合时）
        """
        _CACHE_KEY = "compliance:active-rule-set"
        _CACHE_TTL = 300  # 5 分钟

        # 1. 尝试从缓存读取 rule_set_id
        cached_id = await redis_client.get(_CACHE_KEY)
        if cached_id:
            # 缓存命中，按 id 查询完整对象
            result = await db.execute(
                select(ComplianceRuleSet).where(
                    ComplianceRuleSet.id == cached_id
                )
            )
            rule_set = result.scalar_one_or_none()
            if rule_set is not None:
                return rule_set
            # 缓存中的 id 已失效（被删除），清除缓存后继续走 DB 查询
            await redis_client.delete(_CACHE_KEY)

        # 2. 缓存 miss，查询数据库
        result = await db.execute(
            select(ComplianceRuleSet).where(ComplianceRuleSet.is_active == True)  # noqa: E712
        )
        rule_set = result.scalar_one_or_none()

        # 3. 找到后写入缓存
        if rule_set is not None:
            await redis_client.set(_CACHE_KEY, str(rule_set.id), ex=_CACHE_TTL)

        return rule_set

    async def _enforce_rate_limit(self, user_id: str) -> None:
        """
        对指定用户执行频率限制检查。

        Redis key: ``compliance:rate-limit:{user_id}``
        策略：INCR 原子操作；首次 INCR（count == 1）后设置 60 秒过期；
        count > 10 时抛出 HTTP 429。

        Args:
            user_id: 当前用户 ID（字符串形式）

        Raises:
            HTTPException(429): 60 秒内请求次数超过 10 次
        """
        key = f"compliance:rate-limit:{user_id}"

        count = await redis_client.incr(key)
        if count is None:
            # Redis 不可用时放行（降级策略，避免阻断正常业务）
            return

        if count == 1:
            # 首次计数，设置过期时间
            await redis_client.expire(key, COMPLIANCE_RATE_LIMIT_WINDOW)

        if count > COMPLIANCE_RATE_LIMIT_QUOTA:
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请 60 秒后再试",
            )

    # ──────────────────────────────────────────────────────────────────────────
    # RuleSet CRUD
    # ──────────────────────────────────────────────────────────────────────────

    async def create_rule_set(
        self,
        *,
        name: str,
        description: Optional[str],
        is_active: bool,
        created_by: Optional[str],
        db: AsyncSession,
    ) -> ComplianceRuleSet:
        """
        创建新的 ComplianceRuleSet 记录。

        允许同时多条 is_active=true，不再自动停用其他记录。
        写操作完成后清除 Redis 缓存 ``compliance:active-rule-set``。

        Returns:
            创建的 ComplianceRuleSet 对象
        """
        rule_set = ComplianceRuleSet(
            name=name,
            description=description,
            is_active=is_active,
            created_by=uuid.UUID(str(created_by)) if created_by else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(rule_set)
        await db.commit()
        await db.refresh(rule_set)

        # 清除 active rule set 缓存
        await redis_client.delete("compliance:active-rule-set")

        return rule_set

    async def list_rule_sets(self, *, db: AsyncSession) -> list[ComplianceRuleSet]:
        """
        查询所有 ComplianceRuleSet，按 created_at DESC 排序。
        每条记录附带 rule_count（关联的 ComplianceRule 数量）。

        Returns:
            ComplianceRuleSet 列表（含 rule_count 属性）
        """
        # 子查询：统计每个 rule_set 的规则数量
        rule_count_subq = (
            select(
                ComplianceRule.rule_set_id,
                func.count(ComplianceRule.id).label("rule_count"),
            )
            .group_by(ComplianceRule.rule_set_id)
            .subquery()
        )

        stmt = (
            select(
                ComplianceRuleSet,
                func.coalesce(rule_count_subq.c.rule_count, 0).label("rule_count"),
            )
            .outerjoin(
                rule_count_subq,
                ComplianceRuleSet.id == rule_count_subq.c.rule_set_id,
            )
            .order_by(ComplianceRuleSet.created_at.desc())
        )

        result = await db.execute(stmt)
        rows = result.all()

        rule_sets = []
        for row in rows:
            rs = row[0]
            rs.rule_count = row[1]  # 动态附加 rule_count 属性
            rule_sets.append(rs)

        return rule_sets

    async def update_rule_set(
        self,
        rule_set_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        db: AsyncSession,
    ) -> ComplianceRuleSet:
        """
        更新 ComplianceRuleSet 记录。

        不存在则抛 HTTPException(404)。
        允许同时多条 is_active=true。但拒绝把最后一条 active 改为 inactive
        （保证至少剩 1 条 active），返回 HTTPException(409)。
        写操作完成后清除 Redis 缓存 ``compliance:active-rule-set``。

        Returns:
            更新后的 ComplianceRuleSet 对象
        """
        result = await db.execute(
            select(ComplianceRuleSet).where(
                ComplianceRuleSet.id == uuid.UUID(str(rule_set_id))
            )
        )
        rule_set = result.scalar_one_or_none()
        if rule_set is None:
            raise HTTPException(status_code=404, detail="规范集合不存在")

        # 校验：把最后一条 active 改为 inactive 时拒绝
        deactivating = is_active is False and rule_set.is_active
        if deactivating:
            count_result = await db.execute(
                select(func.count(ComplianceRuleSet.id)).where(
                    ComplianceRuleSet.is_active == True  # noqa: E712
                )
            )
            active_count = count_result.scalar_one()
            if active_count <= 1:
                raise HTTPException(
                    status_code=409,
                    detail="至少需要保留一条生效的规则集合，无法停用最后一条",
                )

        # 更新提供的字段
        if name is not None:
            rule_set.name = name
        if description is not None:
            rule_set.description = description
        if is_active is not None:
            rule_set.is_active = is_active

        rule_set.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(rule_set)

        # 清除 active rule set 缓存
        await redis_client.delete("compliance:active-rule-set")

        return rule_set

    async def delete_rule_set(self, rule_set_id: str, *, db: AsyncSession) -> None:
        """
        删除 ComplianceRuleSet 记录。

        不存在则抛 HTTPException(404)。
        如果 is_active=True，抛 HTTPException(409)，拒绝删除生效中的规则集合。
        否则删除记录（关联的 ComplianceRule 由 ORM cascade 处理）。
        写操作完成后清除 Redis 缓存 ``compliance:active-rule-set``。
        """
        result = await db.execute(
            select(ComplianceRuleSet).where(
                ComplianceRuleSet.id == uuid.UUID(str(rule_set_id))
            )
        )
        rule_set = result.scalar_one_or_none()
        if rule_set is None:
            raise HTTPException(status_code=404, detail="规范集合不存在")

        if rule_set.is_active:
            raise HTTPException(status_code=409, detail="请先停用该规范集合再删除")

        await db.delete(rule_set)
        await db.commit()

        # 清除 active rule set 缓存
        await redis_client.delete("compliance:active-rule-set")

    # ──────────────────────────────────────────────────────────────────────────
    # Rule CRUD
    # ──────────────────────────────────────────────────────────────────────────

    async def create_rule(
        self,
        rule_set_id: str,
        *,
        rule_type,
        title: str,
        requirement: str,
        severity,
        order: int,
        db: AsyncSession,
    ) -> ComplianceRule:
        """
        在指定规则集合下创建新规则。

        - 规则集合不存在时抛 HTTPException(404)
        - 该集合下规则数量 >= 200 时抛 HTTPException(409)
        - 在同一事务中更新所属 rule_set 的 updated_at
        - commit 后返回创建的对象

        Returns:
            创建的 ComplianceRule 对象
        """
        # 1. 查询 rule_set 是否存在
        result = await db.execute(
            select(ComplianceRuleSet).where(
                ComplianceRuleSet.id == uuid.UUID(str(rule_set_id))
            )
        )
        rule_set = result.scalar_one_or_none()
        if rule_set is None:
            raise HTTPException(status_code=404, detail="规范集合不存在")

        # 2. 检查规则数量上限
        count_result = await db.execute(
            select(func.count(ComplianceRule.id)).where(
                ComplianceRule.rule_set_id == uuid.UUID(str(rule_set_id))
            )
        )
        rule_count = count_result.scalar_one()
        if rule_count >= COMPLIANCE_RULES_PER_SET_LIMIT:
            raise HTTPException(
                status_code=409,
                detail="单个规范集合下最多可包含 200 条规则",
            )

        # 3. 创建规则记录
        rule = ComplianceRule(
            rule_set_id=uuid.UUID(str(rule_set_id)),
            rule_type=rule_type,
            title=title,
            requirement=requirement,
            severity=severity,
            order=order,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(rule)

        # 4. 同一事务中更新所属 rule_set 的 updated_at
        await db.execute(
            update(ComplianceRuleSet)
            .where(ComplianceRuleSet.id == uuid.UUID(str(rule_set_id)))
            .values(updated_at=datetime.utcnow())
        )

        await db.commit()
        await db.refresh(rule)
        return rule

    async def list_rules(
        self,
        rule_set_id: str,
        *,
        db: AsyncSession,
    ) -> list[ComplianceRule]:
        """
        查询指定规则集合下的所有规则。

        - 规则集合不存在时抛 HTTPException(404)
        - 按 rule_type ASC, order ASC, created_at ASC 排序返回

        Returns:
            ComplianceRule 列表
        """
        # 1. 查询 rule_set 是否存在
        result = await db.execute(
            select(ComplianceRuleSet).where(
                ComplianceRuleSet.id == uuid.UUID(str(rule_set_id))
            )
        )
        rule_set = result.scalar_one_or_none()
        if rule_set is None:
            raise HTTPException(status_code=404, detail="规范集合不存在")

        # 2. 查询并排序规则列表
        rules_result = await db.execute(
            select(ComplianceRule)
            .where(ComplianceRule.rule_set_id == uuid.UUID(str(rule_set_id)))
            .order_by(
                ComplianceRule.rule_type,
                ComplianceRule.order,
                ComplianceRule.created_at,
            )
        )
        return list(rules_result.scalars().all())

    async def update_rule(
        self,
        rule_id: str,
        *,
        rule_type=None,
        title: Optional[str] = None,
        requirement: Optional[str] = None,
        severity=None,
        order: Optional[int] = None,
        db: AsyncSession,
    ) -> ComplianceRule:
        """
        更新指定规则的字段。

        - 规则不存在时抛 HTTPException(404)
        - 仅更新提供的非 None 字段
        - 在同一事务中更新所属 rule_set 的 updated_at
        - commit 后返回更新后的对象

        Returns:
            更新后的 ComplianceRule 对象
        """
        # 1. 查询 rule 是否存在
        result = await db.execute(
            select(ComplianceRule).where(
                ComplianceRule.id == uuid.UUID(str(rule_id))
            )
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            raise HTTPException(status_code=404, detail="规则不存在")

        # 2. 更新提供的非 None 字段
        if rule_type is not None:
            rule.rule_type = rule_type
        if title is not None:
            rule.title = title
        if requirement is not None:
            rule.requirement = requirement
        if severity is not None:
            rule.severity = severity
        if order is not None:
            rule.order = order
        rule.updated_at = datetime.utcnow()

        # 3. 同一事务中更新所属 rule_set 的 updated_at
        await db.execute(
            update(ComplianceRuleSet)
            .where(ComplianceRuleSet.id == uuid.UUID(str(rule.rule_set_id)))
            .values(updated_at=datetime.utcnow())
        )

        await db.commit()
        await db.refresh(rule)
        return rule

    async def delete_rule(self, rule_id: str, *, db: AsyncSession) -> None:
        """
        删除指定规则。

        - 规则不存在时抛 HTTPException(404)
        - 记录 rule_set_id 后删除规则
        - 在同一事务中更新所属 rule_set 的 updated_at
        - commit 提交
        """
        # 1. 查询 rule 是否存在
        result = await db.execute(
            select(ComplianceRule).where(
                ComplianceRule.id == uuid.UUID(str(rule_id))
            )
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            raise HTTPException(status_code=404, detail="规则不存在")

        # 2. 记录 rule_set_id
        rule_set_id = rule.rule_set_id

        # 3. 删除规则记录
        await db.delete(rule)

        # 4. 同一事务中更新所属 rule_set 的 updated_at
        await db.execute(
            update(ComplianceRuleSet)
            .where(ComplianceRuleSet.id == uuid.UUID(str(rule_set_id)))
            .values(updated_at=datetime.utcnow())
        )

        await db.commit()

    # ──────────────────────────────────────────────────────────────────────────
    # 合规检查主流程
    # ──────────────────────────────────────────────────────────────────────────

    async def create_pending_check(
        self,
        *,
        user_id: str,
        file_data: bytes,
        file_name: str,
        file_size: int,
        file_mime_type: str,
        number_draft: Optional[str],
        name_draft: Optional[str],
        description_draft: Optional[str],
        rule_set_id: Optional[str],
        db: AsyncSession,
    ) -> ComplianceCheckResult:
        """
        创建 pending 状态的合规检查记录，立即返回（不等待 AI）。

        执行步骤 1-5（零副作用校验 → MinIO 上传 → 插入 pending 记录 → commit）。
        步骤 6-9（文本抽取 + AI + 写回）由 Celery task 异步完成。

        Raises:
            HTTPException(429): 频控超限
            HTTPException(422): 不支持的文件类型 / 文件过大
            HTTPException(404): rule_set_id 不存在
            HTTPException(409): 无生效规则集合
        """
        # ── 步骤 1：频控校验 ──────────────────────────────────────────────────
        await self._enforce_rate_limit(user_id)

        # ── 步骤 2：MIME / 文件大小校验（零副作用区域）────────────────────────
        if file_mime_type not in COMPLIANCE_FILE_MIME_WHITELIST:
            raise HTTPException(status_code=422, detail="不支持的文件类型")

        if file_size > COMPLIANCE_FILE_SIZE_LIMIT:
            raise HTTPException(status_code=422, detail="文件大小超过 50MB 限制")

        # ── 步骤 3：解析 rule_set_id（零副作用区域）──────────────────────────
        # rule_set_id 必填且必须是 active 的
        if rule_set_id is None:
            raise HTTPException(
                status_code=422,
                detail="请选择规则集合",
            )
        result = await db.execute(
            select(ComplianceRuleSet).where(
                ComplianceRuleSet.id == uuid.UUID(str(rule_set_id))
            )
        )
        rule_set = result.scalar_one_or_none()
        if rule_set is None:
            raise HTTPException(status_code=404, detail="规范集合不存在")
        if not rule_set.is_active:
            raise HTTPException(
                status_code=422,
                detail="所选规则集合已停用，请选择当前生效的规则集合",
            )

        # ── 步骤 4：上传文件到 MinIO ──────────────────────────────────────────
        check_id = uuid.uuid4()
        file_storage_key = (
            f"{COMPLIANCE_FILE_PATH_PREFIX}/{user_id}/{check_id}/{file_name}"
        )
        minio_client.upload_file_data(
            object_name=file_storage_key,
            file_data=file_data,
            file_size=file_size,
            content_type=file_mime_type,
        )

        # ── 步骤 5：插入 pending 记录并 commit ───────────────────────────────
        check_result = ComplianceCheckResult(
            id=check_id,
            status=ComplianceCheckStatus.PENDING,
            file_storage_key=file_storage_key,
            file_name=file_name,
            file_size=file_size,
            file_mime_type=file_mime_type,
            number_draft=number_draft,
            name_draft=name_draft,
            description_draft=description_draft,
            rule_set_id=rule_set.id,
            requested_by=uuid.UUID(str(user_id)),
            requested_at=datetime.utcnow(),
            extracted_text="",
            text_truncated=False,
            violations=[],
        )
        db.add(check_result)
        await db.commit()
        await db.refresh(check_result)
        return check_result

    async def perform_check(
        self,
        *,
        user_id: str,
        file_data: bytes,
        file_name: str,
        file_size: int,
        file_mime_type: str,
        number_draft: Optional[str],
        name_draft: Optional[str],
        description_draft: Optional[str],
        rule_set_id: Optional[str],
        db: AsyncSession,
    ) -> ComplianceCheckResult:
        """
        [已废弃，保留供 recheck 内部调用] 同步执行完整合规检查流程。
        新代码请使用 create_pending_check + Celery task。
        """
        # ── 步骤 1：频控校验 ──────────────────────────────────────────────────
        await self._enforce_rate_limit(user_id)

        # ── 步骤 2：MIME / 文件大小校验（零副作用区域）────────────────────────
        if file_mime_type not in COMPLIANCE_FILE_MIME_WHITELIST:
            raise HTTPException(status_code=422, detail="不支持的文件类型")

        if file_size > COMPLIANCE_FILE_SIZE_LIMIT:
            raise HTTPException(status_code=422, detail="文件大小超过 50MB 限制")

        # ── 步骤 3：解析 rule_set_id（零副作用区域）──────────────────────────
        # rule_set_id 必填且必须是 active 的（与 create_pending_check 一致）
        if rule_set_id is None:
            raise HTTPException(
                status_code=422,
                detail="请选择规则集合",
            )
        result = await db.execute(
            select(ComplianceRuleSet).where(
                ComplianceRuleSet.id == uuid.UUID(str(rule_set_id))
            )
        )
        rule_set = result.scalar_one_or_none()
        if rule_set is None:
            raise HTTPException(status_code=404, detail="规范集合不存在")
        if not rule_set.is_active:
            raise HTTPException(
                status_code=422,
                detail="所选规则集合已停用，请选择当前生效的规则集合",
            )

        # ── 步骤 4：上传文件到 MinIO ──────────────────────────────────────────
        check_id = uuid.uuid4()
        file_storage_key = (
            f"{COMPLIANCE_FILE_PATH_PREFIX}/{user_id}/{check_id}/{file_name}"
        )
        minio_client.upload_file_data(
            object_name=file_storage_key,
            file_data=file_data,
            file_size=file_size,
            content_type=file_mime_type,
        )

        # ── 步骤 5：插入 pending 记录 ─────────────────────────────────────────
        check_result = ComplianceCheckResult(
            id=check_id,
            status=ComplianceCheckStatus.PENDING,
            file_storage_key=file_storage_key,
            file_name=file_name,
            file_size=file_size,
            file_mime_type=file_mime_type,
            number_draft=number_draft,
            name_draft=name_draft,
            description_draft=description_draft,
            rule_set_id=rule_set.id,
            requested_by=uuid.UUID(str(user_id)),
            requested_at=datetime.utcnow(),
            extracted_text="",
            text_truncated=False,
            violations=[],
        )
        db.add(check_result)
        await db.flush()  # 获取 id，不 commit

        # ── 步骤 6-9：文本抽取 + AI 调用 + 写回结果 ─────────────────────────
        return await self._run_extraction_and_ai(
            file_data=file_data,
            file_mime_type=file_mime_type,
            number_draft=number_draft,
            name_draft=name_draft,
            description_draft=description_draft,
            rule_set_id=rule_set.id,
            check_result=check_result,
            db=db,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 内部：文本抽取 + AI 调用（供 perform_check 与 recheck 共用）
    # ──────────────────────────────────────────────────────────────────────────

    async def _run_extraction_and_ai(
        self,
        *,
        file_data: bytes,
        file_mime_type: str,
        number_draft: Optional[str],
        name_draft: Optional[str],
        description_draft: Optional[str],
        rule_set_id,
        check_result: ComplianceCheckResult,
        db: AsyncSession,
    ) -> ComplianceCheckResult:
        """
        执行文本抽取 + AI 合规检查，并将结果写回 check_result。

        - 抽取失败 → status=failed, error_message="file_extraction_failed", commit, 抛 422
        - 空文本   → status=failed, error_message="empty_extracted_text",   commit, 抛 422
        - AI 超时  → status=failed, error_message="ai_timeout",             commit, 抛 504
        - AI 错误  → status=failed, error_message=str(e),                   commit, 抛 502
        - AI JSON 解析失败 → status=failed, error_message="ai_invalid_response", commit, 返回 check_result（200）
        - 成功     → status=completed, 写入 violations/suggested_*/compliance_score/completed_at, commit

        Returns:
            更新后的 check_result
        """
        # ── 文本抽取 ──────────────────────────────────────────────────────────
        try:
            extracted_text, text_truncated = await asyncio.to_thread(
                self.extractor.extract,
                file_data=file_data,
                mime_type=file_mime_type,
            )
        except TextExtractionError:
            check_result.status = ComplianceCheckStatus.FAILED
            check_result.error_message = "file_extraction_failed"
            await db.commit()
            raise HTTPException(status_code=422, detail="合同文件解析失败")

        if extracted_text.strip() == "":
            check_result.status = ComplianceCheckStatus.FAILED
            check_result.error_message = "empty_extracted_text"
            await db.commit()
            raise HTTPException(status_code=422, detail="合同文件未抽取到可读文本")

        # 更新抽取结果字段
        check_result.extracted_text = extracted_text
        check_result.text_truncated = text_truncated

        # ── 查询规则列表 ──────────────────────────────────────────────────────
        rules = await self.list_rules(str(rule_set_id), db=db)

        # ── 调用 AI ───────────────────────────────────────────────────────────
        try:
            ai_result = await self.ai.check_compliance(
                rules=rules,
                extracted_text=extracted_text,
                text_truncated=text_truncated,
                number_draft=number_draft,
                name_draft=name_draft,
                description_draft=description_draft,
            )
        except asyncio.TimeoutError:
            check_result.status = ComplianceCheckStatus.FAILED
            check_result.error_message = "ai_timeout"
            await db.commit()
            raise HTTPException(status_code=504, detail="AI 检查超时")
        except ComplianceAIError as e:
            check_result.status = ComplianceCheckStatus.FAILED
            check_result.error_message = str(e)
            await db.commit()
            raise HTTPException(status_code=502, detail="AI 服务错误")
        except ComplianceAIInvalidResponseError:
            check_result.status = ComplianceCheckStatus.FAILED
            check_result.error_message = "ai_invalid_response"
            await db.commit()
            return await self._reload_check_result(check_result.id, db)

        # ── 更新为 completed ──────────────────────────────────────────────────
        check_result.status = ComplianceCheckStatus.COMPLETED
        check_result.violations = ai_result["violations"]
        check_result.suggested_name = ai_result["suggested_name"]
        check_result.suggested_description = ai_result["suggested_description"]
        check_result.compliance_score = ai_result["compliance_score"]
        check_result.completed_at = datetime.utcnow()
        await db.commit()
        return await self._reload_check_result(check_result.id, db)

    # ──────────────────────────────────────────────────────────────────────────
    # 重新检查
    # ──────────────────────────────────────────────────────────────────────────

    async def recheck(
        self,
        check_id: str,
        *,
        current_user_id: str,
        current_user_role: str,
        db: AsyncSession,
    ) -> ComplianceCheckResult:
        """
        对已有检查记录重新执行合规检查。

        - 复用原 file_storage_key 从 MinIO 拉取文件（不重新上传）
        - 复用原 drafts 与 rule_set_id
        - 重置记录状态为 PENDING，清空 AI 输出字段
        - 重新执行文本抽取 + AI 流程

        Raises:
            HTTPException(404): 检查记录不存在
            HTTPException(403): 销售角色无权操作他人记录
            HTTPException(410): MinIO 文件已不可访问
        """
        # ── 查询检查记录 ──────────────────────────────────────────────────────
        result = await db.execute(
            select(ComplianceCheckResult).where(
                ComplianceCheckResult.id == uuid.UUID(str(check_id))
            )
        )
        check_result = result.scalar_one_or_none()
        if check_result is None:
            raise HTTPException(status_code=404, detail="检查记录不存在")

        # ── 权限校验（销售只能操作自己的记录）────────────────────────────────
        if current_user_role == "销售":
            if str(check_result.requested_by) != str(current_user_id):
                raise HTTPException(status_code=403, detail="无权操作该检查记录")

        # ── 从 MinIO 拉取文件 ─────────────────────────────────────────────────
        file_data = minio_client.get_file(check_result.file_storage_key)
        if file_data is None:
            raise HTTPException(
                status_code=410,
                detail="合同文件已不可访问，请重新上传发起新的合规检查",
            )

        # ── 重置记录状态为 PENDING，清空 AI 输出字段 ──────────────────────────
        check_result.status = ComplianceCheckStatus.PENDING
        check_result.violations = []
        check_result.suggested_name = None
        check_result.suggested_description = None
        check_result.compliance_score = None
        check_result.error_message = None
        check_result.completed_at = None
        await db.commit()

        # ── 复用原 drafts 与 rule_set_id，重新执行抽取 + AI ──────────────────
        return await self._run_extraction_and_ai(
            file_data=file_data,
            file_mime_type=check_result.file_mime_type,
            number_draft=check_result.number_draft,
            name_draft=check_result.name_draft,
            description_draft=check_result.description_draft,
            rule_set_id=check_result.rule_set_id,
            check_result=check_result,
            db=db,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 查询单条检查记录
    # ──────────────────────────────────────────────────────────────────────────

    async def _reload_check_result(
        self, check_id, db: AsyncSession
    ) -> ComplianceCheckResult:
        """commit 后重新查询 check_result，eager load rule_set.rules 和 requester。"""
        from app.models.compliance import ComplianceRuleSet, ComplianceRule
        from app.models.user import User
        result = await db.execute(
            select(ComplianceCheckResult)
            .where(ComplianceCheckResult.id == check_id)
            .options(
                selectinload(ComplianceCheckResult.rule_set).selectinload(
                    ComplianceRuleSet.rules
                ),
                selectinload(ComplianceCheckResult.requester),
            )
        )
        return result.scalar_one()

    async def get_check(
        self,
        check_id: str,
        *,
        current_user_id: str,
        current_user_role: str,
        db: AsyncSession,
    ) -> ComplianceCheckResult:
        """
        查询单条合规检查记录。

        - 销售角色只能查看自己发起的记录
        - 法务/运营可查看全部记录

        Raises:
            HTTPException(404): 检查记录不存在
            HTTPException(403): 销售角色无权查看他人记录
        """
        result = await db.execute(
            select(ComplianceCheckResult)
            .where(ComplianceCheckResult.id == uuid.UUID(str(check_id)))
            .options(
                selectinload(ComplianceCheckResult.rule_set).selectinload(
                    ComplianceRuleSet.rules
                ),
                selectinload(ComplianceCheckResult.requester),
            )
        )
        check_result = result.scalar_one_or_none()
        if check_result is None:
            raise HTTPException(status_code=404, detail="检查记录不存在")

        # 销售角色：只能查看自己的记录
        if current_user_role == "销售":
            if str(check_result.requested_by) != str(current_user_id):
                raise HTTPException(status_code=403, detail="无权查看该检查记录")

        return check_result

    # ──────────────────────────────────────────────────────────────────────────
    # 查询检查记录列表
    # ──────────────────────────────────────────────────────────────────────────

    async def list_checks(
        self,
        *,
        current_user_id: str,
        current_user_role: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        db: AsyncSession,
    ) -> dict:
        """
        分页查询合规检查记录列表。

        - 销售角色：仅返回自己发起的记录
        - 法务/运营：返回全部记录
        - 支持 status_filter 过滤（None 时不过滤）
        - 按 requested_at DESC 排序
        - page_size 上限 100

        Returns:
            {
                "items": [...],   # 每条附带 violation_count
                "total": int,
                "page": int,
                "page_size": int,
            }
        """
        # page_size 上限 100
        page_size = min(page_size, 100)
        page = max(page, 1)

        # ── 构建基础查询条件 ──────────────────────────────────────────────────
        conditions = []

        # 销售角色：仅返回自己的记录
        if current_user_role == "销售":
            conditions.append(
                ComplianceCheckResult.requested_by == uuid.UUID(str(current_user_id))
            )

        # status 过滤
        if status_filter is not None:
            conditions.append(ComplianceCheckResult.status == status_filter)

        # ── 查询总数 ──────────────────────────────────────────────────────────
        count_stmt = select(func.count(ComplianceCheckResult.id))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        # ── 分页查询记录 ──────────────────────────────────────────────────────
        offset = (page - 1) * page_size
        items_stmt = (
            select(ComplianceCheckResult)
            .order_by(ComplianceCheckResult.requested_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        if conditions:
            items_stmt = items_stmt.where(*conditions)

        items_result = await db.execute(items_stmt)
        items = list(items_result.scalars().all())

        # ── 附加 violation_count ──────────────────────────────────────────────
        for item in items:
            if item.status == ComplianceCheckStatus.COMPLETED:
                item.violation_count = len(item.violations) if item.violations else 0
            else:
                item.violation_count = None

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
