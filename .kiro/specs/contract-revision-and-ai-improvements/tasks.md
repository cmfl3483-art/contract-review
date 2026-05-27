# Implementation Plan: Contract Revision & AI Improvements

## Overview

本实施计划按照"风险低、依赖少先做"的原则，将设计文档拆分为 6 个阶段的离散编码任务：从底层数据库迁移开始，逐层上推到模型、服务、路由、前端 hooks、前端组件，最终通过前后端集成完成全部能力。每个任务都可独立验证，并显式引用具体需求条目。

后端使用 Python（FastAPI / SQLAlchemy / Alembic），前端使用 TypeScript（React + Ant Design + TanStack Query + Zustand）。Property 测试覆盖设计文档中的全部 6 条 Correctness Property，作为可选子任务（postfix `*`）。

> 实施指引：
> Convert the feature design into a series of prompts for a code-generation LLM that will implement each step with incremental progress. Make sure that each prompt builds on the previous prompts, and ends with wiring things together. There should be no hanging or orphaned code that isn't integrated into a previous step. Focus ONLY on tasks that involve writing, modifying, or testing code.

## Tasks

- [x] 1. 阶段1：数据库迁移
  - [x] 1.1 创建 Alembic 迁移：contract_revision_logs 表 + notification_type 枚举扩展
    - 新建文件：`backend/alembic/versions/xxxx_add_contract_revision_logs_and_revised_type.py`
    - `upgrade()` 中执行 `ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'contract_revised'`
    - `upgrade()` 中创建 `contract_revision_logs` 表，列：`id` UUID PK、`contract_id` UUID FK→contracts ON DELETE CASCADE、`revised_by` UUID FK→users ON DELETE CASCADE、`changed_fields` VARCHAR[] NOT NULL、`revised_at` TIMESTAMP NOT NULL DEFAULT now()
    - 创建复合索引 `ix_revision_logs_contract_revised_at(contract_id, revised_at DESC)`
    - `downgrade()` 中 DROP TABLE（PostgreSQL 不移除单个枚举值）
    - 本地执行 `alembic upgrade head` 验证迁移成功，再执行 `alembic downgrade -1` 验证回滚
    - _Requirements: 1.8, 1.10_

- [x] 2. 阶段2：后端模型层
  - [x] 2.1 新建 ContractRevisionLog SQLAlchemy 模型
    - 新建文件：`backend/app/models/contract_revision_log.py`
    - 定义 `ContractRevisionLog(Base)`，`__tablename__ = "contract_revision_logs"`
    - 字段映射严格匹配迁移：`id`、`contract_id`、`revised_by`、`changed_fields`(`ARRAY(String)`)、`revised_at`
    - 关联 `contract`、`revised_by_user` relationship
    - 在 `backend/app/models/__init__.py` 中导出 `ContractRevisionLog`
    - _Requirements: 1.8_

  - [x] 2.2 扩展 NotificationType 枚举新增 CONTRACT_REVISED
    - 修改文件：`backend/app/models/notification.py`
    - 在 `NotificationType` 枚举中追加 `CONTRACT_REVISED = "contract_revised"`
    - 确认枚举值字符串与迁移中 `ALTER TYPE` 添加的值一致
    - _Requirements: 1.10_

