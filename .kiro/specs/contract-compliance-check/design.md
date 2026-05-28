# Design Document - 合同合规检查（第一阶段）

## Overview

本设计文档描述「合同合规检查」第一阶段（**检查 + 字段建议草稿**）的技术实现方案,严格对齐 `requirements.md` 中六项 Requirement,且与既有「合同预审看板」系统(`contract-pre-review` / `contract-enhancements` / `contract-revision-and-ai-improvements` 三个 Spec)保持解耦。

第一阶段的边界与目标:

- **做什么**:管理员在 `/compliance/admin/rule-sets` 维护规则集合,销售在 `/compliance/check/new` 上传合同文件 + 字段初稿,后端做文本抽取 → AI 合规检查 → 返回逐条不符合项 + 合同名称/合同描述建议草稿。
- **不做什么**:不自动发起合同预审、不生成合同编号建议(`suggested_number`)、不做 OCR、不做规则版本化、不做实时流式输出。
- **解耦原则**:独立 API 前缀(`/api/compliance/`)、独立模型模块(`backend/app/models/compliance.py`)、独立前端路由(`/compliance/...`)、独立 MinIO 路径前缀(`compliance/{user_id}/{check_id}/{filename}`),既有 ORM 模型/路由/页面**零侵入**。

技术栈复用情况:

| 能力 | 复用方式 |
|---|---|
| FastAPI + AuthMiddleware + JWT | 100% 复用,新增路由统一挂在 `/api/compliance` |
| SQLAlchemy 2.0 async/asyncpg | 新增 3 个表,放置在独立 model 模块 |
| Redis | 复用 `redis_client`,用于 Active_Rule_Set 缓存与频控计数 |
| MinIO | 复用 `minio_client.upload_file_data` / `get_file`,但使用独立 `compliance/...` 路径前缀,**不复用 `Attachment` 模型** |
| AI(OpenAI SDK + DeepSeek) | 在 `ai_service.py` 上新增 `check_compliance` 方法,复用 `AsyncOpenAI` 客户端与 `_validate_refs` 校验思路 |
| 钉钉 OAuth + JWT | 100% 复用,前端 `App.tsx` 现有未登录回跳逻辑直接覆盖新路径 |
| Socket.IO | **本阶段不新增任何事件**(轮询足够,避免连接风暴) |
| Celery | **本阶段不使用**(检查同步执行 + 前端轮询,简化部署链路) |

---

## Architecture

### 改动范围总览

```
┌──────────────────────────────────────────────────────────────────┐
│  前端层 (React 19 + TS + Antd 6 + Zustand 5 + TanStack Query 5) │
│                                                                  │
│  pages/Compliance/                       ← 5 个独立路由页         │
│    ├─ ComplianceListPage.tsx             /compliance              │
│    ├─ ComplianceCheckNewPage.tsx         /compliance/check/new    │
│    ├─ ComplianceCheckDetailPage.tsx      /compliance/check/{id}   │
│    ├─ admin/RuleSetListPage.tsx          /compliance/admin/rule-sets│
│    └─ admin/RuleSetDetailPage.tsx        /compliance/admin/rule-sets/{id}│
│  components/Compliance/                  ← 业务组件               │
│  hooks/useCompliance*.ts                 ← TanStack Query hooks   │
│  layouts/MainLayout.tsx                  ← 顶部新增「合规审查」入口 │
└──────────────────────────────────────────────────────────────────┘
                          │ HTTP (multipart + JSON)
                          │ 无 Socket.IO 新事件
┌──────────────────────────────────────────────────────────────────┐
│  后端层 (FastAPI + SQLAlchemy 2.0 async)                         │
│                                                                  │
│  routes/compliance.py                    ← 新增,/api/compliance/* │
│  services/compliance_service.py          ← 新增,业务编排          │
│  services/text_extractor.py              ← 新增,PDF/Word 抽取     │
│  services/ai_service.py                  ← 扩展 check_compliance  │
│  models/compliance.py                    ← 新增 3 个表的 ORM      │
│  schemas/compliance.py                   ← 新增 Pydantic 契约     │
│                                                                  │
│  既有 routes/contracts/files/reviews/ai 全部不动                  │
│  既有 models/User/Contract/...           ← 不增列、不增外键       │
└──────────────────────────────────────────────────────────────────┘
                          │
┌──────────────────────────────────────────────────────────────────┐
│  数据/存储层                                                      │
│                                                                  │
│  PostgreSQL                                                      │
│    compliance_rule_sets                  ← 新建表                 │
│    compliance_rules                      ← 新建表                 │
│    compliance_check_results              ← 新建表 (无 contract FK)│
│  Redis                                                           │
│    compliance:rate-limit:{user_id}       ← 60s/10次 频控          │
│    compliance:active-rule-set            ← Active_Rule_Set 缓存   │
│  MinIO (复用同一 bucket,独立路径前缀)                            │
│    compliance/{user_id}/{check_id}/{filename}                    │
└──────────────────────────────────────────────────────────────────┘
```

### 端到端数据流

**A. 管理员维护规则集合(Requirement 1 + 2):**

```
登录 → 进入 /compliance → 角色 ∈ {法务, 运营} 才显示「规则管理」入口
  → /compliance/admin/rule-sets (列表)
  → POST /api/compliance/rule-sets (创建,is_active=true 时事务内将其它 set 置 false)
  → /compliance/admin/rule-sets/{id} (详情,管理 rules)
  → POST/PUT/DELETE /api/compliance/rule-sets/{id}/rules
```

**B. 销售发起合规检查(Requirement 3 + 4):**

```
/compliance/check/new (Antd Form)
  → 选合同文件 (PDF/.doc/.docx, ≤50MB) + 三个字段初稿 (可全空)
  → POST /api/compliance/checks  (multipart/form-data)
       ┌── 频控校验 (Redis: 60s 内 10 次)
       ┌── 角色校验 (∈ {销售, 法务, 运营})
       ┌── 文件 MIME + size 校验 → 不过 → 422,不上传 MinIO
       ┌── 解析 rule_set_id,空则取 Active_Rule_Set,无则 → 409
       ├── upload_file_data → MinIO compliance/{user_id}/{check_id}/{filename}
       ├── INSERT compliance_check_results (status=pending)
       ├── TextExtractor.extract(file) →
       │     失败 → status=failed, error_message='file_extraction_failed' → 422
       │     空文本 → status=failed, error_message='empty_extracted_text' → 422
       │     超 100000 字符 → 截断 + text_truncated=true
       ├── AIService.check_compliance(extracted_text, drafts, rules) →
       │     超时 → status=failed, error_message='ai_timeout' → 504
       │     LLM 错误 → status=failed → 502
       │     JSON 解析失败 → 重试 1 次,再失败 → error_message='ai_invalid_response'
       └── UPDATE compliance_check_results SET status=completed, violations=..., suggested_*=...
  → 响应 { id, status, violations, suggested_name, suggested_description, text_truncated, ... }
  → 前端 navigate(/compliance/check/{id})
```

> 备注:本阶段同步返回完整结果,前端只在 `status=pending` 时启动轮询(对应"AI 真的没在 60s 内返回但接口没超时"的边缘情形,以及「重新检查」走异步)。

**C. 销售查看结果与历史(Requirement 5):**

```
/compliance/check/{id}
  → GET /api/compliance/checks/{id}
  → 若 status === 'pending' → 每 2s 轮询同一接口,90s 上限
  → 若 status === 'completed' → 渲染 violations + 建议草稿 + 复制按钮
  → 若 status === 'failed' → 渲染中文错误文案 + 「重新检查」按钮
       → POST /api/compliance/checks/{id}/recheck
       → 复用 file_storage_key 重做抽取 + AI
       → 若 MinIO 文件丢失 → 410
```

### 架构决策与理由

