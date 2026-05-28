# Design Document - 合规规则 Excel 批量导入

## Overview

本设计文档描述「合规规则 Excel 批量导入」功能的技术实现方案，严格对齐 `requirements.md` 中四项 Requirement，在已交付的 `contract-compliance-check` Spec 之上扩展，**零侵入**既有合规检查逻辑。

功能边界：
- **做什么**：管理员下载标准 Excel 模板 → 填写规则 → 上传预览 → 确认批量写入
- **不做什么**：不涉及规则集合批量创建、规则批量导出、合规检查结果导入导出

改动范围总览：

| 层 | 改动 | 策略 |
|---|---|---|
| 后端 | 新增 `services/compliance_import_service.py` | 不污染 `compliance_service.py` |
| 后端 | 在 `routes/compliance.py` 追加 3 个路由 | 追加，不修改已有路由 |
| 后端 | `requirements.txt` 追加 `openpyxl` | openpyxl 已是项目依赖（pdfplumber 间接依赖），显式声明版本 |
| 前端 | `RuleTable.tsx` 追加「下载模板」「批量导入」按钮 | 追加，不修改已有逻辑 |
| 前端 | 新增 `RuleImportModal.tsx` 组件 | 独立文件 |
| 前端 | `useCompliance.ts` 追加 3 个 hooks | 追加，不修改已有 hooks |
| 前端 | `types/compliance.ts` 追加导入相关类型 | 追加 |
| 缓存 | Redis key `compliance:import:preview:{token}` TTL 600s | 新增，不影响已有 key |

---

## Architecture

### 端到端数据流

```
管理员
  │
  ├─ 点击「下载模板」
  │    → GET /api/compliance/rule-sets/{rule_set_id}/rules/template
  │    → ComplianceImportService.generate_template(rule_set_id)
  │    → openpyxl 生成 xlsx → StreamingResponse
  │
  ├─ 填写 Excel 后点击「批量导入」→ 选择文件 → 点击「上传并预览」
  │    → POST /api/compliance/rule-sets/{rule_set_id}/rules/import/preview
  │    → ComplianceImportService.parse_and_preview(file, rule_set_id)
  │         ├─ MIME / 大小校验
  │         ├─ openpyxl 解析（跳过第 1-2 行）
  │         ├─ 逐行字段校验（全量，收集所有错误）
  │         ├─ 空行 / 超 200 条校验
  │         ├─ rule_set 当前规则数 + 本次数量 ≤ 200 校验
  │         └─ 生成 preview_session_token → Redis SET compliance:import:preview:{token} TTL 600s
  │    → 返回 { preview_session_token, rules, total_count }
  │    → 前端展示预览确认弹窗
  │
  └─ 点击「确认导入」
       → POST /api/compliance/rule-sets/{rule_set_id}/rules/import/confirm
       → ComplianceImportService.confirm_import(rule_set_id, preview_session_token)
            ├─ Redis GET compliance:import:preview:{token}（不存在/过期 → 422）
            ├─ 反序列化规则列表
            ├─ 再次校验 rule_set 规则数 + 本次数量 ≤ 200（竞态保护）
            ├─ 单事务批量 INSERT compliance_rules + UPDATE rule_set.updated_at
            ├─ 事务 commit 后 Redis DEL token（一次性令牌）
            └─ 返回 { imported_count, rule_set_id }
       → 前端关闭弹窗，invalidate rules queryKey，展示「成功导入 N 条规则」
```

### 架构决策

| 决策 | 备选方案 | 选择理由 |
|---|---|---|
| 独立 `compliance_import_service.py` | 在 `compliance_service.py` 中追加方法 | 导入逻辑（openpyxl、Redis token 管理）与现有检查逻辑完全正交，独立文件避免 `compliance_service.py` 膨胀，便于单独测试 |
| Preview_Session_Token 存 Redis（TTL 600s） | 存数据库临时表 | Redis 天然支持 TTL 自动过期，无需定时清理任务；token 是一次性短生命周期数据，不需要持久化 |
| 全量校验后再生成 token | 逐行校验边解析边写 Redis | 需要保证「要么全部成功要么全部失败」的语义；全量校验后一次性生成 token，错误信息更完整 |
| 路由追加到 `routes/compliance.py` | 新建 `routes/compliance_import.py` | 3 个路由都在 `/api/compliance/rule-sets/{rule_set_id}/rules/` 前缀下，与现有规则路由同属一个资源域，追加更自然；避免 router 注册分散 |
| openpyxl 显式追加到 `requirements.txt` | 依赖 pdfplumber 间接引入 | 显式声明避免间接依赖版本漂移导致的兼容性问题 |

