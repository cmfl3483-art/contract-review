# Requirements Document

## Introduction

本文档描述合同预审看板系统「合规规则 Excel 批量导入」功能的需求。该功能面向管理员用户（法务 / 运营角色），允许其通过下载标准 Excel 模板、填写规则内容后批量上传，一次性将多条合规规则导入到指定规则集合（`compliance_rule_sets`）中，替代逐条手动新建的操作。

功能边界：本 Spec 仅覆盖规则的 Excel 批量导入，不涉及规则集合本身的批量创建、规则的批量导出、或合规检查结果的导入导出。

现有系统技术栈：后端 FastAPI + SQLAlchemy 2.0 (async/asyncpg) + openpyxl，前端 React 19 + TypeScript + Ant Design 6 + TanStack Query 5。本功能在已交付的 `contract-compliance-check` Spec 之上扩展，复用其鉴权约定（写接口仅限 `role ∈ {法务, 运营}`）、规则数量上限约束（每个 rule_set 最多 200 条）以及 `compliance_rules` 表结构。

---

## Glossary

- **System**：合同预审看板系统整体
- **Import_Service**：后端合规规则 Excel 导入服务，负责模板生成、文件解析、校验与批量写入
- **Rule_Excel_Template**：由 Import_Service 动态生成的标准 Excel 文件，包含表头行、数据说明行及枚举约束，供管理员下载后填写规则内容
- **Import_Preview**：上传 Excel 后后端解析出的规则列表预览，不写入数据库，仅供前端展示确认
- **Import_Confirm**：管理员在预览页确认后触发的批量写入操作，将 Import_Preview 中的规则全量写入数据库
- **Admin_User**：`User.role ∈ {法务, 运营}` 的用户，具备规则管理写权限
- **Current_User**：当前已登录的用户
- **Compliance_Rule**：单条合规规则，归属于某一 `compliance_rule_sets` 记录，字段包含 `rule_type`、`title`、`requirement`、`severity`、`order`
- **Rule_Set**：合规规则集合，对应 `compliance_rule_sets` 表中的一条记录，通过 `rule_set_id` 标识
- **RuleTable**：前端规则集合详情页（`/compliance/admin/rule-sets/{rule_set_id}`）中展示规则列表的组件，右上角操作栏包含「新建规则」按钮
- **Preview_Session_Token**：后端在 Import_Preview 响应中返回的一次性令牌，用于关联预览数据与后续确认写入操作，有效期 10 分钟

---

## Requirements

### Requirement 1: 下载 Excel 模板

**User Story:** 作为管理员，我希望下载一份标准 Excel 模板，以便了解每列的含义和枚举约束后正确填写规则内容并批量导入。

#### Acceptance Criteria

1. THE Import_Service SHALL 提供下载模板的接口 `GET /api/compliance/rule-sets/{rule_set_id}/rules/template`，响应 Content-Type 为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，Content-Disposition 为 `attachment; filename*=UTF-8''compliance_rules_template.xlsx`（遵循 RFC 5987 编码，避免中文文件名导致 HTTP 500）。

2. WHEN Import_Service 生成模板文件，THE Import_Service SHALL 使用 openpyxl 动态生成 Excel 文件，文件包含以下列（顺序固定）：`rule_type`（规则类型）、`title`（规则名称）、`requirement`（规则正文）、`severity`（严重程度）、`order`（排序）；第一行为表头行，第二行为说明行（灰色背景，说明每列的取值范围与格式要求），数据从第三行起填写。

3. WHEN Import_Service 生成模板文件，THE Import_Service SHALL 在 `rule_type` 列和 `severity` 列的数据区域（第三行起）设置 Excel 数据验证（Data Validation），`rule_type` 枚举值为 `number,name,description,file`，`severity` 枚举值为 `must,should`，使用户在 Excel 中可通过下拉列表选择。

4. IF Current_User 的 `role` 不属于集合 `{法务, 运营}`，THEN THE Import_Service SHALL 拒绝该请求并返回 HTTP 403 错误，响应体包含权限不足说明。

5. IF 请求中 JWT Token 缺失、格式无效或已过期，THEN THE Import_Service SHALL 返回 HTTP 401 错误，响应体包含认证失败说明。

6. IF 请求中的 `rule_set_id` 在 `compliance_rule_sets` 表中不存在，THEN THE Import_Service SHALL 返回 HTTP 404 错误，响应体说明规范集合不存在。

7. THE RuleTable SHALL 在右上角操作栏（「新建规则」按钮旁）渲染「下载模板」按钮；WHEN Admin_User 点击「下载模板」按钮，THE RuleTable SHALL 通过 `axiosInstance.get(url, { responseType: 'blob' })` 发起请求，并使用 `URL.createObjectURL` + `<a download>` 触发文件下载，不得使用原生 `<a href>` 直接导航（遵循项目约定 #9，避免 401）。

