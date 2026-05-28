# Implementation Plan: 合规规则 Excel 批量导入

## Overview

在已交付的 `contract-compliance-check` Spec 之上扩展，零侵入既有合规检查逻辑。后端新增独立的 `compliance_import_service.py`，在 `routes/compliance.py` 追加 3 个路由；前端新增 `RuleImportModal.tsx`，在 `types/compliance.ts` 追加类型、`useCompliance.ts` 追加 3 个 hooks，并在 `RuleTable.tsx` 追加操作按钮。

## Tasks

- [x] 1. 后端依赖与类型声明
  - [x] 1.1 在 `backend/requirements.txt` 的 `python-docx>=1.1` 之后追加 `openpyxl>=3.1,<4.0`
    - 显式声明版本范围，避免 pdfplumber 间接依赖版本漂移
    - _Requirements: 设计文档「改动范围总览」_

- [x] 2. 后端核心服务
  - [x] 2.1 新建 `backend/app/services/compliance_import_service.py`，实现 `generate_template` 方法
    - 使用 openpyxl 生成含表头行（加粗）、说明行（灰色背景 D9D9D9）的 xlsx 文件
    - 在 `rule_type` 列（A3:A1048576）和 `severity` 列（D3:D1048576）设置 Excel Data Validation 下拉列表
    - 列顺序固定：`rule_type`、`title`、`requirement`、`severity`、`order`
    - 返回 `bytes`，供路由层包装为 `StreamingResponse`
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 2.2 在 `compliance_import_service.py` 实现 `_parse_excel` 私有方法
    - 跳过第 1-2 行（表头行和说明行），从第 3 行起逐行读取，跳过全空行
    - 对每行执行全量字段校验：`rule_type` 枚举、`title` 长度 1-100、`requirement` 长度 1-2000、`severity` 枚举（缺省默认 `must`）、`order` 整数（缺省默认 `0`）
    - 收集所有行的错误，返回 `(parsed_rows, errors)` 元组；错误项格式 `{ row_number, field, message }`
    - _Requirements: 2.2, 2.3, 2.4_

  - [ ]* 2.3 为 `_parse_excel` 编写 Property 1 测试（Round-Trip）
    - **Property 1: Excel 解析 Round-Trip**
    - 生成合法规则列表 → 写入 xlsx → `_parse_excel` 解析 → 断言五个字段与原始输入完全一致
    - **Validates: Requirements 2.2, 2.3, 2.7**

  - [ ]* 2.4 为 `_parse_excel` 编写 Property 2 测试（非法字段校验拒绝）
    - **Property 2: 非法字段校验拒绝**
    - 对 `rule_type`/`title`/`requirement`/`severity`/`order` 各字段分别注入非法值，断言 `errors` 包含对应行号和字段，且 `parsed_rows` 不含该行
    - **Validates: Requirements 2.3, 2.4**

  - [x] 2.5 在 `compliance_import_service.py` 实现 `parse_and_preview` 异步方法
    - 按顺序执行：MIME/大小校验 → rule_set 存在性校验 → `_parse_excel` → 空行校验 → 行级错误汇总 → 超 200 条校验 → 与现有规则数合并校验（409）
    - 全量通过后生成 `secrets.token_urlsafe(32)` token，以 `compliance:import:preview:{token}` 为 key 存入 Redis（TTL 600s，JSON 序列化规则列表）
    - 返回 `{ preview_session_token, rules, total_count }`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [x] 2.6 在 `compliance_import_service.py` 实现 `confirm_import` 异步方法
    - 从 Redis 读取 token（不存在/过期 → 422 `import_preview_expired`）
    - 再次校验 rule_set 存在性及规则数量上限（竞态保护，409）
    - 在单个数据库事务中批量 INSERT `compliance_rules` + UPDATE `rule_set.updated_at`；事务 commit 后立即 `redis_client.delete(redis_key)`（一次性令牌）
    - 事务异常时 rollback 并返回 500 `import_transaction_failed`
    - 返回 `{ imported_count, rule_set_id }`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 2.7 为 `confirm_import` 编写 Property 4 测试（写入数量一致性）
    - **Property 4: 确认导入写入数量一致性**
    - 构造含 N 条规则的合法预览会话，调用 `confirm_import`，断言 DB 中该 rule_set 规则数恰好增加 N，且 `imported_count == N`
    - **Validates: Requirements 3.3, 3.6**

  - [ ]* 2.8 为 `confirm_import` 编写 Property 5 测试（Token 一次性语义）
    - **Property 5: Preview_Session_Token 一次性语义**
    - 第一次调用成功后，使用同一 token 再次调用，断言返回 HTTP 422 `import_preview_expired`，且 DB 规则数不变
    - **Validates: Requirements 3.3**

  - [ ]* 2.9 为规则数量上限编写 Property 6 测试（上限不变式）
    - **Property 6: 规则数量上限不变式**
    - 构造已有 M 条规则的 rule_set（M ≤ 200），导入 N 条使 M+N > 200，断言 `parse_and_preview` 和 `confirm_import` 均返回 409，DB 规则数仍为 M
    - **Validates: Requirements 2.8, 3.5**