- [x] 3. 阶段3：后端服务层
  - [x] 3.1 ContractService 新增 revise_contract() 方法
    - 修改文件：`backend/app/services/contract_service.py`
    - 方法签名：`async def revise_contract(self, contract_id, user_id, new_name=None, new_description=None, attachment_added=False, db) -> Contract`
    - 使用 `select(...).with_for_update()` 锁住合同行，避免并发
    - 权限校验：合同不存在 → 404；非 Initiator → 403；status == "completed" → 409
    - 输入校验：`new_name.strip()` 长度需在 1-200，`new_description` 长度 ≤ 5000，否则 422 且不修改任何数据
    - 实际值变更检测：仅当 normalize 后的 `new_name`/`new_description` 与持久化值不同，或 `attachment_added=True`，才追加到 `changed_fields`
    - 同事务内：UPDATE contracts、UPDATE reviews SET status='pending'、INSERT contract_revision_logs
    - 保留 reviews.opinion 与 comments 不删除、不覆盖
    - status 字段保持 progress 不变
    - 事务提交后调用 `_notify_revision`：通过 `sio.emit("contract:revised", payload, room=f"user:{reviewer_id}")` 推送给所有评审人；调用 `notification_service_v2.create_contract_revised_notifications`
    - 调用 `cache_invalidation.invalidate_contract_updated` 清缓存（合同列表、待办数量、合同详情）
    - 若 `changed_fields` 为空，直接返回原合同，不重置 reviews、不写日志、不推送
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.11_

  - [ ]* 3.2 Property 1: 重审原子性属性测试
    - 新建文件：`backend/tests/properties/test_revise_contract_atomicity.py`
    - 使用 Hypothesis 生成 (合同名变更、描述变更、附件标志) 任意组合
    - **Property 1: 重审原子性** —— 在调用 revise_contract 时 mock `db.execute` 在 reviews UPDATE 后抛异常，断言：合同 name/description 未变更、reviews.status 未变更、contract_revision_logs 未新增
    - 同时验证成功路径下三项更新一致可见
    - **Validates: Requirements 1.5, 1.7, 1.8**

  - [ ]* 3.3 Property 2: 实际值变更检测属性测试
    - 新建文件：`backend/tests/properties/test_revise_value_change_detection.py`
    - 使用 Hypothesis 生成 (原 name, 原 description, 提交 name, 提交 description) 字符串组合
    - **Property 2: 实际值变更检测** —— 当 `提交.strip() == 持久化.strip()` 且 `attachment_added=False`，断言不写入 contract_revision_logs、reviews 状态保持不变；否则断言写入日志且 reviews 全部 pending
    - **Validates: Requirements 1.5**

  - [x] 3.4 NotificationServiceV2 新增 create_contract_revised_notifications() 方法
    - 修改文件：`backend/app/services/notification_service_v2.py`
    - 签名：`async def create_contract_revised_notifications(self, contract, changed_fields, db) -> None`
    - 加载该合同所有 reviews，遍历调用 `self.create_notification`
    - `notification_type=NotificationType.CONTRACT_REVISED`、`anchor_id=None`
    - `preview` 文案：`f"{contract.name} 已修改：{', '.join(changed_fields)}，请重新审批"`
    - `actor_id` 设为 contract.initiator_id
    - _Requirements: 1.10_

  - [x] 3.5 AIService 改造：上下文加 ID 前缀 + system prompt 加引用规则
    - 修改文件：`backend/app/services/ai_service.py`
    - `_build_contract_context`：在评审进度区每行前加 `[review-{r.id}]`、在评论记录区每行前加 `[comment-{c.id}]`
    - `_ai_summary`：扩展 system_prompt 加入「引用规则」段落，明确：使用 `[ref:review-{review_id}]` / `[ref:comment-{comment_id}]` 标记，ID 必须严格使用上下文中实际出现的 ID，禁止杜撰；多引用可追加多个标记；无引用则不追加
    - `answer_question` 不解析 `[ref:...]`，原样透传
    - _Requirements: 3.1, 3.2_

- [x] 4. 阶段4：后端路由层
  - [x] 4.1 新增 PATCH /api/contracts/{contract_id} 路由
    - 修改文件：`backend/app/routes/contracts.py`
    - 定义 `ReviseContractRequest(BaseModel)`：`name: Optional[str] = Field(None, max_length=200)`、`description: Optional[str] = Field(None, max_length=5000)`
    - 路由函数从 `Request` 取 current_user，调用 `contract_service.revise_contract(..., attachment_added=False)`
    - 返回 `{"success": True, "data": {"contract": _serialize_contract(contract)}}`
    - HTTPException 自动映射 401/403/404/409/422
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 4.2 改造 POST /api/contracts/{contract_id}/attachments 触发重审
    - 修改文件：`backend/app/routes/files.py`
    - 上传前校验：非 Initiator → 403；非 progress → 409；文件 size > 50MB → 422
    - 上传成功（attachment 已落库）后，在同一请求处理中调用 `contract_service.revise_contract(contract_id, user_id, attachment_added=True, db=db)`
    - 触发后端 reviews 重置 + 审计日志 + Socket.IO + 通知（复用 3.1 实现）
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.8, 1.9, 1.10_

  - [x] 4.3 新增 GET /api/contracts/{contract_id}/mentionable-users 路由
    - 修改文件：`backend/app/routes/contracts.py`
    - 接收 `search: Optional[str] = Query(None)`
    - 加载合同并 `selectinload(reviews).selectinload(reviewer)`，404 当合同不存在
    - 收集相关用户 ID = {initiator_id} ∪ {所有 reviewer_id} ∪ cc_users（按 ID 去重）
    - 权限：当前用户必须在 related_ids 中，否则 403
    - 批量加载 User，应用 search 过滤：`(search or "").strip()` 后长度 1-50 时按 name 不区分大小写子串匹配；空字符串或未提供则返回完整并集
    - 按 name 升序，截断至最多 100 条
    - 返回字段：`id`、`name`、`avatar`、`department`
    - _Requirements: 2.1, 2.2, 2.3, 2.7, 2.8, 2.9_

  - [ ]* 4.4 Property 3: 候选人完整性属性测试
    - 新建文件：`backend/tests/properties/test_mentionable_users_completeness.py`
    - 使用 Hypothesis 生成 (initiator, reviewers[], cc_users[]) 含交集与重复的随机组合
    - **Property 3: 候选人完整性** —— 调用接口（无 search 参数），断言返回结果集合 == `{initiator} ∪ {reviewers} ∪ {cc_users}`，且每个用户 ID 仅出现一次（去重）
    - **Validates: Requirements 2.2**

