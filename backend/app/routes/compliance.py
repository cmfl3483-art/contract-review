"""
合规检查路由层
Compliance check API routes - rule sets, rules, and check operations
"""

import io

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.compliance import (
    CreateRuleSetRequest,
    UpdateRuleSetRequest,
)
from app.services.ai_service import AIService
from app.services.compliance_import_service import ComplianceImportService
from app.services.compliance_service import ComplianceService
from app.services.text_extractor import TextExtractor


router = APIRouter(prefix="/api/compliance", tags=["compliance"])

# ──────────────────────────────────────────────────────────────────────────────
# 模块级单例（在 main.py 注册路由后即可使用）
# ──────────────────────────────────────────────────────────────────────────────

_ai_service = AIService()
_text_extractor = TextExtractor()
compliance_service = ComplianceService(
    ai_service=_ai_service,
    text_extractor=_text_extractor,
)
compliance_import_service = ComplianceImportService()


# ──────────────────────────────────────────────────────────────────────────────
# 权限 helpers
# ──────────────────────────────────────────────────────────────────────────────


def require_admin(user) -> None:
    """规则管理写接口的鉴权（R1.8 / R2.7）"""
    role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)
    if role not in ("法务", "运营"):
        raise HTTPException(403, detail="仅法务/运营可维护合规规则")


def require_compliance_user(user) -> None:
    """发起检查接口的鉴权（R3.8）"""
    role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)
    if role not in ("销售", "法务", "运营"):
        raise HTTPException(403, detail="当前角色无权发起合规检查")


def _get_user_id(user) -> str:
    """从 user dict 或 user 对象中获取用户 ID"""
    if isinstance(user, dict):
        return str(user.get("user_id", ""))
    return str(getattr(user, "id", ""))


def _get_user_role(user) -> str:
    """从 user dict 或 user 对象中获取用户角色"""
    if isinstance(user, dict):
        return user.get("role", "")
    return getattr(user, "role", "")


def _serialize_pydantic_errors(e) -> list:
    """将 Pydantic ValidationError 的 errors() 转换为可 JSON 序列化的格式"""
    result = []
    for err in e.errors():
        serializable_err = {}
        for k, v in err.items():
            if k == "ctx":
                # ctx 可能包含 Exception 对象，转换为字符串
                serializable_err[k] = {
                    ck: str(cv) for ck, cv in v.items()
                } if isinstance(v, dict) else str(v)
            else:
                serializable_err[k] = v
        result.append(serializable_err)
    return result