---

## Components and Interfaces

### 后端组件

#### 1. `services/compliance_import_service.py`（新建）

```python
import io
import json
import secrets
import uuid
from typing import Optional

import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import PatternFill, Font
from fastapi import HTTPException, UploadFile

from app.core.redis_client import redis_client
from app.models.compliance import ComplianceRule, ComplianceRuleSet, RuleType, RuleSeverity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from datetime import datetime

IMPORT_PREVIEW_TTL = 600          # 10 分钟
IMPORT_RULES_LIMIT = 200
IMPORT_FILE_SIZE_LIMIT = 5 * 1024 * 1024   # 5 MB
IMPORT_EXCEL_MIME = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
IMPORT_REDIS_KEY_PREFIX = "compliance:import:preview:"

# 模板列定义（顺序固定）
TEMPLATE_COLUMNS = [
    ("rule_type",    "规则类型",   "枚举：number / name / description / file"),
    ("title",        "规则名称",   "1-100 字符"),
    ("requirement",  "规则正文",   "1-2000 字符"),
    ("severity",     "严重程度",   "枚举：must / should，缺省默认 must"),
    ("order",        "排序",       "整数，缺省默认 0"),
]


class ComplianceImportService:

    # ── 模板生成 ──────────────────────────────────────────────────────────────

    def generate_template(self) -> bytes:
        """
        生成标准 Excel 模板文件（bytes）。
        - 第 1 行：表头行（加粗）
        - 第 2 行：说明行（灰色背景）
        - 第 3 行起：数据区域（含 rule_type / severity 下拉验证）
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "合规规则"

        # 表头行
        for col_idx, (field, label, _) in enumerate(TEMPLATE_COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=label)
            cell.font = Font(bold=True)

        # 说明行（灰色背景）
        gray_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        for col_idx, (_, _, hint) in enumerate(TEMPLATE_COLUMNS, start=1):
            cell = ws.cell(row=2, column=col_idx, value=hint)
            cell.fill = gray_fill

        # 数据验证：rule_type 列（A 列，第 3 行起）
        dv_type = DataValidation(
            type="list",
            formula1='"number,name,description,file"',
            allow_blank=False,
            showDropDown=False,
        )
        ws.add_data_validation(dv_type)
        dv_type.sqref = "A3:A1048576"

        # 数据验证：severity 列（D 列，第 3 行起）
        dv_severity = DataValidation(
            type="list",
            formula1='"must,should"',
            allow_blank=True,
            showDropDown=False,
        )
        ws.add_data_validation(dv_severity)
        dv_severity.sqref = "D3:D1048576"

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    # ── 上传预览 ──────────────────────────────────────────────────────────────

    async def parse_and_preview(
        self,
        *,
        file_data: bytes,
        file_mime_type: str,
        file_size: int,
        rule_set_id: str,
        db: AsyncSession,
    ) -> dict:
        """
        解析 Excel 文件，全量校验，生成预览 token 存入 Redis。

        Returns:
            { "preview_session_token": str, "rules": [...], "total_count": int }

        Raises:
            HTTPException(404): rule_set_id 不存在
            HTTPException(409): 导入后总规则数超过 200 条
            HTTPException(422): 文件类型/大小/内容校验失败
        """
        # 1. 文件类型 / 大小校验
        if file_mime_type != IMPORT_EXCEL_MIME:
            raise HTTPException(422, detail={
                "code": "import_invalid_file",
                "message": "文件类型不合法，请上传 .xlsx 格式文件",
                "field": "file",
            })
        if file_size > IMPORT_FILE_SIZE_LIMIT:
            raise HTTPException(422, detail={
                "code": "import_invalid_file",
                "message": "文件大小超过 5 MB 限制",
                "field": "file",
            })

        # 2. rule_set 存在性校验
        rule_set = await self._get_rule_set(rule_set_id, db)

        # 3. 解析 Excel
        parsed_rows, errors = self._parse_excel(file_data)

        # 4. 空行校验
        if not parsed_rows and not errors:
            raise HTTPException(422, detail={
                "code": "import_empty_file",
                "message": "文件中未包含有效数据行（第三行起为空）",
            })

        # 5. 行级校验错误汇总
        if errors:
            raise HTTPException(422, detail={
                "code": "import_validation_failed",
                "message": f"共 {len(errors)} 行数据校验失败",
                "errors": errors,
            })

        # 6. 超 200 条校验
        if len(parsed_rows) > IMPORT_RULES_LIMIT:
            raise HTTPException(422, detail={
                "code": "import_too_many_rows",
                "message": f"单次导入最多 {IMPORT_RULES_LIMIT} 条规则，本次解析到 {len(parsed_rows)} 条",
            })

        # 7. 与现有规则数量合并校验
        current_count = await self._get_rule_count(rule_set_id, db)
        if current_count + len(parsed_rows) > IMPORT_RULES_LIMIT:
            raise HTTPException(409, detail={
                "code": "import_quota_exceeded",
                "message": (
                    f"导入后总规则数将超过 {IMPORT_RULES_LIMIT} 条上限。"
                    f"当前已有 {current_count} 条，本次导入 {len(parsed_rows)} 条。"
                ),
                "current_count": current_count,
                "import_count": len(parsed_rows),
                "limit": IMPORT_RULES_LIMIT,
            })

        # 8. 生成 token，存入 Redis
        token = secrets.token_urlsafe(32)
        redis_key = f"{IMPORT_REDIS_KEY_PREFIX}{token}"
        await redis_client.set(
            redis_key,
            json.dumps(parsed_rows, ensure_ascii=False),
            ex=IMPORT_PREVIEW_TTL,
        )

        return {
            "preview_session_token": token,
            "rules": parsed_rows,
            "total_count": len(parsed_rows),
        }

    # ── 确认导入 ──────────────────────────────────────────────────────────────

    async def confirm_import(
        self,
        *,
        rule_set_id: str,
        preview_session_token: str,
        db: AsyncSession,
    ) -> dict:
        """
        从 Redis 读取预览数据，在单个事务中批量写入 compliance_rules。

        Returns:
            { "imported_count": int, "rule_set_id": str }

        Raises:
            HTTPException(404): rule_set_id 不存在
            HTTPException(409): 竞态导致总规则数超过 200 条
            HTTPException(422): token 不存在或已过期
            HTTPException(500): 事务执行失败
        """
        # 1. 校验 token
        redis_key = f"{IMPORT_REDIS_KEY_PREFIX}{preview_session_token}"
        raw = await redis_client.get(redis_key)
        if raw is None:
            raise HTTPException(422, detail={
                "code": "import_preview_expired",
                "message": "预览会话已过期，请重新上传 Excel 文件",
            })

        parsed_rows = json.loads(raw)

        # 2. rule_set 存在性校验
        rule_set = await self._get_rule_set(rule_set_id, db)

        # 3. 竞态保护：再次校验规则数量
        current_count = await self._get_rule_count(rule_set_id, db)
        if current_count + len(parsed_rows) > IMPORT_RULES_LIMIT:
            raise HTTPException(409, detail={
                "code": "import_quota_exceeded",
                "message": (
                    f"导入后总规则数将超过 {IMPORT_RULES_LIMIT} 条上限。"
                    f"当前已有 {current_count} 条，本次导入 {len(parsed_rows)} 条。"
                ),
                "current_count": current_count,
                "import_count": len(parsed_rows),
                "limit": IMPORT_RULES_LIMIT,
            })

        # 4. 单事务批量写入
        try:
            now = datetime.utcnow()
            for row in parsed_rows:
                rule = ComplianceRule(
                    rule_set_id=uuid.UUID(str(rule_set_id)),
                    rule_type=RuleType(row["rule_type"]),
                    title=row["title"],
                    requirement=row["requirement"],
                    severity=RuleSeverity(row.get("severity", "must")),
                    order=int(row.get("order", 0)),
                    created_at=now,
                    updated_at=now,
                )
                db.add(rule)

            # 更新 rule_set.updated_at
            await db.execute(
                update(ComplianceRuleSet)
                .where(ComplianceRuleSet.id == uuid.UUID(str(rule_set_id)))
                .values(updated_at=now)
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(500, detail={
                "code": "import_transaction_failed",
                "message": "导入失败，数据未写入，请稍后重试",
            })

        # 5. token 失效（一次性令牌）
        await redis_client.delete(redis_key)

        return {
            "imported_count": len(parsed_rows),
            "rule_set_id": str(rule_set_id),
        }

    # ── 私有辅助方法 ──────────────────────────────────────────────────────────

    def _parse_excel(self, file_data: bytes) -> tuple[list[dict], list[dict]]:
        """
        解析 Excel 文件，跳过第 1-2 行，从第 3 行起逐行读取。
        返回 (parsed_rows, errors)。
        errors 中每项格式：{ "row_number": int, "field": str, "message": str }
        """
        wb = openpyxl.load_workbook(io.BytesIO(file_data), data_only=True)
        ws = wb.active

        parsed_rows = []
        errors = []

        for excel_row_idx, row in enumerate(ws.iter_rows(min_row=3, values_only=True), start=3):
            # 跳过全空行
            if all(cell is None or str(cell).strip() == "" for cell in row):
                continue

            row_errors = []
            rule_type_val = str(row[0]).strip() if row[0] is not None else ""
            title_val = str(row[1]).strip() if row[1] is not None else ""
            requirement_val = str(row[2]).strip() if row[2] is not None else ""
            severity_val = str(row[3]).strip() if row[3] is not None else ""
            order_val = row[4]

            # rule_type 校验
            if rule_type_val not in ("number", "name", "description", "file"):
                row_errors.append({
                    "row_number": excel_row_idx,
                    "field": "rule_type",
                    "message": (
                        f"第 {excel_row_idx} 行：rule_type 取值 '{rule_type_val}' 不合法，"
                        "必须为 number / name / description / file 之一"
                    ),
                })

            # title 校验
            if not (1 <= len(title_val) <= 100):
                row_errors.append({
                    "row_number": excel_row_idx,
                    "field": "title",
                    "message": f"第 {excel_row_idx} 行：title 长度必须为 1-100 字符",
                })

            # requirement 校验
            if not (1 <= len(requirement_val) <= 2000):
                row_errors.append({
                    "row_number": excel_row_idx,
                    "field": "requirement",
                    "message": f"第 {excel_row_idx} 行：requirement 长度必须为 1-2000 字符",
                })

            # severity 校验（缺省默认 must）
            if severity_val == "":
                severity_val = "must"
            elif severity_val not in ("must", "should"):
                row_errors.append({
                    "row_number": excel_row_idx,
                    "field": "severity",
                    "message": (
                        f"第 {excel_row_idx} 行：severity 取值 '{severity_val}' 不合法，"
                        "必须为 must / should 之一"
                    ),
                })

            # order 校验（缺省默认 0）
            if order_val is None or str(order_val).strip() == "":
                order_int = 0
            else:
                try:
                    order_int = int(order_val)
                except (ValueError, TypeError):
                    order_int = None
                    row_errors.append({
                        "row_number": excel_row_idx,
                        "field": "order",
                        "message": f"第 {excel_row_idx} 行：order 必须为整数",
                    })

            if row_errors:
                errors.extend(row_errors)
            else:
                parsed_rows.append({
                    "row_number": excel_row_idx,
                    "rule_type": rule_type_val,
                    "title": title_val,
                    "requirement": requirement_val,
                    "severity": severity_val,
                    "order": order_int,
                })

        return parsed_rows, errors

    async def _get_rule_set(self, rule_set_id: str, db: AsyncSession) -> ComplianceRuleSet:
        result = await db.execute(
            select(ComplianceRuleSet).where(
                ComplianceRuleSet.id == uuid.UUID(str(rule_set_id))
            )
        )
        rule_set = result.scalar_one_or_none()
        if rule_set is None:
            raise HTTPException(404, detail="规范集合不存在")
        return rule_set

    async def _get_rule_count(self, rule_set_id: str, db: AsyncSession) -> int:
        result = await db.execute(
            select(func.count(ComplianceRule.id)).where(
                ComplianceRule.rule_set_id == uuid.UUID(str(rule_set_id))
            )
        )
        return result.scalar_one()
```

