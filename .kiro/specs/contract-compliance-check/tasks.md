# Implementation Plan: 合同合规检查(第一阶段)

## Overview

按照「数据层 → 服务层 → 路由层 → 前端 → 测试」的顺序增量交付。每条任务严格对应 design.md 的组件设计与 requirements.md 的条款,不引入额外抽象。Property 测试(P1~P17)就近放在被测组件后,严格遵守 steering 约定 #1(前端 axios 实例)、#2(异常处理器先注册)、#3(SQLEnum values_callable)、#8(UUID 比较 str() 包一层)。

## Tasks

- [x] 1. 后端依赖与数据模型基线
  - [x] 1.1 更新依赖与 Dockerfile
    - 在 `backend/requirements.txt` 追加 `pdfplumber>=0.11`、`python-docx>=1.1`、`hypothesis>=6.100`(后两者亦可放 dev)
    - 在 `backend/Dockerfile` 追加 `apt-get install -y --no-install-recommends antiword`(用于 `.doc` 抽取),并清理 apt 缓存
    - _Requirements: 3.1, 3.13_

  - [x] 1.2 新建 ORM 模型 `backend/app/models/compliance.py`
    - 定义 `RuleType`(number/name/description/file)、`RuleSeverity`(must/should)、`ComplianceCheckStatus`(pending/completed/failed)三个 `str, enum.Enum`
    - 定义 `ComplianceRuleSet`、`ComplianceRule`、`ComplianceCheckResult` 三张表与字段、索引、关系
    - 所有 `SQLEnum` 列必须使用 `values_callable=lambda x: [e.value for e in x]`(steering #3)
    - 在 `backend/app/models/__init__.py` 中按需 export 新模型,不修改现有模型类
    - _Requirements: 1.1, 1.2, 2.1, 3.10, 6.6, 6.7_

  - [x] 1.3 新建 Alembic 迁移 `add_compliance_tables`
    - 创建 3 个 ENUM type、3 张表、partial unique index `uq_compliance_rule_sets_one_active`(`WHERE is_active = true`)、`ix_compliance_rules_set_id_order`、`ix_compliance_check_results_requester_time`、`ix_compliance_check_results_status`
    - `compliance_check_results` 不含指向 `contracts` 表的外键
    - 提供完整 `downgrade()`(逆序 drop index、table、type)
    - _Requirements: 1.2, 1.5, 2.9, 6.7_

- [x] 2. Pydantic schemas 与服务层基础设施
  - [x] 2.1 新建 `backend/app/schemas/compliance.py`
    - `RuleSet` / `Rule` / `CheckResult` 的请求与响应模型,字段与 design.md「API Interfaces」节一致(含 `rule_count`、`rule_title`、`compliance_score`、`text_truncated`、`error_message`)
    - 字符串字段 `min_length` / `max_length` 严格匹配 requirements 约束(name 1-100、description 0-1000、rule.requirement 1-2000、name_draft 0-200 等)
    - 不包含 `suggested_number` / `contract_text` 字段
    - _Requirements: 1.1, 1.11, 2.1, 2.6, 3.1, 3.7, 3.11, 5.1, 5.2_

  - [x] 2.2 新建 `backend/app/services/text_extractor.py`
    - 定义 `TextExtractionError`,实现 `TextExtractor.extract(file_data, mime_type) -> tuple[str, bool]`
    - PDF 分支用 `pdfplumber` 逐页 `extract_text()`(加密 PDF 抛 `TextExtractionError`)
    - `.docx` 分支用 `python-docx` 拼段落与表格文本
    - `.doc` 分支用 `subprocess.run(["antiword", tmpfile])`,失败抛 `TextExtractionError`
    - 抽取后超过 100000 字符则截断并设 `text_truncated = true`
    - _Requirements: 3.2, 3.13, 3.14_

  - [x] 2.3* 单元测试 `tests/services/test_text_extractor.py`
    - 三种 MIME 各一个最小可读样本 → 抽取成功、不截断
    - 损坏 PDF / 加密 PDF / 空文本层 PDF → 分别命中 `TextExtractionError` 与 strip 后空字符串
    - >100000 字符样本 → 返回 `text_truncated=true` 且文本长度恰为 100000
    - _Requirements: 3.13, 3.14_

- [x] 3. AIService 扩展与合规评分
  - [x] 3.1 在 `backend/app/services/ai_service.py` 新增 `check_compliance` 方法
    - 入参:`rules`、`extracted_text`、`text_truncated`、`number_draft`、`name_draft`、`description_draft`
    - 无规则集时走 `_fallback_no_rules`,直接返回空 violations 与 score=100(不调用 LLM)
    - 调用 LLM 使用 `response_format={"type": "json_object"}`、`timeout=60`、最多重试 1 次
    - 超时直接抛 `asyncio.TimeoutError`;一般错误抛 `ComplianceAIError`;两次解析失败抛 `ComplianceAIInvalidResponseError`
    - System Prompt 严格按 design.md 描述构造,显式禁止输出 `suggested_number` 与 `compliance_score`
    - _Requirements: 4.1, 4.2, 4.10, 4.11, 4.12_

  - [x] 3.2 实现 `_postprocess` 与 `_compute_compliance_score`
    - `_postprocess`:按 `rule_id` 过滤、强制 `location` 与 `rule_type` 一致、用规则真值覆写 `severity`、字段初稿空时丢弃对应 location 的 violation、对 `excerpt`/`description`/`suggestion` 截断到 500 字符
    - `suggested_name` 兜底:LLM 空时回落 `name_draft`,再回落 `extracted_text` 前 200 字符去换行,最终保证 1-200 字符
    - `_compute_compliance_score`:`max(0, min(100, 100 - 10*must - 2*should))`
    - _Requirements: 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.13_

  - [x] 3.3* Hypothesis 属性测试 `tests/services/test_ai_postprocess_properties.py`
    - **Property 3: violations 中 rule_id 必属于本次集合 / Validates: Requirements 4.3**
    - **Property 4: violations.location 与规则 rule_type 一致 / Validates: Requirements 4.3**
    - **Property 5: violations.severity 与规则 severity 一致 / Validates: Requirements 4.3**
    - **Property 6: suggested_name 强约束 (1..200) / Validates: Requirements 4.4**
    - **Property 7: suggested_description 弱约束 (0..2000) / Validates: Requirements 4.4**
    - **Property 8: 字段初稿空时不输出对应 location 违规 / Validates: Requirements 4.6, 4.7, 4.8**
    - 复用 design.md「Hypothesis 落地示例」中的 `rule_set_strategy` + `llm_violations` 策略
    - _Requirements: 4.3, 4.4, 4.6, 4.7, 4.8_

  - [x] 3.4* Hypothesis 属性测试 `tests/services/test_compliance_score_properties.py`
    - **Property 11: compliance_score 算术属性 / Validates: Requirements 4.13**
    - 用 `must_count`、`should_count` 任意取样,断言 `score == max(0, min(100, 100-10*must-2*should))` 且空 violations → 100
    - _Requirements: 4.13_

- [x] 4. ComplianceService 业务编排
  - [x] 4.1 新建 `backend/app/services/compliance_service.py` 骨架与常量
    - 顶部声明 `COMPLIANCE_FILE_PATH_PREFIX="compliance"`、`COMPLIANCE_TEXT_MAX_LENGTH=100_000`、`COMPLIANCE_RATE_LIMIT_WINDOW=60`、`COMPLIANCE_RATE_LIMIT_QUOTA=10`、`COMPLIANCE_AI_TIMEOUT=60`、`COMPLIANCE_RULES_PER_SET_LIMIT=200`、`COMPLIANCE_FILE_SIZE_LIMIT=50*1024*1024`、`COMPLIANCE_FILE_MIME_WHITELIST`
    - `ComplianceService.__init__(self, ai_service, text_extractor)`,在 `app.main` 中以单例注入
    - 实现 `_resolve_active_rule_set`(读 Redis `compliance:active-rule-set`,miss 则 SELECT)与 `_enforce_rate_limit`(`INCR` + `EXPIRE 60`,>10 抛 429)
    - _Requirements: 3.5, 3.12_

  - [x] 4.2 RuleSet CRUD:`create_rule_set` / `list_rule_sets` / `update_rule_set` / `delete_rule_set`
    - 创建/更新带 `is_active=true` 时,**同一事务**先 `UPDATE compliance_rule_sets SET is_active=false WHERE id != target`,再 `is_active=true WHERE id = target`,最后 commit
    - `delete` 在记录 `is_active=true` 时抛 409;否则级联删 rules
    - 列表查询附带 `rule_count` 子查询;按 `created_at DESC` 排
    - 写操作完成后 `redis_client.delete("compliance:active-rule-set")`(steering #6)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.10_

  - [x] 4.3 Rule CRUD:`create_rule` / `list_rules` / `update_rule` / `delete_rule`
    - 新增前 `SELECT COUNT(*)` 判断 `>=200` 抛 409;同事务 `UPDATE compliance_rule_sets SET updated_at=now() WHERE id=:rule_set_id`
    - 列表按 `rule_type ASC, order ASC, created_at ASC` 排序
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.8, 2.9_

  - [x] 4.4 `perform_check` 主流程
    - 顺序:`_enforce_rate_limit` → MIME/size 校验 → 解析 `rule_set_id`(空则取 active set,无 active 抛 409)→ MinIO 上传到 `compliance/{user_id}/{check_id}/{filename}` → 插入 `status=pending` 行 → `text_extractor.extract` → AIService.check_compliance → 在同一事务内 `UPDATE` 终态字段(violations / suggested_* / compliance_score / completed_at)
    - 文件参数错误时**严格保证零副作用**:不上传 MinIO、不写库、不调 AI(对应 P9)
    - 抽取异常 / 空文本 / AI 超时 / AI 错误 / AI JSON 解析失败 分别更新 `status=failed`、`error_message` 写入对应字符串,各自抛对应 HTTPException(422/422/504/502 与 200+failed)
    - **完成态使用 UUID 字段比较时必须 `str(...) == str(...)`**(steering #8)
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.10, 3.11, 3.12, 3.13, 3.14, 3.15, 3.16, 4.10_

  - [x] 4.5 `recheck` / `get_check` / `list_checks`
    - `recheck`:依据 `check_id` 取出原行,从 MinIO 拉 `file_storage_key`(失败抛 410 `compliance_file_lost`),复用原 drafts 与 rule_set_id 重做抽取 + AI,事务内将原行 status 重置为 pending → 终态
    - `get_check`:角色 ∈ {销售} 时强制 `requested_by == current_user.id`(用 `str()` 比较),否则 403
    - `list_checks`:角色 ∈ {销售} 仅返回本人记录;法务/运营返回全集;支持 `status` 过滤、`page`/`page_size`(上限 100)
    - _Requirements: 5.1, 5.2, 5.9, 5.10, 5.11, 5.12_

- [x] 5. 路由层 `routes/compliance.py`
  - [x] 5.1 路由骨架与权限 helpers
    - 新建 `backend/app/routes/compliance.py`,使用 `APIRouter(prefix="/api/compliance", tags=["compliance"])`
    - 定义 `require_admin(user)`(role ∈ {法务, 运营})与 `require_compliance_user(user)`(role ∈ {销售, 法务, 运营})
    - 在 `backend/app/main.py` 中通过 `app.include_router(compliance.router)` 注册;**确认异常处理器在中间件之前注册**(steering #2)
    - _Requirements: 1.8, 1.9, 2.7, 3.8, 3.9, 6.5_

  - [x] 5.2 规则集合接口(R1)
    - `POST/GET/GET-detail/PUT/DELETE /api/compliance/rule-sets[/{id}]` 共 5 个路由,调用 `compliance_service` 对应方法
    - 422 字段约束错误统一以 `compliance_validation_failed` 错误码返回
    - 删除 active set 返回 409 `compliance_active_rule_set_in_use`
    - _Requirements: 1.1, 1.3, 1.4, 1.6, 1.7, 1.10, 1.11_

  - [x] 5.3 规则接口(R2)
    - `POST/GET /api/compliance/rule-sets/{rule_set_id}/rules` 与 `PUT/DELETE /api/compliance/rules/{rule_id}` 共 4 个路由
    - 200 条上限触发返回 409 `compliance_rules_quota_exceeded`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 2.8, 2.9_

  - [x] 5.4 合规检查接口(R3 + R5)
    - `POST /api/compliance/checks`(`multipart/form-data`,fields:file/number_draft/name_draft/description_draft/rule_set_id)
    - `GET /api/compliance/checks`、`GET /api/compliance/checks/{check_id}`、`POST /api/compliance/checks/{check_id}/recheck`
    - 响应体严格按 design.md「API Interfaces」结构,含 `compliance_score`、`text_truncated`、`error_message`,**不含** `suggested_number` 与 `contract_text`
    - _Requirements: 3.1, 3.7, 3.11, 5.1, 5.2, 5.9_

- [x] 6. 后端集成测试与并发性质
  - [x] 6.1* 集成测试 `tests/routes/test_compliance_rule_sets.py`
    - 覆盖 R1.1/1.3/1.4/1.6/1.7/1.8/1.9/1.10/1.11 全部分支(401/403/404/409/422 与正常流)
    - **Property 1: Active Rule Set 唯一性 / Validates: Requirements 1.2, 1.5**
    - 用 `asyncio.gather` 并发 5 个 `is_active=true` 创建,断言最终 `is_active=true` 行数恒为 1
    - **Property 14: 解耦不变量 / Validates: Requirements 6.6, 6.7**
    - 断言 `Contract`/`Attachment`/`Review`/`Comment`/`AISummary`/`Notification` 类的 `__table__.columns.keys()` 与基线快照完全一致
    - _Requirements: 1.2, 1.5, 1.7, 6.6, 6.7_

  - [x] 6.2* 集成测试 `tests/routes/test_compliance_rules.py`
    - **Property 2: 单 Rule Set 规则数上限 / Validates: Requirements 2.9**
    - 连续插入 200 条 → 全部成功;第 201 条 → 409 且 DB 内仍为 200
    - 覆盖 R2.6/2.7/2.8 各分支
    - _Requirements: 2.5, 2.6, 2.7, 2.8, 2.9_

  - [x] 6.3* 集成测试 `tests/routes/test_compliance_checks.py`
    - **Property 9: 文件参数错误零副作用 / Validates: Requirements 3.7**
    - 用 50.1 MB / 错误 MIME / draft 超长 各一种构造请求 → 422,断言 MinIO mock 无 `upload_file_data` 调用、DB 无新行、AI mock 无调用
    - **Property 12: status 状态机单调 / Validates: Requirements 3.2, 3.3, 3.13, 3.14, 3.15, 3.16**
    - 跑过完整 `pending → completed` 与 `pending → failed`(分别 mock 抽取异常 / AI 超时 / AI 错误 / AI JSON 解析失败)
    - **Property 13: 数据范围隔离 / Validates: Requirements 5.10, 5.12**
    - 用户 A(销售)创建检查 → 用户 B(销售)GET 单条 → 403;用户 C(法务)GET 单条 → 200;A 调列表只见己,C 调列表见全集
    - 覆盖 R3.5(无 active)/3.6(rule_set_id 不存在)/3.8/3.9/4.10(无规则跳过 LLM)
    - _Requirements: 3.2, 3.3, 3.5, 3.6, 3.7, 3.8, 3.13, 3.14, 3.15, 3.16, 4.10, 5.10, 5.12_

  - [x] 6.4* Hypothesis 属性测试 `tests/services/test_rate_limit_property.py`
    - **Property 10: 频控严格上界 / Validates: Requirements 3.12**
    - 复用 design.md「P10: 频控滑动窗口」示例,使用 `fakeredis` + `freezegun`,任意时间戳序列下 60s 窗口成功数 ≤ 10
    - _Requirements: 3.12_

- [x] 7. 后端检查点
  - 跑 `cd backend && pytest`,确保所有后端单元 + property + 集成测试全绿;若有失败,优先定位根因而非堆补丁(参考 steering「失败循环识别」)
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. 前端类型与 API 客户端
  - [x] 8.1 新建 `frontend/src/types/compliance.ts`
    - 定义 `RuleType`、`RuleSeverity`、`ComplianceCheckStatus` 字面量联合
    - 定义 `RuleSet`、`RuleSetDetail`、`Rule`、`Violation`、`ComplianceCheckResult`、`ComplianceCheckSummary`、`CreateRuleSetDto`、`UpdateRuleSetDto`、`CreateRuleDto`、`UpdateRuleDto` 等类型
    - _Requirements: 5.1, 5.2_

  - [x] 8.2 新建 `frontend/src/hooks/useCompliance.ts`
    - 实现 RuleSet / Rule / Check 的 useQuery + useMutation hooks(共 13 个)
    - 实现 `useComplianceCheckPolling(checkId, enabled)`,`refetchInterval` 在 `data?.status === 'pending'` 时返回 2000,否则 false
    - **所有请求必须使用 `frontend/src/utils/axios` 实例**(steering #1),禁止直接 `import axios from 'axios'`
    - 写操作成功后 `queryClient.invalidateQueries(['compliance', ...])`
    - _Requirements: 1.3, 1.4, 2.2, 2.3, 5.1, 5.2, 5.6_

- [x] 9. 前端业务组件
  - [x] 9.1 错误文案映射 `frontend/src/components/Compliance/ErrorMessageMap.ts`
    - 实现 `COMPLIANCE_ERROR_MESSAGES` 与 `getComplianceErrorText(errorMessage)`,对未知 key 返回 `AI 检查失败:{x}`,对空值/null 返回 `AI 检查失败`
    - _Requirements: 5.8_

  - [x] 9.2 表单与列表组件
    - `ComplianceCheckForm.tsx`:Antd `Upload` 限制 `.pdf,.doc,.docx` 与 50MB、三个 `TextArea`(maxLength 100/200/2000)、`RuleSetSelector` 默认显示 active
    - `ComplianceCheckList.tsx`:列表渲染 `name_draft`、`rule_set_name`、`file_name`、`text_truncated`、`violation_count`、`compliance_score`、`requested_at`,支持 `status` 过滤
    - `RuleSetSelector.tsx`:复用 `useRuleSets`,active 项加「当前生效」标
    - _Requirements: 3.1, 3.7, 5.2_

  - [x] 9.3 检查结果展示组件
    - `TruncatedNotice.tsx`:`text_truncated=true` 时展示「文件过长已截断,可能影响检查准确性」
    - `ComplianceSuggestions.tsx`:两个独立区块展示 `suggested_name`、`suggested_description`,各自一个「复制到剪贴板」按钮(`navigator.clipboard.writeText`,纯文本)
    - `ViolationItem.tsx` / `ViolationList.tsx`:按 `severity` 优先(must>should)、`location` 次序(number>name>description>file)排序;严重程度红/黄标签;location 中文映射
    - 顶部展示 `compliance_score` 「合规评分:XX/100」+ 风险等级颜色标签(≥90 绿 / 70-89 蓝 / 50-69 黄 / <50 红);`status != 'completed'` 时不渲染评分
    - _Requirements: 5.3, 5.4, 5.5, 5.7_

  - [x] 9.4 规则管理组件
    - `RuleSetTable.tsx`、`RuleSetCreateModal.tsx`、`RuleSetMetaForm.tsx`、`RuleTable.tsx`、`RuleCreateEditDrawer.tsx`
    - `RuleCreateEditDrawer` 表单包含 `rule_type`、`title`、`requirement`、`severity`、`order`,字段长度限制对齐 schemas
    - _Requirements: 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

- [x] 10. 前端页面与路由
  - [x] 10.1 新建 5 个页面
    - `pages/Compliance/ComplianceListPage.tsx`(角色 ∈ {法务, 运营} 额外渲染「规则管理」入口与「全部合规检查」视图)
    - `pages/Compliance/ComplianceCheckNewPage.tsx`(提交后 navigate 到 detail 页)
    - `pages/Compliance/ComplianceCheckDetailPage.tsx`(根据 `status` 渲染 pending/completed/failed,启动 `useComplianceCheckPolling`,Detail 页 `useEffect` 在累计 90s 后置 `enabled=false` 停止轮询)
    - `pages/Compliance/admin/RuleSetListPage.tsx`、`pages/Compliance/admin/RuleSetDetailPage.tsx`
    - _Requirements: 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 6.1, 6.2, 6.4_

  - [x] 10.2 在 `App.tsx` 注册新路由 + `MainLayout.tsx` 顶部导航
    - 添加 `/compliance`、`/compliance/check/new`、`/compliance/check/:checkId`、`/compliance/admin/rule-sets`、`/compliance/admin/rule-sets/:ruleSetId` 五条路由,匹配兜底保留
    - 顶部导航追加「合规审查」一级入口,链接 `/compliance`,所有已登录用户可见
    - 未登录访问 `/compliance/...` 走现有钉钉登录回跳逻辑(无需改 `App.tsx` 已有的 token 注入)
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 11. 前端 Property 测试与 E2E
  - [x] 11.1* 前端 vitest + fast-check `frontend/src/components/Compliance/__tests__/ErrorMessageMap.property.test.ts`
    - **Property 15: 错误文案 fallback 完备 / Validates: Requirements 5.8**
    - 任意字符串 / null / undefined → `getComplianceErrorText` 必返回非空中文字符串
    - _Requirements: 5.8_

  - [x] 11.2* 前端 vitest `useComplianceCheckPolling` `frontend/src/hooks/__tests__/useComplianceCheckPolling.test.tsx`
    - **Property 16: 轮询自动停止 / Validates: Requirements 5.6**
    - mock 接口先返回 `pending`,90s 内若 `status` 仍为 `pending` 则 detail 页置 `enabled=false`,后续不再请求;若中途变为 `completed` 则 `refetchInterval` 立即返回 false
    - _Requirements: 5.6_

  - [x] 11.3* Playwright E2E `frontend/tests/e2e/compliance.spec.ts`
    - 管理员旅程:登录(法务) → 创建规则集合 → 添加 5 条规则覆盖 4 种 rule_type → 切换 active
    - 销售旅程:登录(销售) → 上传 PDF + 三 draft → 提交 → 跳转 detail → 看到 violations + 评分 + 复制按钮
    - **Property 17: 复制不污染剪贴板格式 / Validates: Requirements 5.4** — 通过 `page.evaluate(() => navigator.clipboard.readText())` 断言剪贴板内容为纯文本且与 `suggested_name`/`suggested_description` 一致
    - 失败兜底:上传文本层为空的 PDF → 看到「合同文件未抽取到可读文本」+「重新检查」按钮
    - 角色门禁:销售直接访问 `/compliance/admin/rule-sets` → 后端 403 → 前端展示无权限
    - _Requirements: 5.3, 5.4, 5.7, 5.8, 5.9, 6.4_

- [x] 12. 最终检查点
  - 跑 `cd backend && pytest` 与 `cd frontend && npm run test:e2e`,确保全部测试通过
  - 验证 alembic 在干净 DB 上 `upgrade head` + `downgrade base` 双向通过
  - 通过 `getDiagnostics` 复查所有改动文件无类型/lint 错误
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- 标记 `*` 的子任务为可选测试任务;核心实现任务从不带 `*`
- 每条任务结尾以 `_Requirements: X.Y_` 形式标注覆盖的 requirement 子条款,实现时若发现条款未被任何任务覆盖应回头补任务
- Property 测试任务严格对齐 design.md「Correctness Properties」节的 P1~P17,任务标题包含 Property 序号便于追溯
- 频繁参照的 steering 约定:#1(前端 axios 实例)、#2(异常处理器先注册)、#3(SQLEnum values_callable)、#6(写操作清缓存)、#8(UUID 比较 str() 包一层)、#9(鉴权下载用 axios blob,本 spec 不涉及但若加文件下载需注意)
- 检查点任务用于阶段性验收,失败时优先排查根因而非堆补丁

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "2.1", "8.1", "9.1"] },
    { "id": 1, "tasks": ["1.3", "2.2", "3.1", "8.2", "11.1"] },
    { "id": 2, "tasks": ["2.3", "3.2", "4.1", "9.2", "9.3", "9.4"] },
    { "id": 3, "tasks": ["3.3", "3.4", "4.2", "10.1", "11.2"] },
    { "id": 4, "tasks": ["4.3", "10.2"] },
    { "id": 5, "tasks": ["4.4"] },
    { "id": 6, "tasks": ["4.5", "5.1"] },
    { "id": 7, "tasks": ["5.2"] },
    { "id": 8, "tasks": ["5.3"] },
    { "id": 9, "tasks": ["5.4"] },
    { "id": 10, "tasks": ["6.1", "6.2", "6.3", "6.4", "11.3"] }
  ]
}
```