def _serialize_rule_set(rule_set) -> dict:
    """将 ComplianceRuleSet ORM 对象序列化为 API 响应字典"""
    return {
        "id": str(rule_set.id),
        "name": rule_set.name,
        "description": rule_set.description,
        "is_active": rule_set.is_active,
        "rule_count": getattr(rule_set, "rule_count", 0),
        "created_at": rule_set.created_at.isoformat() if rule_set.created_at else None,
        "updated_at": rule_set.updated_at.isoformat() if rule_set.updated_at else None,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 健康检查
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/health", summary="合规模块健康检查")
async def compliance_health():
    """合规检查模块健康检查端点"""
    return {"status": "ok", "module": "compliance"}


# ──────────────────────────────────────────────────────────────────────────────
# R1：规则集合 CRUD
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/rule-sets", summary="创建规则集合")
async def create_rule_set(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的规则集合。仅法务/运营可操作。

    - 422 字段约束错误以 compliance_validation_failed 错误码返回
    - 返回 {"success": True, "data": {...}}
    """
    user = request.state.user
    require_admin(user)

    # 手动解析请求体，以便捕获 Pydantic 验证错误并返回统一错误码
    try:
        body = await request.json()
        data = CreateRuleSetRequest(**body)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "compliance_validation_failed",
                "message": "请求参数验证失败",
                "errors": _serialize_pydantic_errors(e),
            },
        )
    except Exception:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "compliance_validation_failed",
                "message": "请求体格式错误",
            },
        )

    try:
        rule_set = await compliance_service.create_rule_set(
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            created_by=_get_user_id(user),
            db=db,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建规则集合失败: {str(e)}")

    return {"success": True, "data": _serialize_rule_set(rule_set)}


@router.get("/rule-sets", summary="查询规则集合列表")
async def list_rule_sets(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    查询所有规则集合，按 created_at DESC 排序。所有已登录用户可访问。

    - 返回 {"success": True, "data": {"rule_sets": [...]}}
    """
    # 已由 AuthMiddleware 确保登录，无需额外鉴权
    _ = request.state.user

    try:
        rule_sets = await compliance_service.list_rule_sets(db=db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询规则集合失败: {str(e)}")

    return {
        "success": True,
        "data": {"rule_sets": [_serialize_rule_set(rs) for rs in rule_sets]},
    }


@router.get("/rule-sets/{rule_set_id}", summary="查询规则集合详情")
async def get_rule_set(
    rule_set_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    查询单个规则集合详情，含规则列表。所有已登录用户可访问。

    - 不存在时返回 404
    - 返回 {"success": True, "data": {"rule_set": {...}, "rules": [...]}}
    """
    _ = request.state.user

    try:
        # 获取规则集合列表，找到目标 rule_set
        rule_sets = await compliance_service.list_rule_sets(db=db)
        rule_set = next(
            (rs for rs in rule_sets if str(rs.id) == str(rule_set_id)), None
        )
        if rule_set is None:
            raise HTTPException(status_code=404, detail="规则集合不存在")

        # 获取该集合下的规则列表
        rules = await compliance_service.list_rules(rule_set_id, db=db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询规则集合详情失败: {str(e)}")

    rules_data = [
        {
            "id": str(r.id),
            "rule_set_id": str(r.rule_set_id),
            "rule_type": r.rule_type.value if hasattr(r.rule_type, "value") else r.rule_type,
            "title": r.title,
            "requirement": r.requirement,
            "severity": r.severity.value if hasattr(r.severity, "value") else r.severity,
            "order": r.order,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rules
    ]

    return {
        "success": True,
        "data": {
            "rule_set": _serialize_rule_set(rule_set),
            "rules": rules_data,
        },
    }


@router.put("/rule-sets/{rule_set_id}", summary="更新规则集合")
async def update_rule_set(
    rule_set_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    更新规则集合元数据。仅法务/运营可操作。

    - 422 字段约束错误以 compliance_validation_failed 错误码返回
    - 不存在时返回 404
    - 返回 {"success": True, "data": {...}}
    """
    user = request.state.user
    require_admin(user)

    # 手动解析请求体，以便捕获 Pydantic 验证错误并返回统一错误码
    try:
        body = await request.json()
        data = UpdateRuleSetRequest(**body)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "compliance_validation_failed",
                "message": "请求参数验证失败",
                "errors": _serialize_pydantic_errors(e),
            },
        )
    except Exception:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "compliance_validation_failed",
                "message": "请求体格式错误",
            },
        )

    try:
        rule_set = await compliance_service.update_rule_set(
            rule_set_id,
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            db=db,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新规则集合失败: {str(e)}")

    return {"success": True, "data": _serialize_rule_set(rule_set)}


@router.delete("/rule-sets/{rule_set_id}", summary="删除规则集合", status_code=204)
async def delete_rule_set(
    rule_set_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    删除规则集合。仅法务/运营可操作。

    - 不存在时返回 404
    - 删除生效中的规则集合返回 409 compliance_active_rule_set_in_use
    - 成功返回 HTTP 204 No Content
    """
    user = request.state.user
    require_admin(user)

    try:
        await compliance_service.delete_rule_set(rule_set_id, db=db)
    except HTTPException as e:
        if e.status_code == 409:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "compliance_active_rule_set_in_use",
                    "message": "请先停用该规范集合再删除",
                },
            )
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除规则集合失败: {str(e)}")

    return Response(status_code=204)


# ──────────────────────────────────────────────────────────────────────────────
# R2：规则 CRUD
# ──────────────────────────────────────────────────────────────────────────────


def _serialize_rule(rule) -> dict:
    """将 ComplianceRule ORM 对象序列化为 API 响应字典"""
    return {
        "id": str(rule.id),
        "rule_set_id": str(rule.rule_set_id),
        "rule_type": rule.rule_type.value if hasattr(rule.rule_type, "value") else rule.rule_type,
        "title": rule.title,
        "requirement": rule.requirement,
        "severity": rule.severity.value if hasattr(rule.severity, "value") else rule.severity,
        "order": rule.order,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


@router.post("/rule-sets/{rule_set_id}/rules", summary="新增规则")
async def create_rule(
    rule_set_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    在指定规则集合下新增规则。仅法务/运营可操作。

    - 422 字段约束错误以 compliance_validation_failed 错误码返回
    - 超过 200 条上限返回 409 compliance_rules_quota_exceeded
    - 返回 {"success": True, "data": {"rule": {...}}}
    """
    from app.schemas.compliance import CreateRuleRequest

    user = request.state.user
    require_admin(user)

    try:
        body = await request.json()
        data = CreateRuleRequest(**body)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "compliance_validation_failed",
                "message": "请求参数验证失败",
                "errors": _serialize_pydantic_errors(e),
            },
        )
    except Exception:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "compliance_validation_failed",
                "message": "请求体格式错误",
            },
        )

    try:
        rule = await compliance_service.create_rule(
            rule_set_id,
            rule_type=data.rule_type,
            title=data.title,
            requirement=data.requirement,
            severity=data.severity,
            order=data.order,
            db=db,
        )
    except HTTPException as e:
        if e.status_code == 409:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "compliance_rules_quota_exceeded",
                    "message": "规则数量已达上限（200 条），请先删除不需要的规则",
                },
            )
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"新增规则失败: {str(e)}")

    return {"success": True, "data": {"rule": _serialize_rule(rule)}}