#### 2. `routes/compliance.py` 追加路由

在现有文件末尾追加以下三个路由（`compliance_import_service` 作为模块级单例初始化）：

```python
# 在文件顶部追加 import
from app.services.compliance_import_service import ComplianceImportService
from fastapi.responses import StreamingResponse
import io

# 模块级单例
compliance_import_service = ComplianceImportService()

# ── 导入相关路由（追加到文件末尾）────────────────────────────────────────────

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
    - Content-Disposition 遵循 RFC 5987 编码（steering 约定 #5）
    """
    user = request.state.user
    require_admin(user)

    # 验证 rule_set 存在性
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
```

#### 3. `backend/requirements.txt` 追加

```
openpyxl>=3.1,<4.0
```

追加到 `python-docx>=1.1` 之后。

---

### 前端组件

#### 1. `types/compliance.ts` 追加类型

```typescript
// ─────────────────────────────────────────────
// Excel 批量导入相关类型
// ─────────────────────────────────────────────

/** 预览接口返回的单条规则（含 Excel 行号） */
export interface ImportPreviewRule {
  row_number: number;
  rule_type: RuleType;
  title: string;
  requirement: string;
  severity: RuleSeverity;
  order: number;
}

/** 预览接口响应 */
export interface ImportPreviewResponse {
  preview_session_token: string;
  rules: ImportPreviewRule[];
  total_count: number;
}

/** 确认导入接口响应 */
export interface ImportConfirmResponse {
  imported_count: number;
  rule_set_id: string;
}

/** 行级校验错误 */
export interface ImportRowError {
  row_number: number;
  field: string;
  message: string;
}

/** 422 校验失败响应体 detail */
export interface ImportValidationError {
  code: string;
  message: string;
  errors?: ImportRowError[];
  current_count?: number;
  import_count?: number;
  limit?: number;
}
```