---

### Requirement 2: 上传 Excel 并获取解析预览

**User Story:** 作为管理员，我希望上传填写好的 Excel 文件后先看到解析出的规则列表预览，确认内容无误后再提交写入，以便在批量导入前发现并修正错误。

#### Acceptance Criteria

1. THE Import_Service SHALL 提供上传预览接口 `POST /api/compliance/rule-sets/{rule_set_id}/rules/import/preview`，以 `multipart/form-data` 形式接收字段 `file`（必填，UploadFile，MIME 类型必须为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，文件大小 ≤ 5 MB）。

2. WHEN Import_Service 接收到合法的 Excel 文件，THE Import_Service SHALL 使用 openpyxl 解析文件，跳过第一行（表头行）和第二行（说明行），从第三行起逐行读取数据，将每行解析为一条候选 Compliance_Rule 记录（包含 `rule_type`、`title`、`requirement`、`severity`、`order` 字段）。

3. WHEN Import_Service 解析 Excel 文件，THE Import_Service SHALL 对每行数据执行以下校验：
   - `rule_type` 取值必须属于集合 `{number, name, description, file}`
   - `title` 去除首尾空白后长度为 1 至 100 字符
   - `requirement` 去除首尾空白后长度为 1 至 2000 字符
   - `severity` 取值必须属于集合 `{must, should}`，缺省时默认为 `must`
   - `order` 为整数，缺省时默认为 `0`；若填写了非整数值则视为校验失败

4. IF Excel 文件中任意一行数据校验失败，THEN THE Import_Service SHALL 中止解析，不生成 Import_Preview，不写入任何数据，返回 HTTP 422 错误，响应体包含所有校验失败行的行号（从第三行起计为第 1 条数据，行号以 Excel 实际行号表示）及每行的失败原因描述。

5. IF Excel 文件解析后有效数据行数为 0（文件仅含表头行和说明行，或第三行起全为空行），THEN THE Import_Service SHALL 返回 HTTP 422 错误，响应体说明文件中未包含有效数据行。

6. IF Excel 文件解析后有效数据行数超过 200 条，THEN THE Import_Service SHALL 返回 HTTP 422 错误，响应体说明单次导入最多 200 条规则。

7. WHEN Import_Service 完成全量校验且所有行均通过，THE Import_Service SHALL 生成 Import_Preview，并在响应体中返回：`preview_session_token`（Preview_Session_Token，有效期 10 分钟）、`rules`（解析出的规则列表，每条包含 `row_number`、`rule_type`、`title`、`requirement`、`severity`、`order`）、`total_count`（有效数据行数）。

8. IF 当前 Rule_Set 已有规则数量与本次导入数量之和超过 200 条，THEN THE Import_Service SHALL 返回 HTTP 409 错误，响应体说明导入后总规则数将超过 200 条上限，并提示当前已有规则数量与本次导入数量。

9. IF Current_User 的 `role` 不属于集合 `{法务, 运营}`，THEN THE Import_Service SHALL 拒绝该请求并返回 HTTP 403 错误，响应体包含权限不足说明，且不解析文件、不写入任何数据。

10. IF 请求中 JWT Token 缺失、格式无效或已过期，THEN THE Import_Service SHALL 返回 HTTP 401 错误，响应体包含认证失败说明。

11. IF 请求中的 `rule_set_id` 在 `compliance_rule_sets` 表中不存在，THEN THE Import_Service SHALL 返回 HTTP 404 错误，响应体说明规范集合不存在，且不解析文件、不写入任何数据。

12. IF 上传文件的 MIME 类型不为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，或文件大小超过 5 MB，THEN THE Import_Service SHALL 返回 HTTP 422 错误，响应体说明触发限制的字段及其约束，且不解析文件、不写入任何数据。

13. THE RuleTable SHALL 在右上角操作栏（「新建规则」按钮旁）渲染「批量导入」按钮；WHEN Admin_User 点击「批量导入」按钮，THE RuleTable SHALL 展示文件上传弹窗，支持选择 `.xlsx` 格式文件并调用预览接口；WHEN 预览接口返回成功，THE RuleTable SHALL 关闭上传弹窗并展示预览确认弹窗，显示解析出的规则列表（含行号、rule_type、title、severity、order 列）及总条数。

---

### Requirement 3: 确认导入并批量写入

**User Story:** 作为管理员，我希望在预览确认页核对规则列表无误后点击「确认导入」，由系统将全部规则一次性写入数据库，以便完成批量导入操作。