- [x] 5. 阶段5：前端类型与 hooks
  - [x] 5.1 扩展 frontend/src/types/index.ts
    - 修改文件：`frontend/src/types/index.ts`
    - `NotificationType` 联合类型新增 `'contract_revised'`
    - 新增 `MentionableUser` 接口：`{ id: string; name: string; avatar?: string; department?: string }`
    - 新增 `ContractRevisionLog` 接口：`{ id, contractId, revisedBy, changedFields: ('name' | 'description' | 'attachment')[], revisedAt }`
    - _Requirements: 1.10, 2.1_

  - [x] 5.2 新增 useReviseContract hook
    - 新建文件：`frontend/src/hooks/useReviseContract.ts`
    - 封装 `useMutation`，调用 `axios.patch(${API_BASE_URL}/api/contracts/${contractId}, data)`
    - 仅传变更字段（`name?: string`、`description?: string`）
    - `onSuccess` 时 invalidate `queryKeys.contracts.detail(id)`、`queryKeys.reviews.list(id)`、`queryKeys.contracts.lists()`、`queryKeys.pending.count()`
    - 抛错时透传后端 message 用于前端 Form 兜底
    - _Requirements: 1.1, 1.4, 1.5_

  - [x] 5.3 新增 useMentionableUsers hook（替代 MentionPicker 中的 useUsers）
    - 新建文件：`frontend/src/hooks/useMentionableUsers.ts`
    - 使用 `useQuery`，queryKey: `['mentionable-users', contractId, debouncedQuery]`
    - 请求 `GET /api/contracts/${contractId}/mentionable-users`，`params` 仅在 `debouncedQuery` 非空时携带 `search`
    - axios 配置 `timeout: 5000`、`retry: false`
    - 返回 `{ data, isLoading, error }`，data 为 `MentionableUser[]`
    - _Requirements: 2.4, 2.5, 2.10_

  - [x] 5.4 frontend/src/config/socket.ts 新增 onContractRevised
    - 修改文件：`frontend/src/config/socket.ts`
    - 导出函数 `onContractRevised(callback)`：内部 `getSocket().on("contract:revised", callback)`，返回 unsubscribe
    - payload 类型：`{ contractId: string; contractName: string; changedFields: string[] }`
    - _Requirements: 1.9_

  - [x] 5.5 useSocket.ts 新增 contract:revised 事件监听
    - 修改文件：`frontend/src/hooks/useSocket.ts`
    - 在已有的 socket 订阅函数中追加：调用 `onContractRevised`，回调中 invalidate `queryKeys.contracts.detail(contractId)`、`queryKeys.reviews.list(contractId)`、`queryKeys.contracts.lists()`、`queryKeys.pending.count()`
    - 弹 `message.warning(\`合同「${contractName}」已被发起人修改（${changedFields.join('、')}），请重新审批\`)`
    - 在 cleanup 中调用 unsubscribe
    - _Requirements: 1.9, 1.11_