#### 2. `hooks/useCompliance.ts` 追加 hooks

```typescript
// ─────────────────────────────────────────────
// Excel 批量导入 hooks（追加到文件末尾）
// ─────────────────────────────────────────────

import type {
  ImportPreviewResponse,
  ImportConfirmResponse,
} from '../types/compliance';

/**
 * 下载 Excel 模板（blob 下载，遵循 steering 约定 #9）
 * 不使用 useMutation，直接返回触发函数，由组件调用
 */
export function useDownloadRulesTemplate() {
  return async (ruleSetId: string): Promise<void> => {
    const response = await axiosInstance.get(
      `/api/compliance/rule-sets/${ruleSetId}/rules/template`,
      { responseType: 'blob' }
    );
    const url = URL.createObjectURL(new Blob([response.data]));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'compliance_rules_template.xlsx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
}

/**
 * 上传 Excel 并获取解析预览
 */
export function useImportRulesPreview() {
  return useMutation({
    mutationFn: ({
      ruleSetId,
      file,
    }: {
      ruleSetId: string;
      file: File;
    }): Promise<ImportPreviewResponse> => {
      const formData = new FormData();
      formData.append('file', file);
      return unwrap<ImportPreviewResponse>(
        axiosInstance.post(
          `/api/compliance/rule-sets/${ruleSetId}/rules/import/preview`,
          formData
        )
      );
    },
  });
}

/**
 * 确认导入并批量写入规则
 */
export function useImportRulesConfirm() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      ruleSetId,
      previewSessionToken,
    }: {
      ruleSetId: string;
      previewSessionToken: string;
    }): Promise<ImportConfirmResponse> =>
      unwrap<ImportConfirmResponse>(
        axiosInstance.post(
          `/api/compliance/rule-sets/${ruleSetId}/rules/import/confirm`,
          { preview_session_token: previewSessionToken }
        )
      ),
    onSuccess: (_data, variables) => {
      // 刷新规则列表（使 TanStack Query 对应 queryKey 失效）
      queryClient.invalidateQueries({
        queryKey: complianceKeys.rules(variables.ruleSetId),
      });
      queryClient.invalidateQueries({
        queryKey: complianceKeys.ruleSets(),
      });
    },
  });
}
```