#### Acceptance Criteria

1. THE Import_Service SHALL 提供确认导入接口 `POST /api/compliance/rule-sets/{rule_set_id}/rules/import/confirm`，请求体为 JSON，包含字段 `preview_session_token`（必填，字符串，对应 Requirement 2 第 7 条返回的 Preview_Session_Token）。

2. WHEN Import_Service 接收到确认导入请求，THE Import_Service SHALL 校验 `preview_session_token` 的有效性（存在且未过期）；IF `preview_session_token` 不存在或已过期（超过 10 分钟），THEN THE Import_Service SHALL 返回 HTTP 422 错误，响应体说明预览会话已过期，需重新上传 Excel 文件。

3. WHEN Import_Service 校验 `preview_session_token` 有效，THE Import_Service SHALL 在单个数据库事务中执行以下操作：将 Preview_Session_Token 关联的全部候选 Compliance_Rule 记录批量插入 `compliance_rules` 表，并同步更新所属 Rule_Set 的 `updated_at` 字段；事务提交成功后立即使 `preview_session_token` 失效（不可重复使用）。

4. IF 数据库事务执行过程中发生任何错误，THEN THE Import_Service SHALL 回滚整个事务，不写入任何 Compliance_Rule 数据，不更新 Rule_Set 的 `updated_at`，并返回 HTTP 500 错误，响应体包含失败说明。

5. IF 在确认导入时（事务执行前）Rule_Set 已有规则数量与待写入数量之和超过 200 条（并发写入导致的竞态），THEN THE Import_Service SHALL 回滚事务，返回 HTTP 409 错误，响应体说明导入后总规则数将超过 200 条上限，且不写入任何数据。

6. WHEN Import_Service 完成批量写入，THE Import_Service SHALL 在响应体中返回：`imported_count`（成功写入的规则条数）、`rule_set_id`（所属规则集合 ID）。

7. IF Current_User 的 `role` 不属于集合 `{法务, 运营}`，THEN THE Import_Service SHALL 拒绝该请求并返回 HTTP 403 错误，响应体包含权限不足说明，且不写入任何数据。

8. IF 请求中 JWT Token 缺失、格式无效或已过期，THEN THE Import_Service SHALL 返回 HTTP 401 错误，响应体包含认证失败说明。

9. IF 请求中的 `rule_set_id` 在 `compliance_rule_sets` 表中不存在，THEN THE Import_Service SHALL 返回 HTTP 404 错误，响应体说明规范集合不存在，且不写入任何数据。

10. WHEN Admin_User 在预览确认弹窗中点击「确认导入」按钮，THE RuleTable SHALL 调用确认导入接口；WHEN 接口返回成功，THE RuleTable SHALL 关闭预览确认弹窗，刷新规则列表（使 TanStack Query 对应 queryKey 失效），并展示成功提示（「成功导入 N 条规则」）。

11. WHEN Admin_User 在预览确认弹窗中点击「取消」按钮，THE RuleTable SHALL 关闭预览确认弹窗，不调用确认导入接口，不写入任何数据，Preview_Session_Token 保持有效直至自然过期。

---

### Requirement 4: 错误处理与用户反馈

**User Story:** 作为管理员，我希望在上传或导入过程中遇到错误时，能看到清晰的错误提示（包含具体行号和原因），以便快速定位并修正 Excel 文件中的问题。

#### Acceptance Criteria

1. WHEN Import_Service 返回 HTTP 422 错误且包含行级校验失败信息，THE RuleTable SHALL 在上传弹窗中展示错误详情列表，每条错误显示 Excel 行号及对应的失败原因（如「第 5 行：rule_type 取值 'clause' 不合法，必须为 number / name / description / file 之一」）。

2. WHEN Import_Service 返回 HTTP 409 错误（规则数量超限），THE RuleTable SHALL 在上传弹窗中展示提示，说明当前已有规则数量、本次导入数量及 200 条上限，引导管理员减少导入条数或先删除部分现有规则。

3. WHEN Import_Service 返回 HTTP 422 错误（预览会话过期），THE RuleTable SHALL 关闭预览确认弹窗，展示提示「预览已过期，请重新上传 Excel 文件」，引导管理员重新操作。

4. WHEN Import_Service 返回 HTTP 500 错误（事务失败），THE RuleTable SHALL 展示提示「导入失败，数据未写入，请稍后重试」。

5. WHILE 确认导入接口请求进行中，THE RuleTable SHALL 将「确认导入」按钮置为 loading 状态，防止重复提交。

6. WHILE 预览接口请求进行中，THE RuleTable SHALL 将上传弹窗的「上传并预览」按钮置为 loading 状态，防止重复提交。