- [x] 6. 阶段6：前端组件
  - [x] 6.1 改造 ContractDetail 新增编辑模式
    - 修改文件：`frontend/src/components/ContractDetail/ContractDetail.tsx`
    - 仅当 `currentUser.id === contract.initiator.id && contract.status === 'progress'` 时显示「编辑」按钮
    - 进入编辑模式：标题 → `<Input maxLength={200}>`、描述 → `<Input.TextArea maxLength={5000}>`
    - 顶部显示 `<Alert>` 警告：「修改后所有评审人需重新审批」
    - 「保存」按钮调用 `useReviseContract().mutateAsync`，仅传 dirty 字段；成功后退出编辑模式
    - 「取消」按钮恢复原值并退出编辑模式
    - 422 错误时显示后端返回的字段限制信息
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 6.2 改造 MentionPicker 改用 mentionable-users 接口
    - 修改文件：`frontend/src/components/Timeline/MentionPicker.tsx`（若实际路径不同请按实存路径修改）
    - 移除原 `GET /api/users` 调用，改用 `useMentionableUsers(contractId, debouncedQuery)`
    - 输入做 200ms 防抖；前后请求竞态由 TanStack Query 默认行为保证仅渲染最新结果
    - `error` 存在 → 渲染「加载候选人失败，请重试」
    - `data` 为空 → 渲染「无匹配用户」，禁止完成 @ 选择
    - _Requirements: 2.4, 2.5, 2.6, 2.10_

  - [x] 6.3 新增 MessageContent 组件解析 [ref:...] 标记
    - 新建文件：`frontend/src/components/AIAdvisor/MessageContent.tsx`
    - 正则：`/\[ref:(review|comment)-([a-f0-9-]+)\]/g`
    - 接收 props：`text`、`contractId`、`reviewMap: Map<string, {authorName}>`、`commentMap: Map<string, {authorName}>`
    - 遍历匹配渲染 `<a class="ai-ref-link">@{authorName}的评审/评论</a>`，未匹配 ID 渲染 `<span class="ai-ref-invalid">引用不可用</span>`
    - 点击链接：`useSelectedContractStore.setSelectedContractId(contractId)`、`useFocusedAnchorStore.setAnchorId(id)`，setTimeout 后 `document.getElementById(\`anchor-${id}\`).scrollIntoView`、添加 `highlight-flash` 类，3 秒后移除
    - 同 ID 多次出现：每次独立 React key（含 match.index）
    - 同时新增/扩展 `frontend/src/components/AIAdvisor/AIAdvisor.css`（或 inline）：`.ai-ref-link`、`.ai-ref-invalid`、`.highlight-flash`
    - _Requirements: 3.3, 3.4, 3.5_

  - [ ]* 6.4 Property 4: 引用 ID 真实性属性测试
    - 新建文件：`frontend/src/components/AIAdvisor/__tests__/MessageContent.property.test.tsx`
    - 使用 fast-check 生成 (合法 reviewIds, 合法 commentIds, 注入到 text 的 [ref:...] 标记，部分 ID 不在 map 中)
    - **Property 4: 引用 ID 真实性** —— 渲染 MessageContent，断言：所有在 map 中存在的 ID 渲染为可点击链接 `<a>`；所有不存在的 ID 渲染为不可点击纯文本「引用不可用」；非 ref 文本完整保留；不抛错、不静默丢字符
    - **Validates: Requirements 3.2, 3.5**

  - [x] 6.5 新增 CollapsibleMessage 组件
    - 新建文件：`frontend/src/components/AIAdvisor/CollapsibleMessage.tsx`
    - 使用 `useLayoutEffect` 测量 `ref.current.scrollHeight`，与阈值 `LINE_HEIGHT_PX(22) * MAX_LINES(10) = 220` 比较，决定 `needCollapse`
    - 状态 `expanded` 默认 false；折叠态显示前 10 行 + 渐变遮罩 + 「展开全部」按钮；展开态完整显示 + 「收起」按钮
    - 测量时临时移除 `max-height` 拿到真实 scrollHeight
    - 监听依赖：children 文本变化时重新测量（通过 ref 比较 textContent 或 useEffect deps 传入文本签名）
    - 接收 prop `isStreaming?: boolean`（默认 false），`isStreaming === true` 时不测量、不显示折叠按钮、不应用遮罩
    - 配套 CSS：`.collapsible-message.collapsed .collapsible-content { max-height: 220px; overflow: hidden }`、`.fade-mask` 渐变遮罩、`.toggle-btn` 按钮样式
    - _Requirements: 3.6, 3.7, 3.8, 3.9, 3.11_

  - [ ]* 6.6 Property 5: 折叠测量幂等性属性测试
    - 新建文件：`frontend/src/components/AIAdvisor/__tests__/CollapsibleMessage.property.test.tsx`
    - 使用 fast-check + @testing-library/react，注入固定宽度容器与确定的 line-height
    - **Property 5: 折叠测量幂等性** —— 同一文本在同一渲染宽度下，多次挂载/重渲染的 `needCollapse` 判定结果必须一致；判定基于 DOM `scrollHeight`，行数 ≤ 10 时不显示按钮，> 10 时显示
    - **Validates: Requirements 3.6, 3.7**

  - [ ]* 6.7 Property 6: 流式输出折叠延迟属性测试
    - 新建文件：`frontend/src/components/AIAdvisor/__tests__/CollapsibleMessage.streaming.property.test.tsx`
    - 使用 fast-check 生成任意长文本切片序列，模拟流式追加（多次 rerender，`isStreaming=true`）
    - **Property 6: 流式输出折叠延迟** —— 流式过程中所有快照都不渲染折叠按钮、不应用遮罩；切到 `isStreaming=false` 后，按真实 DOM 高度重新执行测量，必要时显示折叠按钮
    - **Validates: Requirements 3.11**

  - [x] 6.8 改造 Message 组件集成 MessageContent + CollapsibleMessage
    - 修改文件：`frontend/src/components/AIAdvisor/Message.tsx`
    - 新增 props：`reviewMap`、`commentMap`、`contractId`、`isStreaming?`
    - `body` 中将原始文本节点替换为 `<MessageContent text={message.content} ... />`
    - `isUser === true` 时直接渲染 body（不折叠、不测量、不遮罩）
    - `isUser === false` 时用 `<CollapsibleMessage isStreaming={isStreaming}>` 包裹 body
    - _Requirements: 3.3, 3.6, 3.7, 3.10, 3.11_

  - [x] 6.9 改造 AIAdvisor 构建 reviewMap/commentMap 并透传 isStreaming
    - 修改文件：`frontend/src/components/AIAdvisor/AIAdvisor.tsx`
    - 通过 `useReviews(selectedContractId)` 获取 reviews + comments
    - `useMemo` 构建 `reviewMap`（reviewer.name）、`commentMap`（包含 reviews.replies 的评论 + topLevelComments；author.name）
    - 渲染 Message 时传入 reviewMap、commentMap、contractId
    - 流式状态：当前正在接收的 AI 消息 `isStreaming={true}`，结束后 `false` 触发重新测量
    - _Requirements: 3.1, 3.3, 3.4, 3.11_

  - [x] 6.10 改造 NotificationItem 新增 contract_revised 图标
    - 修改文件：`frontend/src/components/NotificationCenter/NotificationItem.tsx`
    - `TYPE_ICONS` 追加 `contract_revised: '📝'`
    - 跳转逻辑：`anchor_id` 为 null 时仅切换合同（`setSelectedContractId`），不调用 setAnchorId、不滚动
    - _Requirements: 1.10_