#### 3. `components/Compliance/RuleImportModal.tsx`（新建）

组件包含两个步骤：**上传步骤**（选择文件 + 上传并预览）和**预览确认步骤**（展示规则列表 + 确认导入）。

```tsx
import React, { useState } from 'react';
import {
  Modal, Upload, Button, Table, Tag, Alert, Space, Typography, message
} from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  useImportRulesPreview,
  useImportRulesConfirm,
} from '../../hooks/useCompliance';
import type {
  ImportPreviewRule,
  ImportPreviewResponse,
  ImportRowError,
  ImportValidationError,
  RuleType,
  RuleSeverity,
} from '../../types/compliance';

const { Dragger } = Upload;
const { Text } = Typography;

const RULE_TYPE_LABELS: Record<RuleType, string> = {
  number: '合同编号', name: '合同名称',
  description: '合同描述', file: '合同文件',
};
const SEVERITY_CONFIG: Record<RuleSeverity, { label: string; color: string }> = {
  must: { label: '必须', color: 'red' },
  should: { label: '建议', color: 'gold' },
};

interface RuleImportModalProps {
  ruleSetId: string;
  open: boolean;
  onClose: () => void;
}

type Step = 'upload' | 'preview';

const RuleImportModal: React.FC<RuleImportModalProps> = ({
  ruleSetId, open, onClose,
}) => {
  const [step, setStep] = useState<Step>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null);
  const [rowErrors, setRowErrors] = useState<ImportRowError[]>([]);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const previewMutation = useImportRulesPreview();
  const confirmMutation = useImportRulesConfirm();

  const handleClose = () => {
    // 重置状态
    setStep('upload');
    setSelectedFile(null);
    setPreviewData(null);
    setRowErrors([]);
    setErrorMessage('');
    onClose();
  };

  const handleUploadPreview = async () => {
    if (!selectedFile) return;
    setRowErrors([]);
    setErrorMessage('');
    try {
      const data = await previewMutation.mutateAsync({ ruleSetId, file: selectedFile });
      setPreviewData(data);
      setStep('preview');
    } catch (err: any) {
      const detail: ImportValidationError = err?.response?.data?.detail ?? {};
      if (detail.code === 'import_validation_failed' && detail.errors) {
        setRowErrors(detail.errors);
      } else if (detail.code === 'import_quota_exceeded') {
        setErrorMessage(
          `导入后总规则数将超过 ${detail.limit} 条上限。` +
          `当前已有 ${detail.current_count} 条，本次导入 ${detail.import_count} 条。` +
          `请减少导入条数或先删除部分现有规则。`
        );
      } else {
        setErrorMessage(detail.message || '上传失败，请重试');
      }
    }
  };

  const handleConfirm = async () => {
    if (!previewData) return;
    try {
      const result = await confirmMutation.mutateAsync({
        ruleSetId,
        previewSessionToken: previewData.preview_session_token,
      });
      message.success(`成功导入 ${result.imported_count} 条规则`);
      handleClose();
    } catch (err: any) {
      const detail: ImportValidationError = err?.response?.data?.detail ?? {};
      if (detail.code === 'import_preview_expired') {
        message.error('预览已过期，请重新上传 Excel 文件');
        setStep('upload');
        setPreviewData(null);
      } else if (detail.code === 'import_transaction_failed') {
        message.error('导入失败，数据未写入，请稍后重试');
      } else {
        message.error(detail.message || '导入失败，请重试');
      }
    }
  };

  // 预览表格列定义
  const previewColumns: ColumnsType<ImportPreviewRule> = [
    { title: 'Excel 行号', dataIndex: 'row_number', key: 'row_number', width: 90 },
    {
      title: '规则类型', dataIndex: 'rule_type', key: 'rule_type', width: 100,
      render: (v: RuleType) => <Tag>{RULE_TYPE_LABELS[v]}</Tag>,
    },
    { title: '规则标题', dataIndex: 'title', key: 'title', ellipsis: true },
    {
      title: '严重程度', dataIndex: 'severity', key: 'severity', width: 90,
      render: (v: RuleSeverity) => {
        const cfg = SEVERITY_CONFIG[v];
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    { title: '排序', dataIndex: 'order', key: 'order', width: 60 },
  ];

  const uploadFooter = (
    <Space>
      <Button onClick={handleClose}>取消</Button>
      <Button
        type="primary"
        loading={previewMutation.isPending}
        disabled={!selectedFile}
        onClick={handleUploadPreview}
      >
        上传并预览
      </Button>
    </Space>
  );

  const previewFooter = (
    <Space>
      <Button onClick={() => { setStep('upload'); setPreviewData(null); }}>
        返回重新上传
      </Button>
      <Button
        type="primary"
        loading={confirmMutation.isPending}
        onClick={handleConfirm}
      >
        确认导入
      </Button>
    </Space>
  );

  return (
    <Modal
      title={step === 'upload' ? '批量导入规则' : `预览确认（共 ${previewData?.total_count ?? 0} 条）`}
      open={open}
      onCancel={handleClose}
      footer={step === 'upload' ? uploadFooter : previewFooter}
      width={step === 'preview' ? 800 : 520}
      destroyOnClose
    >
      {step === 'upload' && (
        <>
          <Dragger
            accept=".xlsx"
            maxCount={1}
            beforeUpload={(file) => { setSelectedFile(file); return false; }}
            onRemove={() => setSelectedFile(null)}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">点击或拖拽 .xlsx 文件到此区域</p>
            <p className="ant-upload-hint">仅支持 .xlsx 格式，文件大小不超过 5 MB</p>
          </Dragger>
          {errorMessage && (
            <Alert style={{ marginTop: 12 }} type="error" message={errorMessage} showIcon />
          )}
          {rowErrors.length > 0 && (
            <Alert
              style={{ marginTop: 12 }}
              type="error"
              message={`共 ${rowErrors.length} 行数据校验失败`}
              description={
                <ul style={{ margin: 0, paddingLeft: 16 }}>
                  {rowErrors.map((e, i) => (
                    <li key={i}><Text type="danger">{e.message}</Text></li>
                  ))}
                </ul>
              }
              showIcon
            />
          )}
        </>
      )}
      {step === 'preview' && previewData && (
        <Table<ImportPreviewRule>
          rowKey="row_number"
          columns={previewColumns}
          dataSource={previewData.rules}
          pagination={{ pageSize: 20, showSizeChanger: false }}
          size="small"
          scroll={{ y: 400 }}
        />
      )}
    </Modal>
  );
};

export default RuleImportModal;
```