- [x] 3. 后端路由
  - [x] 3.1 在 `backend/app/routes/compliance.py` 末尾追加 3 个路由及模块级单例
    - 文件顶部追加 import：`ComplianceImportService`、`StreamingResponse`、`io`
    - 初始化模块级单例 `compliance_import_service = ComplianceImportService()`
    - `GET /rule-sets/{rule_set_id}/rules/template`：调用 `require_admin(user)` 鉴权，验证 rule_set 存在性，返回 `StreamingResponse`，Content-Disposition 遵循 RFC 5987 编码（约定 #5）
    - `POST /rule-sets/{rule_set_id}/rules/import/preview`：从 `multipart/form-data` 读取 `file` 字段，调用 `parse_and_preview`，返回 `{ success: True, data: ... }`
    - `POST /rule-sets/{rule_set_id}/rules/import/confirm`：从 JSON body 读取 `preview_session_token`，调用 `confirm_import`，返回 `{ success: True, data: ... }`
    - _Requirements: 1.1, 1.4, 1.5, 1.6, 2.1, 2.9, 2.10, 3.1, 3.7, 3.8, 3.9_

  - [ ]* 3.2 为 3 个路由编写 Property 3 集成测试（权限校验）
    - **Property 3: 权限校验对所有非法角色成立**
    - 对 `role ∉ {法务, 运营}` 的用户（销售/财务/业务/人事）分别调用三个接口，断言均返回 HTTP 403，且无文件解析或 DB 写入
    - **Validates: Requirements 1.4, 2.9, 3.7**

- [x] 4. Checkpoint — 后端自测
  - 确保所有后端测试通过，ask the user if questions arise.

- [x] 5. 前端类型与 Hooks
  - [x] 5.1 在 `frontend/src/types/compliance.ts` 末尾追加导入相关类型
    - 追加：`ImportPreviewRule`、`ImportPreviewResponse`、`ImportConfirmResponse`、`ImportRowError`、`ImportValidationError`
    - _Requirements: 2.7, 3.6, 4.1, 4.2_

  - [x] 5.2 在 `frontend/src/hooks/useCompliance.ts` 末尾追加 3 个 hooks
    - `useDownloadRulesTemplate`：返回异步触发函数，使用 `axiosInstance.get(url, { responseType: 'blob' })` + `URL.createObjectURL` + `<a download>` 触发下载（遵循约定 #9，禁止原生 `<a href>`）
    - `useImportRulesPreview`：`useMutation`，以 `FormData` 形式 POST 到预览接口，返回 `ImportPreviewResponse`
    - `useImportRulesConfirm`：`useMutation`，POST 到确认接口，`onSuccess` 中 `invalidateQueries` 使规则列表和 rule_sets 缓存失效
    - _Requirements: 1.7, 2.13, 3.10_