@router.get("/rule-sets/{rule_set_id}/rules", summary="查询规则列表")
async def list_rules(
    rule_set_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    查询指定规则集合下的所有规则，按 rule_type ASC, order ASC, created_at ASC 排序。
    所有已登录用户可访问。

    - 返回 {"success": True, "data": {"rules": [...]}}
    """
    _ = request.state.user

    try:
        rules = await compliance_service.list_rules(rule_set_id, db=db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询规则列表失败: {str(e)}")

    return {
        "success": True,
        "data": {"rules": [_serialize_rule(r) for r in rules]},
    }


@router.put("/rules/{rule_id}", summary="更新规则")
async def update_rule(
    rule_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    更新指定规则。仅法务/运营可操作。

    - 422 字段约束错误以 compliance_validation_failed 错误码返回
    - 不存在时返回 404
    - 返回 {"success": True, "data": {"rule": {...}}}
    """
    from app.schemas.compliance import UpdateRuleRequest

    user = request.state.user
    require_admin(user)

    try:
        body = await request.json()
        data = UpdateRuleRequest(**body)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "compliance_validation_failed",
                "message": "请求参数验证失败",
                "errors": _serialize_pydantic_errors(e),
            },
        )
    except Exception:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "compliance_validation_failed",
                "message": "请求体格式错误",
            },
        )

    try:
        rule = await compliance_service.update_rule(
            rule_id,
            rule_type=data.rule_type,
            title=data.title,
            requirement=data.requirement,
            severity=data.severity,
            order=data.order,
            db=db,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新规则失败: {str(e)}")

    return {"success": True, "data": {"rule": _serialize_rule(rule)}}


@router.delete("/rules/{rule_id}", summary="删除规则", status_code=204)
async def delete_rule(
    rule_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    删除指定规则。仅法务/运营可操作。

    - 不存在时返回 404
    - 成功返回 HTTP 204 No Content
    """
    user = request.state.user
    require_admin(user)

    try:
        await compliance_service.delete_rule(rule_id, db=db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除规则失败: {str(e)}")

    return Response(status_code=204)


# ──────────────────────────────────────────────────────────────────────────────
# R3 + R5：合规检查接口
# ──────────────────────────────────────────────────────────────────────────────


def _serialize_check_result(check_result) -> dict:
    """
    将 ComplianceCheckResult ORM 对象序列化为 API 响应字典。
    不包含 suggested_number 与 contract_text 字段（R5.1）。
    violations 中每项附带 rule_title 和 rule_type（从 rule_set 关联查询补全）。
    """
    # 构建 rule_id -> rule 的映射，用于补全 violations 中的 rule_title / rule_type
    rule_map: dict = {}
    if check_result.rule_set and check_result.rule_set.rules:
        for rule in check_result.rule_set.rules:
            rule_map[str(rule.id)] = rule

    # 序列化 violations，补全 rule_title / rule_type
    violations_data = []
    raw_violations = check_result.violations or []
    for v in raw_violations:
        rule_id = str(v.get("rule_id", ""))
        rule = rule_map.get(rule_id)
        violations_data.append(
            {
                "rule_id": rule_id,
                "rule_title": rule.title if rule else v.get("rule_title", ""),
                "rule_type": (
                    rule.rule_type.value
                    if rule and hasattr(rule.rule_type, "value")
                    else (rule.rule_type if rule else v.get("rule_type", ""))
                ),
                "location": v.get("location", ""),
                "excerpt": v.get("excerpt", ""),
                "description": v.get("description", ""),
                "suggestion": v.get("suggestion", ""),
                "severity": v.get("severity", ""),
            }
        )

    # 序列化 requested_by（User ORM 对象）
    requester = check_result.requester
    requested_by_data = {
        "id": str(requester.id) if requester else None,
        "name": requester.name if requester else None,
        "avatar": requester.avatar if requester else None,
    }

    return {
        "id": str(check_result.id),
        "status": (
            check_result.status.value
            if hasattr(check_result.status, "value")
            else check_result.status
        ),
        "requested_by": requested_by_data,
        "rule_set_id": str(check_result.rule_set_id) if check_result.rule_set_id else None,
        "rule_set_name": (
            check_result.rule_set.name if check_result.rule_set else None
        ),
        "file_name": check_result.file_name,
        "file_size": check_result.file_size,
        "file_mime_type": check_result.file_mime_type,
        "extracted_text": check_result.extracted_text or "",
        "text_truncated": check_result.text_truncated,
        "number_draft": check_result.number_draft,
        "name_draft": check_result.name_draft,
        "description_draft": check_result.description_draft,
        "violations": violations_data,
        "suggested_name": check_result.suggested_name,
        "suggested_description": check_result.suggested_description,
        "compliance_score": check_result.compliance_score,
        "requested_at": (
            check_result.requested_at.isoformat() if check_result.requested_at else None
        ),
        "completed_at": (
            check_result.completed_at.isoformat() if check_result.completed_at else None
        ),
        "error_message": check_result.error_message,
    }


def _serialize_check_result_simple(check_result) -> dict:
    """
    轻量版序列化：用于 create_pending_check 返回，不访问关联对象。
    前端只需要 id 和 status 来跳转详情页。
    """
    return {
        "id": str(check_result.id),
        "status": (
            check_result.status.value
            if hasattr(check_result.status, "value")
            else check_result.status
        ),
        "file_name": check_result.file_name,
        "file_size": check_result.file_size,
        "file_mime_type": check_result.file_mime_type,
        "extracted_text": "",
        "text_truncated": False,
        "number_draft": check_result.number_draft,
        "name_draft": check_result.name_draft,
        "description_draft": check_result.description_draft,
        "violations": [],
        "suggested_name": None,
        "suggested_description": None,
        "compliance_score": None,
        "rule_set_id": str(check_result.rule_set_id) if check_result.rule_set_id else None,
        "rule_set_name": None,
        "requested_by": {"id": None, "name": None, "avatar": None},
        "requested_at": (
            check_result.requested_at.isoformat() if check_result.requested_at else None
        ),
        "completed_at": None,
        "error_message": None,
    }


def _serialize_check_summary(item) -> dict:
    """
    将 ComplianceCheckResult ORM 对象序列化为列表摘要字典。
    不含 extracted_text（R5.2）。
    """
    raw_violations = item.violations or []
    violation_count = len(raw_violations) if item.status == "completed" or (
        hasattr(item.status, "value") and item.status.value == "completed"
    ) else None

    return {
        "id": str(item.id),
        "status": (
            item.status.value if hasattr(item.status, "value") else item.status
        ),
        "name_draft": item.name_draft,
        "rule_set_name": item.rule_set.name if item.rule_set else None,
        "file_name": item.file_name,
        "text_truncated": item.text_truncated,
        "violation_count": violation_count,
        "compliance_score": item.compliance_score,
        "requested_at": (
            item.requested_at.isoformat() if item.requested_at else None
        ),
        "completed_at": (
            item.completed_at.isoformat() if item.completed_at else None
        ),
    }


@router.post("/checks", summary="发起合规检查")
async def perform_compliance_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    发起合规检查（multipart/form-data）。异步模式：立即返回 pending 记录，
    AI 检查由 Celery worker 后台完成，前端轮询状态。

    Form fields:
    - file: UploadFile（必填）
    - number_draft: str（可选）
    - name_draft: str（可选）
    - description_draft: str（可选）
    - rule_set_id: str（必填）

    - 仅销售/法务/运营可操作（R3.8）
    - 返回 {"success": True, "data": {...}}  status=pending
    """
    from fastapi import UploadFile
    from fastapi.datastructures import FormData
    from app.tasks.compliance_tasks import run_compliance_check_task

    user = request.state.user
    require_compliance_user(user)

    # 解析 multipart/form-data
    form: FormData = await request.form()
    file: UploadFile = form.get("file")  # type: ignore[assignment]
    if file is None:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "compliance_validation_failed",
                "message": "缺少必填字段 file",
            },
        )

    number_draft: str | None = form.get("number_draft") or None
    name_draft: str | None = form.get("name_draft") or None
    description_draft: str | None = form.get("description_draft") or None
    rule_set_id: str | None = form.get("rule_set_id") or None

    # 读取文件内容
    file_data: bytes = await file.read()

    try:
        # 步骤 1-5：校验 + MinIO 上传 + 插入 pending 记录，立即返回
        check_result = await compliance_service.create_pending_check(
            file_data=file_data,
            file_name=file.filename or "unknown",
            file_size=len(file_data),
            file_mime_type=file.content_type or "application/octet-stream",
            number_draft=number_draft,
            name_draft=name_draft,
            description_draft=description_draft,
            rule_set_id=rule_set_id,
            user_id=_get_user_id(user),
            db=db,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合规检查提交失败: {str(e)}")

    # 步骤 6-9：投递 Celery task，后台异步执行
    run_compliance_check_task.delay(str(check_result.id))

    # 返回 pending 状态的记录，前端跳转详情页轮询
    return {"success": True, "data": _serialize_check_result_simple(check_result)}


@router.get("/checks", summary="查询合规检查历史列表")
async def list_compliance_checks(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    查询合规检查历史列表。

    Query params:
    - page: int（默认 1）
    - page_size: int（默认 20，上限 100）
    - status: str（可选，pending/completed/failed）

    - 销售仅返回本人记录；法务/运营返回全集（R5.10/5.12）
    - 返回 {"success": True, "data": {"items": [...], "total": ..., "page": ..., "page_size": ...}}
    """
    from datetime import datetime, timedelta
    from sqlalchemy import update as sa_update
    from app.models.compliance import ComplianceCheckResult, ComplianceCheckStatus

    user = request.state.user

    # 自动清理超过 10 分钟还是 pending 的孤儿记录（Celery task 丢失）
    try:
        timeout_threshold = datetime.utcnow() - timedelta(minutes=10)
        await db.execute(
            sa_update(ComplianceCheckResult)
            .where(
                ComplianceCheckResult.status == ComplianceCheckStatus.PENDING,
                ComplianceCheckResult.requested_at < timeout_threshold,
            )
            .values(status=ComplianceCheckStatus.FAILED, error_message="task_lost")
        )
        await db.commit()
    except Exception:
        pass  # 清理失败不影响正常查询

    try:
        result = await compliance_service.list_checks(
            current_user_id=_get_user_id(user),
            current_user_role=_get_user_role(user),
            page=page,
            page_size=page_size,
            status_filter=status,
            db=db,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询合规检查列表失败: {str(e)}")

    items = result.get("items", [])
    return {
        "success": True,
        "data": {
            "items": [_serialize_check_summary(item) for item in items],
            "total": result.get("total", 0),
            "page": result.get("page", page),
            "page_size": result.get("page_size", page_size),
        },
    }


@router.get("/checks/{check_id}", summary="查询单条合规检查结果")
async def get_compliance_check(
    check_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    查询单条合规检查结果。

    - 销售只能查看自己发起的检查（R5.9）
    - 不存在时返回 404
    - 返回 {"success": True, "data": {...}}
    """
    user = request.state.user

    try:
        check_result = await compliance_service.get_check(
            check_id=check_id,
            current_user_id=_get_user_id(user),
            current_user_role=_get_user_role(user),
            db=db,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询合规检查结果失败: {str(e)}")

    return {"success": True, "data": _serialize_check_result(check_result)}


@router.post("/checks/{check_id}/recheck", summary="重新检查")
async def recheck_compliance(
    check_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    对已有合规检查记录重新发起检查（复用原文件与 drafts）。

    - 仅销售/法务/运营可操作（R3.8）
    - 文件已从 MinIO 删除时返回 410
    - 返回 {"success": True, "data": {...}}
    """
    user = request.state.user
    require_compliance_user(user)

    try:
        check_result = await compliance_service.recheck(
            check_id=check_id,
            current_user_id=_get_user_id(user),
            current_user_role=_get_user_role(user),
            db=db,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新检查失败: {str(e)}")

    return {"success": True, "data": _serialize_check_result(check_result)}


# ──────────────────────────────────────────────────────────────────────────────
# Excel 批量导入路由（追加，零侵入既有路由）
# ──────────────────────────────────────────────────────────────────────────────


@router.get(
    "/rule-sets/{rule_set_id}/rules/template",
    summary="下载合规规则 Excel 模板",
)
async def download_rules_template(
    rule_set_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    下载标准 Excel 模板文件。仅法务/运营可操作（R1.4）。
    - rule_set_id 不存在返回 404（R1.6）
    - Content-Disposition 遵循 RFC 5987 编码（约定 #5）
    """
    user = request.state.user
    require_admin(user)
    await compliance_import_service._get_rule_set(rule_set_id, db)
    xlsx_bytes = compliance_import_service.generate_template()
    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename*=UTF-8''compliance_rules_template.xlsx"
        },
    )


@router.post(
    "/rule-sets/{rule_set_id}/rules/import/preview",
    summary="上传 Excel 并获取解析预览",
)
async def import_rules_preview(
    rule_set_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    上传 Excel 文件，解析并返回预览数据（不写入数据库）。仅法务/运营可操作（R2.9）。
    - 返回 { "success": True, "data": { "preview_session_token": ..., "rules": [...], "total_count": ... } }
    """
    user = request.state.user
    require_admin(user)
    form = await request.form()
    file = form.get("file")
    if file is None:
        raise HTTPException(422, detail={
            "code": "import_invalid_file",
            "message": "缺少必填字段 file",
        })
    file_data: bytes = await file.read()
    result = await compliance_import_service.parse_and_preview(
        file_data=file_data,
        file_mime_type=file.content_type or "",
        file_size=len(file_data),
        rule_set_id=rule_set_id,
        db=db,
    )
    return {"success": True, "data": result}


@router.post(
    "/rule-sets/{rule_set_id}/rules/import/confirm",
    summary="确认导入并批量写入规则",
)
async def import_rules_confirm(
    rule_set_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    确认导入，将预览数据批量写入数据库。仅法务/运营可操作（R3.7）。
    - 请求体：{ "preview_session_token": "..." }
    - 返回 { "success": True, "data": { "imported_count": ..., "rule_set_id": ... } }
    """
    user = request.state.user
    require_admin(user)
    body = await request.json()
    token = body.get("preview_session_token")
    if not token:
        raise HTTPException(422, detail={
            "code": "import_preview_expired",
            "message": "缺少必填字段 preview_session_token",
        })
    result = await compliance_import_service.confirm_import(
        rule_set_id=rule_set_id,
        preview_session_token=token,
        db=db,
    )
    return {"success": True, "data": result}