#### 4. `components/Compliance/RuleTable.tsx` 追加按钮

在现有 `RuleTable.tsx` 的操作栏（`div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}`）中追加「下载模板」和「批量导入」按钮，并引入 `RuleImportModal`：

```tsx
// 追加 import
import { DownloadOutlined, ImportOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { message } from 'antd';
import RuleImportModal from './RuleImportModal';
import { useDownloadRulesTemplate } from '../../hooks/useCompliance';

// 在组件内追加状态
const [importModalOpen, setImportModalOpen] = useState(false);
const downloadTemplate = useDownloadRulesTemplate();
const [downloading, setDownloading] = useState(false);

const handleDownloadTemplate = async () => {
  setDownloading(true);
  try {
    await downloadTemplate(ruleSetId);
  } catch {
    message.error('模板下载失败，请重试');
  } finally {
    setDownloading(false);
  }
};

// 操作栏替换为：
<div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
  <Button
    icon={<DownloadOutlined />}
    loading={downloading}
    onClick={handleDownloadTemplate}
  >
    下载模板
  </Button>
  <Button
    icon={<ImportOutlined />}
    onClick={() => setImportModalOpen(true)}
  >
    批量导入
  </Button>
  <Button type="primary" icon={<PlusOutlined />} onClick={onCreateClick}>
    新建规则
  </Button>
</div>

// 在 Table 之后追加：
<RuleImportModal
  ruleSetId={ruleSetId}
  open={importModalOpen}
  onClose={() => setImportModalOpen(false)}
/>
```