- [x] 6. 前端 RuleImportModal 组件
  - [x] 6.1 新建 `frontend/src/components/Compliance/RuleImportModal.tsx`，实现上传步骤
    - 使用 Ant Design `Upload.Dragger`，`accept=".xlsx"`，`beforeUpload` 拦截文件（`return false`），`maxCount={1}`
    - 「上传并预览」按钮调用 `previewMutation.mutateAsync`，`loading={previewMutation.isPending}`（防重复提交，Requirements 4.6）
    - 成功后切换到预览步骤；失败时按 `detail.code` 分支展示错误：`import_validation_failed` → 行级错误列表（含行号和原因），`import_quota_exceeded` → 数量提示（当前/导入/上限）
    - _Requirements: 2.13, 4.1, 4.2, 4.6_

  - [x] 6.2 在 `RuleImportModal.tsx` 实现预览确认步骤
    - 使用 Ant Design `Table` 展示规则列表，列：Excel 行号、规则类型（Tag）、规则标题（ellipsis）、严重程度（Tag + 颜色）、排序；分页 pageSize=20，scroll y=400
    - 「确认导入」按钮调用 `confirmMutation.mutateAsync`，`loading={confirmMutation.isPending}`（防重复提交，Requirements 4.5）
    - 成功后 `message.success('成功导入 N 条规则')` 并关闭弹窗
    - 失败时按 `detail.code` 分支处理：`import_preview_expired` → `message.error` + 回到上传步骤，`import_transaction_failed` → `message.error('导入失败，数据未写入，请稍后重试')`
    - 「取消」按钮关闭弹窗，不调用确认接口（Requirements 3.11）
    - _Requirements: 2.13, 3.10, 3.11, 4.3, 4.4, 4.5_

- [x] 7. 前端 RuleTable 集成
  - [x] 7.1 在 `frontend/src/components/Compliance/RuleTable.tsx` 追加「下载模板」和「批量导入」按钮
    - 追加 import：`DownloadOutlined`、`ImportOutlined`、`useState`、`message`、`RuleImportModal`、`useDownloadRulesTemplate`
    - 追加状态：`importModalOpen`、`downloading`
    - 操作栏（`justifyContent: 'flex-end'`）中在「新建规则」按钮左侧依次插入「下载模板」（`loading={downloading}`）和「批量导入」按钮，`gap: 8`
    - 在 Table 之后渲染 `<RuleImportModal ruleSetId={ruleSetId} open={importModalOpen} onClose={() => setImportModalOpen(false)} />`
    - _Requirements: 1.7, 2.13_

- [x] 8. Final Checkpoint — 全链路验证
  - 确保所有测试通过，前后端类型无 TypeScript 编译错误，ask the user if questions arise.

## Notes

- 任务标有 `*` 的为可选测试任务，可跳过以加快 MVP 交付
- 后端改动均为追加，不修改已有路由和服务逻辑（零侵入）
- 前端改动均为追加，不修改已有 hooks 和组件逻辑
- 约定 #5（RFC 5987 Content-Disposition）、约定 #9（blob 下载）已在任务描述中显式标注
- SQLAlchemy UUID 字段比较需 `str()` 包一层（约定 #8），`confirm_import` 中已在设计中体现
- Property 测试建议使用 `pytest` + `hypothesis`（后端）编写

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["2.3", "2.4", "2.5", "5.1"] },
    { "id": 3, "tasks": ["2.6", "2.7", "2.8", "2.9", "5.2"] },
    { "id": 4, "tasks": ["3.1"] },
    { "id": 5, "tasks": ["3.2", "6.1"] },
    { "id": 6, "tasks": ["6.2"] },
    { "id": 7, "tasks": ["7.1"] }
  ]
}
```