| 决策 | 备选方案 | 选择理由 |
|---|---|---|
| 同步检查 + 前端轮询 fallback | Celery 异步任务 + Socket.IO 事件 | 第一阶段 P95 检查时长 < 30s,同步路径调试和错误归因更直接;轮询作为兜底,90s 上限避免无限等待。引入 Celery 会增加部署链路、Redis broker 队列、ack 失败重试等复杂度,与「快速交付」目标不匹配。 |
| 独立 model 模块 + 无 contracts 外键 | 在 `Contract` 上新增 `compliance_check_id` 外键 | Requirement 6 要求与现有合同记录解耦,且本阶段合规检查不绑定具体已发起合同;预留可空外键到二阶段再扩展。 |
| 独立 MinIO 路径前缀,不复用 `attachments` 表 | 复用 `Attachment` 模型 + `contract_id=NULL` | `Attachment.contract_id NOT NULL`,放宽会破坏既有路径(`/api/files/attachments/{id}/download` 的鉴权依赖 contract);独立路径更清晰,删除合规检查记录时也不影响合同附件。 |
| 在 `ai_service.py` 上加方法,不新建 service | 新建 `compliance_ai_service.py` | 复用 `AsyncOpenAI` 客户端、超时配置、`_validate_refs` 思路,避免重复初始化;`AIService` 类已是聚合多个 AI 用途的容器(总结、问答),新增「合规检查」用途符合既有抽象。 |
| 独立 service 文件 `compliance_service.py` | 把所有逻辑塞到 `routes/compliance.py` | 业务编排(频控、文件 → MinIO、文本抽取、AI 调用、状态机)体量可观,放到 service 层便于单测与复用(尤其是「重新检查」与「首次检查」共享同一段逻辑)。 |
| 频控用 Redis `INCR` + `EXPIRE` 滑动窗口 | 数据库 SELECT count + INSERT | Requirement 3.12 是高频写场景,DB 查询会成为热点;Redis `INCR` + 60s `EXPIRE` 是标准方案。 |
| AI 超时 60s | 30s / 120s | 对齐既有 `settings.AI_TIMEOUT = 60`,合同正文 100k 字符 + 200 条规则,DeepSeek 实际响应 P95 ~25s,留足余量。 |
| 文件大小 50MB / 文本截断 100k | 30MB / 50k | 50MB 沿用 `MAX_FILE_SIZE`(steering 项目总览);100k 字符约对应 LLM 25k token,接近 DeepSeek 单次上下文上限的舒适区。 |

---

## Components and Interfaces

### 后端组件

#### 1. `routes/compliance.py`(新建)

统一挂在 `/api/compliance` 前缀下,使用 `APIRouter(prefix="/api/compliance", tags=["compliance"])`。所有路由通过 `auth_middleware` 已注入的 `request.state.user` 取当前用户。

```
# 规则集合 (Requirement 1)
POST   /api/compliance/rule-sets                    管理员创建规则集合
GET    /api/compliance/rule-sets                    所有用户可查列表
GET    /api/compliance/rule-sets/{rule_set_id}      获取详情(含规则)
PUT    /api/compliance/rule-sets/{rule_set_id}      管理员更新
DELETE /api/compliance/rule-sets/{rule_set_id}      管理员删除

# 规则 (Requirement 2)
POST   /api/compliance/rule-sets/{rule_set_id}/rules    管理员新增规则
GET    /api/compliance/rule-sets/{rule_set_id}/rules    所有用户可查列表
PUT    /api/compliance/rules/{rule_id}                  管理员更新
DELETE /api/compliance/rules/{rule_id}                  管理员删除

# 合规检查 (Requirement 3 + 5)
POST   /api/compliance/checks                       销售发起检查 (multipart)
GET    /api/compliance/checks                       查询历史 (角色相关数据范围)
GET    /api/compliance/checks/{check_id}            查询单条
POST   /api/compliance/checks/{check_id}/recheck    重新检查
```

权限装饰器(以 helper 形式实现,放 `routes/compliance.py` 顶部):

```python
def require_admin(user) -> None:
    """规则管理写接口的鉴权(R1.8 / R2.7)"""
    if user.role not in ("法务", "运营"):
        raise HTTPException(403, detail="仅法务/运营可维护合规规则")

def require_compliance_user(user) -> None:
    """发起检查接口的鉴权(R3.8)"""
    if user.role not in ("销售", "法务", "运营"):
        raise HTTPException(403, detail="当前角色无权发起合规检查")
```

#### 2. `services/compliance_service.py`(新建)

`ComplianceService` 类,聚焦业务编排。关键方法:

```python
class ComplianceService:
    def __init__(self, ai_service: AIService, text_extractor: TextExtractor):
        self.ai = ai_service
        self.extractor = text_extractor

    # === Rule Set 管理 ===
    async def create_rule_set(self, *, name, description, is_active, db) -> ComplianceRuleSet
    async def list_rule_sets(self, *, db) -> list[ComplianceRuleSet]
    async def update_rule_set(self, rule_set_id, *, fields, db) -> ComplianceRuleSet
    async def delete_rule_set(self, rule_set_id, *, db) -> None  # R1.7 active 拒绝

    # === Rule 管理 ===
    async def create_rule(self, rule_set_id, *, fields, db) -> ComplianceRule
    async def list_rules(self, rule_set_id, *, db) -> list[ComplianceRule]
    async def update_rule(self, rule_id, *, fields, db) -> ComplianceRule
    async def delete_rule(self, rule_id, *, db) -> None

    # === 合规检查主流程 ===
    async def perform_check(
        self, *, user_id, file: UploadFile,
        number_draft, name_draft, description_draft, rule_set_id,
        db
    ) -> ComplianceCheckResult:
        """完整一次检查的编排:校验 → 频控 → MinIO → 抽取 → AI → 持久化"""

    async def recheck(self, check_id, *, current_user_id, db) -> ComplianceCheckResult:
        """复用已存 file_storage_key 重做"""

    async def get_check(self, check_id, *, current_user, db) -> ComplianceCheckResult
    async def list_checks(self, *, current_user, page, page_size, status, db) -> dict

    # === 私有 ===
    async def _resolve_active_rule_set(self, db) -> ComplianceRuleSet | None
    async def _enforce_rate_limit(self, user_id) -> None  # R3.12
    async def _set_active_atomically(self, rule_set_id, db) -> None  # R1.2/R1.5 事务
```

**Active_Rule_Set 唯一性的实现**(对应 R1.2 / R1.5):在同一事务内执行 `UPDATE compliance_rule_sets SET is_active = false WHERE is_active = true AND id != :target_id` 后再 `UPDATE ... SET is_active = true WHERE id = :target_id`,共一个 `await db.commit()`。

**频控实现**(对应 R3.12):

```python
async def _enforce_rate_limit(self, user_id: str) -> None:
    key = f"compliance:rate-limit:{user_id}"
    # INCR 是原子操作,首次 INCR 后 EXPIRE 设置 60s 滑动窗口
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, 60)
    if count > 10:
        raise HTTPException(429, detail="请求过于频繁,请 60 秒后再试")
```

#### 3. `services/text_extractor.py`(新建)

```python
class TextExtractionError(Exception):
    """统一抽取异常,触发 R3.13 file_extraction_failed"""

class TextExtractor:
    MAX_LENGTH = 100_000

    async def extract(
        self, *, file_data: bytes, mime_type: str
    ) -> tuple[str, bool]:
        """
        Returns: (extracted_text, text_truncated)
        Raises:
            TextExtractionError: 当文件损坏 / 加密 / 不可解析
        """
        if mime_type == "application/pdf":
            text = self._extract_pdf(file_data)
        elif mime_type == (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ):
            text = self._extract_docx(file_data)
        elif mime_type == "application/msword":
            text = self._extract_doc(file_data)
        else:
            raise TextExtractionError(f"unsupported mime: {mime_type}")

        truncated = False
        if len(text) > self.MAX_LENGTH:
            text = text[: self.MAX_LENGTH]
            truncated = True
        return text, truncated
```

**技术选型**:

| 类型 | 库 | 备注 |
|---|---|---|
| `.pdf` | `pdfplumber >= 0.11`(底层 `pdfminer.six`) | 逐页 `page.extract_text()` + 表格抽取 `page.extract_tables()`,对多列 / 表格 / 签字盖章页排版鲁棒性显著优于 `pypdf`;加密 PDF 通过 `pdf.metadata` + 打开异常识别,直接抛 `TextExtractionError`。决策参考:[ContractGuard](https://github.com/he-yufeng/ContractGuard)(MIT)与多个企业合同审查项目均采用 `pdfplumber` 而非 `pypdf` |
| `.docx` | `python-docx >= 1.1` | 遍历 `doc.paragraphs` + 表格 `cell.text`,拼接为段落 |
| `.doc` (老二进制) | `olefile` + `antiword`(Linux 二进制)→ 实际部署用 `subprocess.run(["antiword", tmpfile])`;若部署环境无 antiword,可改用 `python-docx2txt` 的 `process()`(对部分 `.doc` 兼容)| 决策依据:`docx2txt` 纯 Python 易部署但兼容性较差;`antiword` 兼容性好但需在 Dockerfile 安装 apt 包。**推荐方案:Dockerfile 添加 `apt-get install -y antiword`,代码用 `subprocess.run` 调用,失败 → 抛 `TextExtractionError`**。 |

落地规则:抽取出的文本去除首尾空白(`text.strip()`)后判断长度;长度为 0 时由调用方(`compliance_service.perform_check`)将 `error_message` 置为 `empty_extracted_text` 并 422(R3.14)。

#### 4. `services/ai_service.py` 扩展

新增方法(不动既有 `generate_summary` / `answer_question`):

```python
class AIService:
    # ... 既有方法 ...

    async def check_compliance(
        self,
        *,
        rules: list[ComplianceRule],
        extracted_text: str,
        text_truncated: bool,
        number_draft: str | None,
        name_draft: str | None,
        description_draft: str | None,
    ) -> dict:
        """
        Returns:
            {
                "violations": [
                    {"rule_id": str, "location": str, "excerpt": str,
                     "description": str, "suggestion": str, "severity": str},
                    ...
                ],
                "suggested_name": str (1..200),
                "suggested_description": str (0..2000),
            }
        Raises:
            asyncio.TimeoutError: → R3.15 ai_timeout (504)
            ComplianceAIError: → R3.16 一般 AI 错误 (502)
            ComplianceAIInvalidResponseError: → R4.11 (status=failed, error_message='ai_invalid_response')
        """
```

**System Prompt 设计**:

```
你是「合同合规检查助理」。请基于「合同规范」「合同文件正文」「字段初稿」三类输入,
逐条比对并产出合规检查结果。

【输入】
1. 规则集合(每条规则给出 id / rule_type / title / requirement / severity):
   - rule_type ∈ {number, name, description, file}
     · number → 规则作用于「合同编号字段初稿」
     · name → 规则作用于「合同名称字段初稿」+ 合同正文
     · description → 规则作用于「合同描述字段初稿」+ 合同正文
     · file → 规则作用于「合同文件正文」
   - severity ∈ {must, should}
2. 合同文件正文(extracted_contract_text,可能是 null 表示无文本)
3. 文件是否被截断(text_truncated)
4. 三个字段初稿:number_draft / name_draft / description_draft (可能为 null)

【输出严格 JSON】(只输出 JSON,不要任何前后说明):
{
  "violations": [
    {
      "rule_id": "<必须为输入规则集合中的实际 id>",
      "location": "<必须与该 rule_id 对应规则的 rule_type 完全一致>",
      "excerpt": "<不超过 500 字符,location=number/name/description 时取自字段初稿;location=file 时取自 extracted_contract_text 相关片段;允许为空字符串>",
      "description": "<不超过 500 字符,具体说明违反点>",
      "suggestion": "<不超过 500 字符,给出修改建议>",
      "severity": "<必须与对应规则 severity 完全一致, must 或 should>"
    }
  ],
  "suggested_name": "<1-200 字符,符合规范的合同名称>",
  "suggested_description": "<0-2000 字符,符合规范的合同描述,允许空字符串>"
}

【约束】
- 不要输出 suggested_number 字段(合同编号由系统发号器生成)
- 不要输出 compliance_score 字段(由后端基于 violations 与 severity 计算,LLM 不参与打分)
- 当某 rule_type=number/name/description 对应的字段初稿为 null 或空字符串,
  不要为该字段类型输出 violation,仅 rule_type=file 不受字段初稿影响
- 必须使用规则的真实 id,不要杜撰
- text_truncated=true 时,可在 description 中提示「正文被截断,可能影响判断」
```

**校验与回退实现**(对应 R4.3 / R4.4 / R4.10 / R4.11):

```python
async def check_compliance(...) -> dict:
    if not rules:
        # R4.10:无规则,跳过模型调用;返回空 violations + score=100
        return self._fallback_no_rules(name_draft, description_draft, extracted_text)
        # _fallback_no_rules 返回:
        #   { "violations": [], "suggested_name": ..., "suggested_description": ...,
        #     "compliance_score": 100 }

    payload = self._build_compliance_prompt(rules, extracted_text, text_truncated, drafts)

    for attempt in range(2):  # R4.11 重试 1 次
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": payload},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=4096,
                    temperature=0.2,
                ),
                timeout=60,  # R4.12
            )
        except asyncio.TimeoutError:
            raise  # 直接抛给上层,触发 R3.15
        except Exception as e:
            raise ComplianceAIError(str(e))

        raw = response.choices[0].message.content or ""
        try:
            parsed = json.loads(raw)
            return self._postprocess(parsed, rules, drafts, extracted_text)
        except (json.JSONDecodeError, ValueError, KeyError):
            if attempt == 1:
                raise ComplianceAIInvalidResponseError("ai_invalid_response")
            continue  # 第一次失败,进入第二次重试

def _postprocess(self, parsed, rules, drafts, extracted_text) -> dict:
    """R4.3 / R4.4:rule_id 过滤、location 一致性、长度截断、suggested_name 兜底"""
    rule_map = {str(r.id): r for r in rules}
    violations = []
    for v in parsed.get("violations", []):
        rid = v.get("rule_id")
        rule = rule_map.get(rid)
        if rule is None:
            continue  # R4.3:rule_id 不在集合中 → 丢弃
        if v.get("location") != rule.rule_type.value:
            continue  # R4.3:location 与 rule_type 不一致 → 丢弃
        # R4.6/R4.7/R4.8:字段初稿为空时丢弃对应 location 的违规
        if v["location"] in ("number", "name", "description"):
            draft = drafts.get(f"{v['location']}_draft")
            if not draft:
                continue
        violations.append({
            "rule_id": rid,
            "location": v["location"],
            "excerpt": (v.get("excerpt") or "")[:500],
            "description": (v.get("description") or "")[:500],
            "suggestion": (v.get("suggestion") or "")[:500],
            "severity": rule.severity.value,  # 强制对齐规则 severity
        })

    # R4.4:suggested_name 长度归一化与兜底
    suggested_name = (parsed.get("suggested_name") or "")[:200]
    if not suggested_name:
        if drafts.get("name_draft"):
            suggested_name = drafts["name_draft"][:200]
        else:
            suggested_name = (extracted_text.replace("\n", " ").strip())[:200] or "未命名合同"
    suggested_description = (parsed.get("suggested_description") or "")[:2000]

    return {
        "violations": violations,
        "suggested_name": suggested_name,
        "suggested_description": suggested_description,
        "compliance_score": _compute_compliance_score(violations),  # R4.13
    }


def _compute_compliance_score(violations: list[dict]) -> int:
    """R4.13: 100 起扣,must -10/条,should -2/条,clamp 到 [0,100]."""
    score = 100
    for v in violations:
        if v["severity"] == "must":
            score -= 10
        elif v["severity"] == "should":
            score -= 2
    return max(0, min(100, score))
```

#### 5. `models/compliance.py`(新建)

放置 `ComplianceRuleSet`、`ComplianceRule`、`ComplianceCheckResult` 三张表的 SQLAlchemy ORM,以及对应的枚举(`RuleType`、`RuleSeverity`、`ComplianceCheckStatus`)。详见后文 Data Models 节。

> ⚠️ Steering 约定(条目 #3):枚举列必须用 `SQLEnum(MyEnum, values_callable=lambda x: [e.value for e in x])`,本模块严格遵守。

#### 6. `schemas/compliance.py`(新建)

Pydantic 请求/响应类型集中此处,详见 API Interfaces 节。

### 前端组件

#### 1. 路由与导航

`App.tsx` 在现有 `<Routes>` 中追加:

```tsx
<Route path="/" element={<ContractBoard />} />
<Route path="/compliance" element={<ComplianceListPage />} />
<Route path="/compliance/check/new" element={<ComplianceCheckNewPage />} />
<Route path="/compliance/check/:checkId" element={<ComplianceCheckDetailPage />} />
<Route path="/compliance/admin/rule-sets" element={<RuleSetListPage />} />
<Route path="/compliance/admin/rule-sets/:ruleSetId" element={<RuleSetDetailPage />} />
<Route path="*" element={<Navigate to="/" replace />} />
```

`MainLayout.tsx` 顶部 `<Header>` 内新增导航(替换或在 `<h1>` 旁追加,具体由 UI 走查决定):

```tsx
<Menu mode="horizontal" selectable={false}>
  <Menu.Item key="contract"><Link to="/">合同预审看板</Link></Menu.Item>
  <Menu.Item key="compliance"><Link to="/compliance">合规审查</Link></Menu.Item>
</Menu>
```

> 角色门禁不在路由层做(任何已登录用户都能访问 `/compliance` 看自己的列表),管理员入口与「全部合规检查」视图通过页面内 `currentUser.role` 条件渲染区分(R6.4)。后端是真正的鉴权边界。

#### 2. 页面与组件树

```
pages/Compliance/
├─ ComplianceListPage.tsx
│   └─ <ComplianceCheckList />            ← 当前用户的检查历史 (角色 ∈ 销售)
│   └─ <ComplianceCheckList scope="all"/> ← 全部 (角色 ∈ 法务/运营,额外渲染)
│   └─ <Button to="/compliance/check/new">新建合规检查</Button>
│   └─ <Button to="/compliance/admin/rule-sets">规则管理</Button> ← 角色 ∈ 法务/运营
├─ ComplianceCheckNewPage.tsx
│   └─ <ComplianceCheckForm />            ← Antd Form: 文件上传 + 三初稿 + rule_set 选择
│       └─ <RuleSetSelector />            ← 默认显示 Active_Rule_Set
│       └─ <Upload accept=".pdf,.doc,.docx" maxSize=50MB />
│       └─ <Input.TextArea> x3
├─ ComplianceCheckDetailPage.tsx
│   └─ <ComplianceCheckHeader />          ← 文件名 + 状态 + 元数据
│   └─ <TruncatedNotice show={text_truncated} />  ← R5.5
│   └─ <ComplianceStatusPending />        ← status=pending,启动 useComplianceCheckPolling
│   └─ <ComplianceStatusFailed />         ← status=failed,错误文案 + 重新检查按钮
│   └─ <ComplianceSuggestions />          ← 完成后展示 suggested_name / suggested_description + 复制
│   └─ <ViolationList />                  ← 完成后排序展示
│       └─ <ViolationItem severity location ... />
└─ admin/
   ├─ RuleSetListPage.tsx
   │   └─ <RuleSetTable />                ← 含 is_active 标记
   │   └─ <RuleSetCreateModal />
   └─ RuleSetDetailPage.tsx
       └─ <RuleSetMetaForm />             ← name / description / is_active
       └─ <RuleTable />                   ← 按 rule_type → order → created_at 排序
       └─ <RuleCreateEditDrawer />

components/Compliance/
├─ ComplianceCheckList.tsx
├─ ComplianceCheckForm.tsx
├─ RuleSetSelector.tsx
├─ ViolationList.tsx
├─ ViolationItem.tsx
├─ ComplianceSuggestions.tsx
├─ TruncatedNotice.tsx
└─ ErrorMessageMap.ts                     ← error_message → 中文文案
```

**`ErrorMessageMap.ts`**(对应 R5.8):

```typescript
export const COMPLIANCE_ERROR_MESSAGES: Record<string, string> = {
  file_extraction_failed: '合同文件解析失败,请确认文件未损坏且非加密文件',
  empty_extracted_text: '合同文件未抽取到可读文本(纯图片 PDF 暂不支持)',
  ai_timeout: 'AI 检查超时,请稍后重试',
  ai_invalid_response: 'AI 返回结果无法解析,请稍后重试',
};

export function getComplianceErrorText(errorMessage: string | null | undefined): string {
  if (!errorMessage) return 'AI 检查失败';
  return COMPLIANCE_ERROR_MESSAGES[errorMessage] || `AI 检查失败:${errorMessage}`;
}
```

#### 3. TanStack Query Hooks

`frontend/src/hooks/useCompliance.ts`(单文件聚合所有 query/mutation hooks,与既有 `useContracts.ts` 风格一致):

```typescript
// === Rule Set ===
export function useRuleSets(): UseQueryResult<RuleSet[]>
export function useRuleSet(ruleSetId: string): UseQueryResult<RuleSetDetail>
export function useCreateRuleSet(): UseMutationResult<RuleSet, Error, CreateRuleSetDto>
export function useUpdateRuleSet(): UseMutationResult<RuleSet, Error, UpdateRuleSetDto>
export function useDeleteRuleSet(): UseMutationResult<void, Error, string>

// === Rule ===
export function useRules(ruleSetId: string): UseQueryResult<Rule[]>
export function useCreateRule(): UseMutationResult<Rule, Error, CreateRuleDto>
export function useUpdateRule(): UseMutationResult<Rule, Error, UpdateRuleDto>
export function useDeleteRule(): UseMutationResult<void, Error, string>

// === Check ===
export function useComplianceChecks(params: ListParams): UseQueryResult<ChecksPage>
export function useComplianceCheck(checkId: string): UseQueryResult<ComplianceCheckResult>
export function useCreateComplianceCheck(): UseMutationResult<ComplianceCheckResult, Error, FormData>
export function useRecheckCompliance(): UseMutationResult<ComplianceCheckResult, Error, string>

// === 轮询(R5.6)===
export function useComplianceCheckPolling(checkId: string, enabled: boolean) {
  return useQuery({
    queryKey: ['compliance', 'check', checkId],
    queryFn: () => fetchCheck(checkId),
    enabled,
    refetchInterval: (data) => (data?.status === 'pending' ? 2000 : false),
    refetchIntervalInBackground: false,
    staleTime: 0,
  });
}
// 配合 Detail 页面的 useEffect 在累计 90s 后停止轮询(R5.6 上限)
```

> 所有请求**必须**使用 `frontend/src/utils/axios` 中的 axios 实例(steering 约定 #1)。

#### 4. 状态管理

本功能**不引入新的 Zustand store**:

- 服务端数据全部走 TanStack Query 缓存。
- 表单态走 Antd Form 的 `useForm`。
- 路由参数 / 用户身份从既有 `useUserStore` 读取。

---

## Data Models

### 数据库变更汇总

| 类型 | 对象 | 说明 |
|---|---|---|
| 新建表 | `compliance_rule_sets` | 规则集合 |
| 新建表 | `compliance_rules` | 单条规则,FK → `compliance_rule_sets.id` ON DELETE CASCADE |
| 新建表 | `compliance_check_results` | 一次合规检查的结果(无 contracts FK) |
| 新建枚举 | `rule_type` | `('number','name','description','file')` |
| 新建枚举 | `rule_severity` | `('must','should')` |
| 新建枚举 | `compliance_check_status` | `('pending','completed','failed')` |
| 新建索引 | `ix_compliance_rule_sets_active` | partial index `WHERE is_active = true`(强约束 active 唯一) |
| 新建索引 | `ix_compliance_rules_set_id` | 加速按 set 查询 |
| 新建索引 | `ix_compliance_check_results_requested_by_at` | 历史列表分页 |
| 既有 ORM 模型 | `Contract` / `Attachment` / `Review` / `Comment` / ... | **零改动** |

### `compliance_rule_sets`

```python
class ComplianceRuleSet(Base):
    __tablename__ = "compliance_rule_sets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    rules: Mapped[list["ComplianceRule"]] = relationship(
        "ComplianceRule", back_populates="rule_set",
        cascade="all, delete-orphan", lazy="select"
    )

    __table_args__ = (
        # 软强约束:partial unique index 仅对 is_active=true 行加唯一性
        # PostgreSQL 支持,作为代码层事务的兜底
        Index(
            "uq_compliance_rule_sets_one_active",
            "is_active",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )
```

### `compliance_rules`

```python
class RuleType(str, enum.Enum):
    NUMBER = "number"
    NAME = "name"
    DESCRIPTION = "description"
    FILE = "file"

class RuleSeverity(str, enum.Enum):
    MUST = "must"
    SHOULD = "should"

class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_rule_sets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    rule_type: Mapped[RuleType] = mapped_column(
        SQLEnum(RuleType, name="rule_type",
                values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    requirement: Mapped[str] = mapped_column(String(2000), nullable=False)
    severity: Mapped[RuleSeverity] = mapped_column(
        SQLEnum(RuleSeverity, name="rule_severity",
                values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=RuleSeverity.MUST,
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    rule_set: Mapped["ComplianceRuleSet"] = relationship(
        "ComplianceRuleSet", back_populates="rules"
    )

    __table_args__ = (
        Index("ix_compliance_rules_set_id_order",
              "rule_set_id", "rule_type", "order", "created_at"),
    )
```

### `compliance_check_results`

```python
class ComplianceCheckStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class ComplianceCheckResult(Base):
    __tablename__ = "compliance_check_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    rule_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_rule_sets.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[ComplianceCheckStatus] = mapped_column(
        SQLEnum(ComplianceCheckStatus, name="compliance_check_status",
                values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ComplianceCheckStatus.PENDING, index=True,
    )

    # 文件元数据(MinIO key 独立路径前缀)
    file_storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # 抽取结果
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    text_truncated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 字段初稿(任一可空)
    number_draft: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name_draft: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description_draft: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # AI 输出
    violations: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    suggested_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    suggested_description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    compliance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0..100, R4.13

    # 失败原因
    error_message: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # 时间戳
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 关系
    requester: Mapped["User"] = relationship("User", foreign_keys=[requested_by], lazy="joined")
    rule_set: Mapped["ComplianceRuleSet | None"] = relationship(
        "ComplianceRuleSet", foreign_keys=[rule_set_id], lazy="joined"
    )

    __table_args__ = (
        Index("ix_compliance_check_results_requester_time",
              "requested_by", "requested_at",
              postgresql_ops={"requested_at": "DESC"}),
        Index("ix_compliance_check_results_status", "status"),
    )
```

### `violations` JSONB 形状(每元素)

```json
{
  "rule_id": "uuid string",
  "location": "number | name | description | file",
  "excerpt": "<= 500 chars",
  "description": "<= 500 chars",
  "suggestion": "<= 500 chars",
  "severity": "must | should"
}
```

后端在序列化响应给前端时,会用 `rule_set.rules` 关联表查 `rule_id → rule.title / rule.rule_type`,补充为 `rule_title` / `rule_type` 字段,**不**冗余写到 JSONB 列(避免规则改名后字段陈旧)。

### Alembic 迁移大纲

新增一个迁移文件 `xxxx_add_compliance_tables.py`:

```python
def upgrade():
    # 枚举
    op.execute("CREATE TYPE rule_type AS ENUM ('number','name','description','file')")
    op.execute("CREATE TYPE rule_severity AS ENUM ('must','should')")
    op.execute("CREATE TYPE compliance_check_status AS ENUM ('pending','completed','failed')")

    # compliance_rule_sets
    op.create_table(
        "compliance_rule_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "uq_compliance_rule_sets_one_active",
        "compliance_rule_sets", ["is_active"],
        unique=True, postgresql_where=sa.text("is_active = true"),
    )

    # compliance_rules
    op.create_table(
        "compliance_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_set_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("compliance_rule_sets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_type",
                  postgresql.ENUM(name="rule_type", create_type=False),
                  nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("requirement", sa.String(2000), nullable=False),
        sa.Column("severity",
                  postgresql.ENUM(name="rule_severity", create_type=False),
                  nullable=False, server_default="must"),
        sa.Column("order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_compliance_rules_set_id_order",
                    "compliance_rules",
                    ["rule_set_id", "rule_type", "order", "created_at"])

    # compliance_check_results
    op.create_table(
        "compliance_check_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_set_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("compliance_rule_sets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status",
                  postgresql.ENUM(name="compliance_check_status", create_type=False),
                  nullable=False, server_default="pending"),
        sa.Column("file_storage_key", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.BigInteger, nullable=False),
        sa.Column("file_mime_type", sa.String(100), nullable=False),
        sa.Column("extracted_text", sa.Text, nullable=False, server_default=""),
        sa.Column("text_truncated", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("number_draft", sa.String(100), nullable=True),
        sa.Column("name_draft", sa.String(200), nullable=True),
        sa.Column("description_draft", sa.String(2000), nullable=True),
        sa.Column("violations", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("suggested_name", sa.String(200), nullable=True),
        sa.Column("suggested_description", sa.String(2000), nullable=True),
        sa.Column("compliance_score", sa.Integer, nullable=True),  # R4.13: 0..100, NULL on failed
        sa.Column("error_message", sa.String(200), nullable=True),
        sa.Column("requested_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )
    op.create_index(
        "ix_compliance_check_results_requester_time",
        "compliance_check_results", ["requested_by", "requested_at"],
        postgresql_ops={"requested_at": "DESC"},
    )
    op.create_index(
        "ix_compliance_check_results_status",
        "compliance_check_results", ["status"],
    )

def downgrade():
    op.drop_index("ix_compliance_check_results_status", "compliance_check_results")
    op.drop_index("ix_compliance_check_results_requester_time", "compliance_check_results")
    op.drop_table("compliance_check_results")
    op.drop_index("ix_compliance_rules_set_id_order", "compliance_rules")
    op.drop_table("compliance_rules")
    op.drop_index("uq_compliance_rule_sets_one_active", "compliance_rule_sets")
    op.drop_table("compliance_rule_sets")
    op.execute("DROP TYPE compliance_check_status")
    op.execute("DROP TYPE rule_severity")
    op.execute("DROP TYPE rule_type")
```

---

## API Interfaces

所有响应使用项目既有的统一封装(参考 `routes/contracts.py`):

```python
{"success": true, "data": {...}}
{"success": false, "error": {"code": "...", "message": "..."}}
```

### 规则集合(Requirement 1)

```
POST /api/compliance/rule-sets
  Auth: 法务/运营
  Body: { "name": "...", "description": "...", "is_active": false }
  Response: { success, data: { id, name, description, is_active, rule_count, created_at, updated_at } }
  Errors: 401 / 403 / 422

GET /api/compliance/rule-sets
  Auth: 任何已登录用户
  Response: { success, data: { rule_sets: [{ ...含 rule_count }] } }

GET /api/compliance/rule-sets/{rule_set_id}
  Response: { success, data: { rule_set, rules: [...] } }

PUT /api/compliance/rule-sets/{rule_set_id}
  Auth: 法务/运营
  Body: { name?, description?, is_active? }
  Response: { success, data: { ...rule_set } }
  Errors: 401 / 403 / 404 / 422

DELETE /api/compliance/rule-sets/{rule_set_id}
  Auth: 法务/运营
  Response: 204 No Content
  Errors: 401 / 403 / 404 / 409 (active 时拒绝, R1.7)
```

### 规则(Requirement 2)

```
POST /api/compliance/rule-sets/{rule_set_id}/rules
  Auth: 法务/运营
  Body: { rule_type, title, requirement, severity, order }
  Response: { success, data: { rule } }
  Errors: 401 / 403 / 404 / 409 (>= 200 条, R2.9) / 422

GET /api/compliance/rule-sets/{rule_set_id}/rules
  Response: { success, data: { rules: [...排序后] } }

PUT /api/compliance/rules/{rule_id}
  Auth: 法务/运营

DELETE /api/compliance/rules/{rule_id}
  Auth: 法务/运营
```

### 合规检查(Requirement 3 + 5)

```
POST /api/compliance/checks
  Auth: 销售/法务/运营
  Content-Type: multipart/form-data
  Form fields:
    file (UploadFile, required, ≤50MB, MIME ∈ {pdf, doc, docx})
    number_draft (str, optional, 0..100)
    name_draft (str, optional, 0..200)
    description_draft (str, optional, 0..2000)
    rule_set_id (str, optional UUID)
  Response: { success, data: ComplianceCheckResult }  ← 完整结构,见下
  Errors:
    401 - JWT 无效
    403 - 角色不在 {销售,法务,运营}
    404 - rule_set_id 指定但不存在
    409 - 未指定 rule_set_id 且无 active set
    422 - 文件参数错误 / 抽取失败 (file_extraction_failed) / 空文本 (empty_extracted_text)
    429 - 频控 (60s 10次)
    502 - AI 服务错误
    504 - AI 超时

GET /api/compliance/checks
  Auth: 任何已登录用户
  Query: page, page_size, status
  Response: { success, data: { items: [ComplianceCheckListItem], total, page, page_size } }
  数据范围(R5.12):
    role ∈ {销售} → 仅 requested_by = current_user
    role ∈ {法务,运营} → 全部
    其他角色 → 同销售(只看自己),也是合规处理(实测路径只允许销售/法务/运营触达列表)

GET /api/compliance/checks/{check_id}
  Auth: requester 本人或法务/运营
  Response: { success, data: ComplianceCheckResult }
  Errors: 401 / 403 / 404

POST /api/compliance/checks/{check_id}/recheck
  Auth: requester 本人或法务/运营
  Response: { success, data: ComplianceCheckResult }
  Errors: 401 / 403 / 404 / 410 (file lost) / 502 / 504
```

### Pydantic Schema (`schemas/compliance.py`)

```python
class ComplianceCheckResultDto(BaseModel):
    id: str
    status: Literal["pending", "completed", "failed"]
    requested_by: UserBriefDto              # id / name / avatar
    rule_set_id: str | None
    rule_set_name: str | None
    file_name: str
    file_size: int
    file_mime_type: str
    extracted_text: str                     # 长度 0-100k
    text_truncated: bool
    number_draft: str | None
    name_draft: str | None
    description_draft: str | None
    violations: list[ViolationDto]
    suggested_name: str | None
    suggested_description: str | None
    compliance_score: int | None             # 0..100, status != completed 时为 None
    requested_at: datetime
    completed_at: datetime | None
    error_message: str | None
    # 注意:不包含 suggested_number / contract_text 字段 (R5.1)

class ViolationDto(BaseModel):
    rule_id: str
    rule_title: str                          # 后端 join 补全
    rule_type: Literal["number","name","description","file"]
    location: Literal["number","name","description","file"]
    excerpt: str                             # ≤ 500
    description: str                         # ≤ 500
    suggestion: str                          # ≤ 500
    severity: Literal["must","should"]

class ComplianceCheckListItemDto(BaseModel):
    id: str
    status: Literal["pending","completed","failed"]
    name_draft: str | None
    rule_set_name: str | None
    file_name: str
    text_truncated: bool
    violation_count: int | None              # 仅 completed 才有,否则 None
    compliance_score: int | None             # 0..100, status != completed 时为 None
    requested_at: datetime
    completed_at: datetime | None
    # 不包含 contract_text / extracted_text (R5.2)
```

---

## Correctness Properties

> 以下属性以「不变量」形式给出,既覆盖 requirements.md 的 IF/THEN 边界,也作为后续 Property-Based Testing(Hypothesis / fast-check)的目标性质。每条标注关联的 Requirement 与拟用工具。

### Property 1: Active Rule Set 唯一性
**Validates: Requirements 1.2, 1.5**
对任意通过创建/更新接口产生的 `compliance_rule_sets` 状态,`SELECT COUNT(*) FROM compliance_rule_sets WHERE is_active = true ≤ 1`。即使并发提交多个 `is_active=true` 的请求,partial unique index `uq_compliance_rule_sets_one_active` 在数据库层兜底拒绝。

### Property 2: 单 Rule Set 规则数上限
**Validates: Requirements 2.9**
对任意 `rule_set_id`,`SELECT COUNT(*) FROM compliance_rules WHERE rule_set_id = X ≤ 200`。新增第 201 条时返回 409,且行数不变。

### Property 3: violations 中 rule_id 必属于本次集合
**Validates: Requirements 4.3**
对任意成功完成的 Compliance_Check_Result,设其 `rule_set_id` 关联规则 ID 集合为 `R`,则 `∀ v ∈ violations: v.rule_id ∈ R`。

### Property 4: violations.location 与规则 rule_type 一致
**Validates: Requirements 4.3**
`∀ v ∈ violations: v.location == rule_map[v.rule_id].rule_type`。

### Property 5: violations.severity 与规则 severity 一致
**Validates: Requirements 4.3**
`∀ v ∈ violations: v.severity == rule_map[v.rule_id].severity`。后端 `_postprocess` 在拷贝 violation 时直接用规则的 severity 覆写 LLM 返回值,确保此属性恒成立(LLM 返回错的 severity 会被无声纠正)。

### Property 6: suggested_name 强约束
**Validates: Requirements 4.4**
对 `status=completed` 的 Compliance_Check_Result,`1 ≤ len(suggested_name) ≤ 200`。`status=failed` 时 `suggested_name` 可为 NULL。

### Property 7: suggested_description 弱约束
**Validates: Requirements 4.4**
对 `status=completed`,`0 ≤ len(suggested_description) ≤ 2000`(允许空字符串)。

### Property 8: 字段初稿空时不输出对应 location 违规
**Validates: Requirements 4.6, 4.7, 4.8**
对任一 `loc ∈ {'number','name','description'}`,若 `${loc}_draft` 为 NULL 或 strip 后为空,则 `∀ v ∈ violations: v.location ≠ loc`。`rule_type='file'` 类规则不受此约束影响。

### Property 9: 文件参数错误零副作用
**Validates: Requirements 3.7**
若请求中 `file` 缺失、MIME 不在白名单、size > 50MB 或任一 draft 超长,则该请求**不**产生:① MinIO 对象 ② `compliance_check_results` 行 ③ AI 调用。数据库与对象存储的状态完全等于请求未发起。

### Property 10: 频控严格上界
**Validates: Requirements 3.12**
对任意单一 `user_id`,在任意 60 秒滑动窗口内,`POST /api/compliance/checks` 返回 2xx 的次数 ≤ 10。窗口外的请求计数清零(由 Redis EXPIRE 保证)。

### Property 11: compliance_score 算术属性
**Validates: Requirements 4.13**
对 `status=completed`:`0 ≤ compliance_score ≤ 100`,且
`compliance_score == max(0, min(100, 100 - 10 * |{v ∈ violations: v.severity='must'}| - 2 * |{v ∈ violations: v.severity='should'}|))`。
对 `status=failed`,`compliance_score IS NULL`。violations 为空时 compliance_score = 100。

### Property 12: status 状态机单调
**Validates: Requirements 3.2, 3.3, 3.13, 3.14, 3.15, 3.16**
任一 Compliance_Check_Result 的 `status` 转移只允许:`pending → completed` 或 `pending → failed`,**不允许**任何反向或越级转移。recheck 走新事务覆写同一行 → 仍是 `pending → 终态`。

### Property 13: 数据范围隔离
**Validates: Requirements 5.10, 5.12**
- 角色 ∈ {销售}:`GET /api/compliance/checks/{id}` 仅在 `requested_by == current_user.id` 时返回 200,否则 403。
- 角色 ∈ {销售}:`GET /api/compliance/checks` 返回的所有 `item.requested_by == current_user.id`。
- 角色 ∈ {法务, 运营}:无 `requested_by` 过滤(数据范围 = 全集)。

### Property 14: 解耦不变量
**Validates: Requirements 6.6, 6.7**
`Contract` / `Attachment` / `Review` / `Comment` / `AISummary` / `Notification` 模型的字段集合在本 Spec 实施前后保持不变。`compliance_check_results` 不存在指向 `contracts.id` 的外键。

### Property 15: 错误文案 fallback 完备(前端)
**Validates: Requirements 5.8**
`getComplianceErrorText` 对**任意**字符串输入都返回非空中文字符串(已知 key 走映射表,未知 key 走 `AI 检查失败:{x}`,空值/null 走 `AI 检查失败`)。

### Property 16: 轮询自动停止(前端)
**Validates: Requirements 5.6**
`useComplianceCheckPolling`:从 `enabled=true` 起算,数据 `status !== 'pending'` 时 `refetchInterval` 返回 false;累计经过墙上时间 > 90s 时 Detail 页面把 `enabled` 置 false。两者满足任一则后续不再请求。

### Property 17: 复制不污染剪贴板格式(前端)
**Validates: Requirements 5.4**
`<ComplianceSuggestions>` 的「复制到剪贴板」按钮调用 `navigator.clipboard.writeText` 写入纯文本,不携带 HTML 格式;`suggested_name` 与 `suggested_description` 各自独立按钮,互不干扰。

---

## Error Handling

> 覆盖所有 IF/THEN 边界,逐条列出 HTTP 状态码、`error_message` / 业务码、是否回滚、关联的 Requirement。

### 规则集合(R1)

| 触发条件 | HTTP | 错误体 message 关键词 | 回滚 | 关联 |
|---|---|---|---|---|
| JWT 缺失/无效/过期 | 401 | "未登录或登录已过期" | 中间件直接拒绝 | R1.9 |
| 角色不在 {法务,运营} 调写接口 | 403 | "仅法务/运营可维护合规规则" | 不开事务 | R1.8 |
| `name` strip 后空 / >100 字符 / `description` >1000 字符 | 422 | 字段约束说明 | Pydantic 在路由层拒绝,不开事务 | R1.11 |
| `rule_set_id` 不存在(PUT/DELETE) | 404 | "规范集合不存在" | 不开事务 | R1.10 |
| 删除 active rule set | 409 | "请先停用该规范集合再删除" | rollback | R1.7 |

### 规则(R2)

| 触发条件 | HTTP | 错误体 message 关键词 | 回滚 | 关联 |
|---|---|---|---|---|
| `rule_type`/`severity` 不在合法集合 / `title` strip 空或 >100 / `requirement` strip 空或 >2000 | 422 | 字段约束说明 | 不开事务 | R2.6 |
| 角色不在 {法务,运营} 调写接口 | 403 | "仅法务/运营可维护合规规则" | 不开事务 | R2.7 |
| `rule_set_id` / `rule_id` 不存在 | 404 | 资源不存在说明 | 不开事务 | R2.8 |
| 单 rule_set 已 200 条还要新增 | 409 | "单个规范集合下最多可包含 200 条规则" | rollback | R2.9 |

### 合规检查 - 提交(R3)

| 触发条件 | HTTP | error_message 字段 | 副作用 | 关联 |
|---|---|---|---|---|
| JWT 无效 | 401 | — | 中间件拦截 | R3.9 |
| 角色不在 {销售,法务,运营} | 403 | — | 不上传/不写库/不调 AI | R3.8 |
| file 缺失或 MIME 非白名单或 size>50MB 或 draft 超长 | 422 | — (Pydantic/Form 校验) | 不上传/不写库/不调 AI | R3.7 |
| `rule_set_id` 提供但不存在 | 404 | — | 不上传/不写库/不调 AI | R3.6 |
| 未提供 `rule_set_id` 且无 active set | 409 | — | 不上传/不写库/不调 AI | R3.5 |
| 60s 内同 user 第 11 次请求 | 429 | — | 不上传/不写库/不调 AI | R3.12 |
| 文本抽取异常(损坏/加密/不识别) | 422 | `file_extraction_failed` | **MinIO 已上传**,记录 status=failed 持久化(便于诊断) | R3.13 |
| 抽取出文本 strip 后长度 0 | 422 | `empty_extracted_text` | MinIO 已上传 + 记录 status=failed | R3.14 |
| AI 60s 超时 | 504 | `ai_timeout` | MinIO 已上传 + 记录 status=failed | R3.15 |
| AI 接口错误 / 网络异常 | 502 | AI 异常 message | MinIO 已上传 + 记录 status=failed | R3.16 |
| AI JSON 解析两次失败 | 200 + status=failed | `ai_invalid_response` | MinIO 已上传 + 记录 status=failed,**接口仍 200**,前端按 status=failed 渲染 | R4.11 |

### 合规检查 - 查看(R5)

| 触发条件 | HTTP | 错误体 message 关键词 | 关联 |
|---|---|---|---|
| `check_id` 不存在 | 404 | "检查记录不存在" | R5.11 |
| 非 requester 本人且角色 ∉ {法务,运营} | 403 | "无权查看该检查记录" | R5.10 |
| Recheck 时 MinIO 文件丢失 | 410 | "合同文件已不可访问,请重新上传" | R5.9 |
| Recheck 触发的 AI 错误 | 502/504 | 同 R3.15/R3.16 | R5.9 |

### 错误响应统一格式

```json
{
  "success": false,
  "error": {
    "code": "compliance_rate_limited",
    "message": "请求过于频繁,请 60 秒后再试"
  }
}
```

`code` 命名约定:

- `compliance_unauthorized` (401) / `compliance_forbidden` (403) / `compliance_not_found` (404)
- `compliance_validation_failed` (422,通用 schema 校验)
- `compliance_active_rule_set_required` (409, R3.5) / `compliance_active_rule_set_in_use` (409, R1.7) / `compliance_rules_quota_exceeded` (409, R2.9)
- `compliance_rate_limited` (429, R3.12)
- `compliance_file_extraction_failed` (422, R3.13) / `compliance_empty_extracted_text` (422, R3.14)
- `compliance_ai_timeout` (504, R3.15) / `compliance_ai_error` (502, R3.16)
- `compliance_file_lost` (410, R5.9)

---

## Testing Strategy

### 测试金字塔分层

| 层级 | 工具 | 覆盖目标 |
|---|---|---|
| 单元测试 | `pytest` + `pytest-asyncio` | `_postprocess` 校验逻辑、`_compute_compliance_score`、`_enforce_rate_limit`、`TextExtractor` 各分支(纯函数) |
| Property-Based Testing | `hypothesis`(后端) / `fast-check`(前端可选) | P1~P17 不变量 |
| 集成测试 | `pytest` + `httpx.AsyncClient` + 真 PostgreSQL(test 库)+ fakeredis + mocked AI | 路由 → service → DB 全链路;频控滑动窗口;Active set 唯一性的并发场景 |
| E2E 测试 | `Playwright`(已有) | 关键用户旅程:管理员维护规则集 / 销售上传文件查看检查结果 / 角色门禁 |

### Hypothesis 落地示例

#### P3 + P4 + P5: violations 一致性

```python
from hypothesis import given, strategies as st
from hypothesis.strategies import composite

@composite
def rule_set_strategy(draw):
    n = draw(st.integers(min_value=1, max_value=20))
    return [
        {
            "id": str(uuid4()),
            "rule_type": draw(st.sampled_from(["number","name","description","file"])),
            "severity": draw(st.sampled_from(["must","should"])),
            "title": draw(st.text(min_size=1, max_size=100)),
            "requirement": draw(st.text(min_size=1, max_size=2000)),
        }
        for _ in range(n)
    ]

@given(
    rules=rule_set_strategy(),
    llm_violations=st.lists(st.fixed_dictionaries({
        "rule_id": st.text(),
        "location": st.sampled_from(["number","name","description","file","invalid"]),
        "excerpt": st.text(max_size=600),
        "description": st.text(max_size=600),
        "suggestion": st.text(max_size=600),
        "severity": st.sampled_from(["must","should","critical"]),
    })),
    drafts=st.fixed_dictionaries({
        "number_draft": st.one_of(st.none(), st.text(max_size=100)),
        "name_draft": st.one_of(st.none(), st.text(max_size=200)),
        "description_draft": st.one_of(st.none(), st.text(max_size=2000)),
    }),
)
def test_postprocess_invariants(rules, llm_violations, drafts):
    parsed = {"violations": llm_violations, "suggested_name": "x", "suggested_description": ""}
    out = AIService()._postprocess(parsed, rules, drafts, extracted_text="some text")
    rule_map = {r["id"]: r for r in rules}
    for v in out["violations"]:
        assert v["rule_id"] in rule_map                                      # P3
        assert v["location"] == rule_map[v["rule_id"]]["rule_type"]          # P4
        assert v["severity"] == rule_map[v["rule_id"]]["severity"]           # P5
        if v["location"] in ("number", "name", "description"):
            assert drafts[f"{v['location']}_draft"]                          # P8
```

#### P11: compliance_score 算术

```python
@given(
    must_count=st.integers(min_value=0, max_value=50),
    should_count=st.integers(min_value=0, max_value=50),
)
def test_compliance_score(must_count, should_count):
    violations = (
        [{"severity": "must"}] * must_count
        + [{"severity": "should"}] * should_count
    )
    score = _compute_compliance_score(violations)
    assert 0 <= score <= 100
    expected = max(0, min(100, 100 - 10 * must_count - 2 * should_count))
    assert score == expected
```

#### P10: 频控滑动窗口

```python
@given(
    timestamps=st.lists(
        st.floats(min_value=0.0, max_value=120.0),
        min_size=1, max_size=50,
    ),
)
async def test_rate_limit_sliding_window(timestamps, fake_redis, frozen_time):
    user_id = "u1"
    successes = 0
    for t in sorted(timestamps):
        frozen_time.move_to(t)
        try:
            await service._enforce_rate_limit(user_id)
            successes += 1
        except HTTPException as e:
            assert e.status_code == 429
    sorted_ts = sorted(timestamps)
    for i, t in enumerate(sorted_ts):
        in_window = sum(1 for s in sorted_ts[i:] if s - t < 60)
        assert min(in_window, 10) <= 10
```

### 集成测试关键用例

1. **Active set 并发安全**:`asyncio.gather` 并发触发 5 个 `is_active=true` 的创建,断言 DB 内 `is_active=true` 行数恒为 1(部分唯一索引兜底)。
2. **R1.7 active 删除拒绝**:删除 active set → 409,行数不变;先 PUT 置 `is_active=false` 再 DELETE → 204。
3. **R2.9 边界**:连续 POST 200 条 rule 全部成功;第 201 条 → 409,DB 内 count=200。
4. **R3.7 零副作用**:发 size 50.1MB 的请求 → 422 + MinIO 无对象 + DB 无新行。
5. **R3.13 抽取失败**:伪造一份"文件头是 PDF 但 body 是损坏字节"的文件 → 422 + status=failed + MinIO 有上传记录(便于事后排查)。
6. **R3.15 AI 超时**:mock `AIService.check_compliance` 抛 `asyncio.TimeoutError` → 504 + status=failed + error_message='ai_timeout'。
7. **R5.10 跨用户访问**:用户 A 创建检查,用户 B(销售)GET → 403;用户 C(法务)GET → 200。

### E2E 关键路径(Playwright)

1. **管理员旅程**:登录(法务) → /compliance/admin/rule-sets → 创建规则集合 → 添加 5 条规则覆盖 4 种 rule_type → 切换 active。
2. **销售旅程**:登录(销售) → /compliance/check/new → 上传 PDF + 填三个 draft → 提交 → 跳转 /compliance/check/{id} → 看到 violations + 评分 + 复制按钮 → 点「复制」验证 clipboard。
3. **失败兜底**:上传一个文本层为空的 PDF → 看到「合同文件未抽取到可读文本」+「重新检查」按钮。
4. **角色门禁**:销售直接访问 `/compliance/admin/rule-sets` → 后端返回 403 → 前端展示无权限。

---

## Deployment Notes

### 依赖变更

**后端 `backend/requirements.txt` 新增**:

```
pdfplumber>=0.11
python-docx>=1.1
hypothesis>=6.100  # dev 依赖,可放 requirements-dev.txt
```

**Dockerfile 新增系统包(为 .doc 抽取)**:

```dockerfile
# backend/Dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    antiword \
    && rm -rf /var/lib/apt/lists/*
```

> 参考 steering #17:服务器侧热修必须回流到 git。`apt-get install antiword` 在 Dockerfile 写好,**不要**在生产服务器上 `docker exec apt install` 临时打补丁。

> 参考 steering #18:腾讯云长 SSH 会被踢。在 prod 重新 build backend 镜像走 GitHub Actions(`.github/workflows/deploy-prod.yml`),不要 SSH 上去 `docker build`。

### 数据库迁移

```bash
cd backend
alembic revision --autogenerate -m "add compliance tables"
# 检查生成文件:
#   - 创建 3 个 ENUM type
#   - 创建 3 张表
#   - partial unique index uq_compliance_rule_sets_one_active
alembic upgrade head
```

部署流程位置:GitHub Actions `deploy-prod.yml` 在 `docker compose up -d` 之后插入 `docker compose exec backend alembic upgrade head` 步骤(已存在)。

### 共享基础设施风险(steering #20)

本功能**不修改** docker-compose.yml 中 postgres / redis / minio 的服务定义,仅:

- 新增数据库表(由 alembic 自动 apply)
- 在已有 MinIO bucket 内新增路径前缀 `compliance/...`,不需新建 bucket
- 复用 Redis db,key 前缀 `compliance:` 不与既有 key 冲突

CI/CD 推 develop 完全安全。

### 环境变量

本功能**不引入**新环境变量。复用既有的:

- `MINIO_ENDPOINT` / `MINIO_BUCKET`
- `REDIS_URL`
- `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `AI_MODEL` / `AI_TIMEOUT`(`ai_service.py` 已初始化)

### 配置常量(代码内)

放 `backend/app/services/compliance_service.py` 顶部:

```python
COMPLIANCE_FILE_PATH_PREFIX = "compliance"   # MinIO key 前缀
COMPLIANCE_TEXT_MAX_LENGTH = 100_000         # 文本截断上限
COMPLIANCE_RATE_LIMIT_WINDOW = 60            # 频控窗口秒数
COMPLIANCE_RATE_LIMIT_QUOTA = 10             # 窗口内允许的成功请求数
COMPLIANCE_AI_TIMEOUT = 60                   # AI 调用超时
COMPLIANCE_RULES_PER_SET_LIMIT = 200         # 单 rule_set 下规则上限
COMPLIANCE_FILE_SIZE_LIMIT = 50 * 1024 * 1024
COMPLIANCE_FILE_MIME_WHITELIST = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
```

### 缓存清理(steering #6)

写操作必须清缓存:

| 写操作 | 清理 key |
|---|---|
| 创建/更新/删除 rule_set | `compliance:active-rule-set` |
| 切换 is_active | `compliance:active-rule-set` |
| 创建/更新/删除 rule | (本阶段 rules 不缓存,无需清理) |

### 前端构建

无需 `--no-cache` 重建,常规 `docker compose build frontend` 即可(新增页面是新文件,Vite 不会命中旧 chunk)。

---

## Out of Scope(对齐 requirements.md)

- 销售在结果页原地编辑后再次提交
- 检查通过后自动调用 `POST /api/contracts` 发起预审
- AI 生成 `suggested_number`(合同编号建议)
- 合规规则版本化、规则导入/导出
- OCR(纯图片 PDF)、加密 PDF / 受保护 docx
- 除 `.pdf` / `.doc` / `.docx` 外的 Office 格式
- 多语言合规规则(中英文混合规则的语义区分)
- 实时流式输出 AI 检查结果
- 合同详情页内嵌「一键合规检查」入口

---

## Future Considerations

- **第二阶段**:`POST /api/compliance/checks/{check_id}/confirm-and-initiate` 端点,内部调用 `POST /api/contracts`,把本次合规检查的 MinIO 文件转为合同附件。
- **规则版本化**:`compliance_rule_sets` 加 `version` / `parent_id`,支持回滚。
- **OCR**:`TextExtractor` 加 OCR 管线(腾讯云 OCR / PaddleOCR)。
- **RAG**:规则膨胀至 500+ 时,改 vector DB + 检索 top-K 相关规则进 prompt(参考 `aniket-work/autonomous-legal-contract-auditor` 的 Risk Playbook 思路)。
- **整体合规评分细化**:目前是线性扣分,二阶段可改为按 `rule_type` 加权 / 按合同类型动态调整 base score。
- **WebSocket 推送**:本阶段用前端轮询;若检查耗时显著上升,改 socket.io 推 `compliance:check:completed` 事件,沿用 steering #21/#22 的公开路径与 nginx location 约定。