---

## Data Models

### Redis 数据结构

| Key | 格式 | TTL | 说明 |
|---|---|---|---|
| `compliance:import:preview:{token}` | JSON 字符串（规则列表数组） | 600s | 预览会话数据，确认导入后立即删除 |

**Value 格式示例：**

```json
[
  {
    "row_number": 3,
    "rule_type": "name",
    "title": "合同名称须包含甲方全称",
    "requirement": "合同名称中必须包含甲方公司全称，不得使用简称。",
    "severity": "must",
    "order": 1
  }
]
```

### 数据库变更

本功能**不新增任何数据库表或字段**。批量导入直接写入已有 `compliance_rules` 表，复用现有 ORM 模型 `ComplianceRule`。

---

## Error Handling

### 错误码一览

| HTTP 状态码 | `code` 字段 | 触发场景 |
|---|---|---|
| 401 | — | JWT 缺失/无效/过期（AuthMiddleware 统一处理） |
| 403 | — | 非法务/运营角色访问写接口 |
| 404 | — | rule_set_id 不存在 |
| 409 | `import_quota_exceeded` | 导入后总规则数超过 200 条 |
| 422 | `import_invalid_file` | 文件类型不合法或大小超限 |
| 422 | `import_empty_file` | 文件中无有效数据行 |
| 422 | `import_too_many_rows` | 单次导入超过 200 条 |
| 422 | `import_validation_failed` | 行级字段校验失败（含 `errors` 数组） |
| 422 | `import_preview_expired` | preview_session_token 不存在或已过期 |
| 500 | `import_transaction_failed` | 数据库事务执行失败 |