- [x] 7. 最终 checkpoint - 确保前后端集成测试通过
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- 标记 `*` 的子任务为可选属性测试，可在快速 MVP 中跳过；核心实现任务不会被标记为可选
- 每个任务都引用了具体的需求条目（如 1.5、2.2、3.4），便于实现时回查约束
- Property 测试覆盖设计文档中 6 条 Correctness Property，后端 3 条（重审原子性、值变更检测、候选人完整性），前端 3 条（引用真实性、折叠幂等性、流式折叠延迟）
- Checkpoint 任务 7 用于在所有阶段完成后做端到端验证，必要时与用户确认；不进入依赖图
- 所有任务严格限定为代码层操作，不包含部署、用户培训、性能压测等非代码动作
- 前端 hook（5.2、5.3）与后端路由（4.1、4.3）通过新建独立文件解耦，可在路由完成前并行编写以加速进度

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "5.1", "5.4"] },
    { "id": 1, "tasks": ["2.1", "2.2", "5.5", "6.3", "6.5"] },
    { "id": 2, "tasks": ["3.4", "3.5", "5.2", "5.3", "6.4", "6.6", "6.7", "6.10"] },
    { "id": 3, "tasks": ["3.1", "6.8"] },
    { "id": 4, "tasks": ["3.2", "3.3", "4.1", "4.2", "6.1", "6.2", "6.9"] },
    { "id": 5, "tasks": ["4.3"] },
    { "id": 6, "tasks": ["4.4"] }
  ]
}
```