### 前端错误处理策略

```
previewMutation 失败
  ├─ import_validation_failed → 展示行级错误列表（含行号和原因）
  ├─ import_quota_exceeded    → 展示当前数量/导入数量/上限提示
  └─ 其他                     → 展示 detail.message

confirmMutation 失败
  ├─ import_preview_expired   → message.error + 回到上传步骤
  ├─ import_transaction_failed → message.error（数据未写入）
  └─ 其他                     → message.error(detail.message)
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Excel 解析 Round-Trip

*For any* 合法的规则列表（每条规则的 `rule_type`、`title`、`requirement`、`severity`、`order` 均满足字段约束），将其写入 Excel 文件后再通过 `_parse_excel` 解析，解析结果中每条规则的五个字段值应与原始输入完全一致。

**Validates: Requirements 2.2, 2.3, 2.7**

### Property 2: 非法字段校验拒绝

*For any* 包含至少一行非法数据的 Excel 文件（`rule_type` 不在枚举集合内、`title` 为空或超长、`requirement` 为空或超长、`severity` 不在枚举集合内、`order` 为非整数值），`_parse_excel` 应在 `errors` 列表中返回对应行的错误信息，且 `parsed_rows` 中不包含该行数据。

**Validates: Requirements 2.3, 2.4**

### Property 3: 权限校验对所有非法角色成立

*For any* `role ∉ {法务, 运营}` 的用户，调用下载模板、上传预览、确认导入三个接口均应返回 HTTP 403，且不执行任何文件解析或数据库写入操作。

**Validates: Requirements 1.4, 2.9, 3.7**

### Property 4: 确认导入写入数量一致性

*For any* 合法的预览会话（包含 N 条规则），调用确认导入接口后，`compliance_rules` 表中该 `rule_set_id` 下的规则数量应恰好增加 N 条，且响应中的 `imported_count` 等于 N。

**Validates: Requirements 3.3, 3.6**

### Property 5: Preview_Session_Token 一次性语义

*For any* 合法的 `preview_session_token`，第一次调用确认导入接口应成功；使用同一 token 再次调用确认导入接口应返回 HTTP 422（`import_preview_expired`），且不写入任何数据。

**Validates: Requirements 3.3**

### Property 6: 规则数量上限不变式

*For any* 已有 M 条规则的 `rule_set`（M ≤ 200），若本次导入 N 条规则且 M + N > 200，则预览接口和确认导入接口均应返回 HTTP 409，且 `compliance_rules` 表中该 `rule_set_id` 下的规则数量保持不变（仍为 M）。

**Validates: Requirements 2.8, 3.5**
