# Requirements Document

## Introduction

本文档描述合同预审看板系统的第三轮功能增强需求，包含三项独立但相关的改进：

1. **合同修改触发重新审批**：发起人在合同进行中阶段修改关键字段（标题、描述、附件）时，自动重置所有评审人的审批状态，并同步通知评审人重新审批。
2. **@ 提及候选人范围限制**：评论与回复中的 @ 提及候选列表从"全公司用户"收窄为"当前合同的相关人员"（发起人 + 评审人 + 抄送人）。
3. **AI 合同预审助理改造**：AI 总结输出可定位的引用标记（点击跳转到原始评论/评审），并对超长 AI 回复进行折叠展示。

现有系统技术栈：后端 FastAPI + PostgreSQL + Redis + Socket.IO（Python），前端 React + TypeScript + Ant Design + Zustand + TanStack Query，认证采用钉钉 OAuth2 + JWT，部署于 Docker Compose 腾讯云生产环境。本轮需求建立在已交付的 `contract-pre-review` 与 `contract-enhancements` 两个 spec 之上。

## Glossary

- **System**：合同预审看板系统整体
- **Contract**：合同记录，对应 `contracts` 表
- **Review**：评审记录，对应 `reviews` 表
- **Comment**：评论记录，对应 `comments` 表
- **Attachment**：附件记录，对应 `attachments` 表
- **Current_User**：当前已登录的用户
- **Initiator**：合同发起人，即 `contracts.initiator_id` 对应的用户
- **Reviewer**：评审人，即在 `reviews` 表中存在记录的用户
- **CC_User**：抄送用户，即出现在 `contracts.cc_users` 数组中的用户
- **Mentionable_User**：在某 Contract 上下文中可被 @ 提及的用户，定义为 Initiator、Reviewer、CC_User 三类去重后的并集
- **Revision_Service**：后端合同修改服务，负责处理标题、描述、附件的修改并触发重审流程
- **Re_Review_Event**：重新审批事件，触发于 Initiator 在 progress 状态下修改 Contract 关键字段（标题、描述、新增附件版本）的实际值变更
- **Revision_Audit_Log**：重新审批审计日志，记录修改字段、修改人、修改时间，对应新增的 `contract_revision_logs` 表
- **Mentionable_Users_API**：返回某 Contract 候选 @ 提及人列表的后端接口
- **Mention_Picker**：评论或回复输入时弹出的人员选择框组件（在 `CommentInput`、`MentionInput` 等输入控件中复用）
- **AI_Service**：后端 AI 合同预审助理服务，对应 `ai_service.answer_question`
- **AI_Advisor**：前端 AI 顾问对话组件，对应 `AIAdvisor.tsx`
- **AI_Reference_Tag**：AI 回复中用于引用具体 Review 或 Comment 的结构化标记，格式为 `[ref:review-{id}]` 或 `[ref:comment-{id}]`
- **Focused_Anchor_Store**：前端用于跨页面跳转并定位评论/评审卡片的 Zustand store（已实现 `useFocusedAnchorStore`）
- **AI_Message_Bubble**：AI 顾问对话中渲染单条 AI 回复的气泡组件
- **Visual_Line**：AI 回复在当前气泡渲染宽度下的视觉文本行，由 DOM 实际渲染高度决定，而非源文本中的换行符数量

---

## Requirements

### Requirement 1: 合同修改触发重新审批

**User Story:** 作为合同发起人，我希望在合同进行中阶段修改标题、描述或附件后，所有评审人能自动重新审批，以便确保评审基于最新版本的合同内容进行。

#### Acceptance Criteria

1. WHILE Contract 的 `status` 为 `progress`，WHEN Initiator 提交对 Contract 的 `name`、`description` 修改或新增一条 Attachment 版本的请求，且 `name` 在去除首尾空白后长度为 1 至 200 个字符、`description` 长度为 0 至 5000 个字符、单个新增 Attachment 文件大小不超过 50 MB，THE Revision_Service SHALL 接受该请求并将变更持久化至数据库。
2. IF Current_User 不是 Contract 的 Initiator 且尝试修改 Contract 的 `name`、`description` 或新增 Attachment 版本，THEN THE Revision_Service SHALL 拒绝该请求并返回 HTTP 403 错误，响应体包含权限不足说明，且不修改任何 Contract、Review、Attachment 数据。
3. IF Contract 的 `status` 为 `completed` 且 Current_User 尝试修改 Contract 的 `name`、`description` 或新增 Attachment 版本，THEN THE Revision_Service SHALL 拒绝该请求并返回 HTTP 409 错误，响应体说明已完成的合同不允许修改，且不修改任何 Contract、Review、Attachment 数据。
4. IF Initiator 在 `status` 为 `progress` 时提交的 `name` 长度超出 1 至 200 字符范围、`description` 长度超过 5000 字符，或新增 Attachment 文件大小超过 50 MB，THEN THE Revision_Service SHALL 拒绝该请求并返回 HTTP 422 错误，响应体说明触发限制的字段及其上限，且不重置任何 Review 记录的 `status`、不写入 Revision_Audit_Log。
5. WHEN Initiator 在 `progress` 状态下成功提交对 Contract 的 `name` 或 `description` 字段的实际值变更（即提交值在去除首尾空白后与当前持久化值不相等），或成功新增一条 Attachment 记录，THE Revision_Service SHALL 在同一数据库事务中将该 Contract 关联的全部 Review 记录的 `status` 字段重置为 `pending`。
6. WHEN Re_Review_Event 触发，THE Revision_Service SHALL 保留该 Contract 已存在的 Review `opinion` 字段值与全部 Comment 记录作为历史评审意见，不进行删除或覆盖。
7. WHEN Re_Review_Event 触发，THE Revision_Service SHALL 保持 Contract 的 `status` 字段为 `progress` 不变。
8. WHEN Re_Review_Event 触发，THE Revision_Service SHALL 在同一数据库事务中向 Revision_Audit_Log 中插入一条记录，包含 `contract_id`、`revised_by`（Initiator 用户 ID）、`changed_fields`（变更字段列表，取值范围为 `name`、`description`、`attachment` 的非空子集）、`revised_at`（变更时间戳，UTC）。
9. WHEN Re_Review_Event 所在数据库事务成功提交，THE System SHALL 通过 Socket.IO 在 5 秒内向该 Contract 的全部 Reviewer 各推送一条事件消息，事件包含 Contract ID、Contract 名称、变更字段列表，以提示 Reviewer 重新审批。
10. WHEN Re_Review_Event 所在数据库事务成功提交，THE System SHALL 为该 Contract 的全部 Reviewer 各生成一条类型为 `contract_revised` 的 Notification，关联对应的 Contract 记录。
11. WHEN Reviewer 在 Re_Review_Event 触发后调用合同列表的 `待我处理` 筛选项接口，THE System SHALL 将该 Contract 重新纳入返回结果，即使该 Reviewer 在重审前已审批通过。

---

### Requirement 2: @ 提及候选人范围限制

**User Story:** 作为评审参与者，我希望 @ 提及候选列表只显示当前合同的相关人员，以避免误选无关同事并提升选择效率。

#### Acceptance Criteria

1. THE System SHALL 提供 Mentionable_Users_API，路径为 `GET /api/contracts/{contract_id}/mentionable-users`，返回当前 Contract 的 Mentionable_User 列表；返回的每条用户记录至少包含 `id`、`name`、`avatar`、`department` 四个字段，列表按 `name` 升序排列，最多返回 100 条。
2. WHEN Mentionable_Users_API 被调用，THE System SHALL 将返回结果限定为以下三类用户的并集：Initiator、Reviewer、CC_User，并按用户 ID 去重，每个用户在结果中仅出现一次。
3. WHEN Mentionable_Users_API 接收到 `search` 查询参数，THE System SHALL 在执行匹配前对参数值去除首尾空白；IF 去除空白后的值长度大于 0 且小于等于 50 字符，THEN THE System SHALL 在并集结果上按用户姓名进行不区分大小写的子串匹配，仅返回匹配项；IF 去除空白后的值为空字符串或参数未提供，THEN THE System SHALL 返回完整的并集结果。
4. WHEN Current_User 在评论输入框或回复输入框中触发 @ 提及，THE Mention_Picker SHALL 调用 Mentionable_Users_API 获取候选列表，且不再调用全员搜索接口（如 `GET /api/users`）。
5. WHEN Mention_Picker 处于展开状态且 Current_User 输入字符，THE Mention_Picker SHALL 对输入做 200ms 防抖后将最新输入字符作为 `search` 参数传递给 Mentionable_Users_API；IF 在前一请求未返回前再次触发请求，THEN THE Mention_Picker SHALL 仅渲染最新一次请求的响应结果，丢弃过期请求的响应。
6. IF Mentionable_Users_API 返回空列表，THEN THE Mention_Picker SHALL 显示"无匹配用户"提示，且不允许 Current_User 通过该选择器完成 @ 提及操作。
7. IF Current_User 不是该 Contract 的 Initiator、Reviewer 或 CC_User，THEN THE Mentionable_Users_API SHALL 返回 HTTP 403 错误，响应体包含权限不足说明。
8. IF 请求中 JWT Token 缺失、格式无效或已过期，THEN THE Mentionable_Users_API SHALL 返回 HTTP 401 错误，响应体包含认证失败说明。
9. IF 请求中的 `contract_id` 在 `contracts` 表中不存在，THEN THE Mentionable_Users_API SHALL 返回 HTTP 404 错误，响应体说明合同不存在。
10. IF Mentionable_Users_API 返回非 2xx 响应或在 5 秒内未返回，THEN THE Mention_Picker SHALL 显示"加载候选人失败，请重试"提示，并保留输入框的原始 @ 文本不变，且不渲染候选列表。

---

### Requirement 3: AI 合同预审助理改造

**User Story:** 作为合同评审参与者，我希望 AI 助手的总结能够引用具体的评论或评审并支持点击跳转，同时较长的 AI 回复支持折叠展示，以便快速定位关键信息并控制阅读区域。

#### Acceptance Criteria

1. WHEN Current_User 向 AI_Service 提交的问题文本（不区分英文大小写）以子串方式包含"总结"二字，THE AI_Service SHALL 在生成的回复中，针对每条引用的 Review 内容插入格式为 `[ref:review-{review_id}]` 的 AI_Reference_Tag，针对每条引用的 Comment 内容插入格式为 `[ref:comment-{comment_id}]` 的 AI_Reference_Tag。
2. WHEN AI_Service 调用大语言模型生成总结回复，THE AI_Service SHALL 通过 system prompt 显式指示模型仅使用 Contract 上下文中实际存在的 Review ID 与 Comment ID 作为 AI_Reference_Tag 的取值。
3. WHEN AI_Advisor 接收到包含 AI_Reference_Tag 的 AI 回复，THE AI_Advisor SHALL 解析回复文本，将每个 AI_Reference_Tag 渲染为可点击的内联链接：链接显示文本对于 Review 引用为 `@{作者姓名}的评审`、对于 Comment 引用为 `@{作者姓名}的评论`；同一 ID 在回复中多次出现时，每次出现均渲染为独立的可点击链接。
4. WHEN Current_User 点击 AI_Advisor 中渲染出的引用链接，THE AI_Advisor SHALL 通过 Focused_Anchor_Store 记录目标 Review 或 Comment 的 ID，导航至对应 Contract 详情页，将该卡片滚动至视口内完整可见，对该卡片应用高亮样式，并在 3 秒后自动恢复为原样式。
5. IF AI_Reference_Tag 中的 Review 或 Comment ID 在当前 Contract 上下文中不存在，THEN THE AI_Advisor SHALL 将该标记渲染为不可点击的纯文本"引用不可用"，且不影响其他有效引用的渲染与点击。
6. WHEN AI_Message_Bubble 首次挂载或其回复内容文本发生变更，THE AI_Message_Bubble SHALL 测量回复内容在当前渲染宽度下的 Visual_Line 数量；IF Visual_Line 数量严格大于 10，THEN THE AI_Message_Bubble SHALL 默认仅展示前 10 行内容、在底部叠加自顶向下的渐变遮罩，并在遮罩下方显示"展开全部"按钮。
7. WHEN AI_Message_Bubble 渲染一条 AI 角色的回复且 Visual_Line 数量小于或等于 10，THE AI_Message_Bubble SHALL 完整展示全部内容，且不显示"展开全部"按钮、不显示渐变遮罩。
8. WHEN Current_User 点击 AI_Message_Bubble 上的"展开全部"按钮，THE AI_Message_Bubble SHALL 移除渐变遮罩并展示该回复的完整内容，同时将"展开全部"按钮替换为"收起"按钮。
9. WHEN Current_User 点击 AI_Message_Bubble 上的"收起"按钮，THE AI_Message_Bubble SHALL 恢复仅展示前 10 行内容、重新叠加渐变遮罩，并将"收起"按钮替换为"展开全部"按钮。
10. WHEN AI_Message_Bubble 渲染一条 user 角色的消息，THE AI_Message_Bubble SHALL 完整展示全部内容，不进行 Visual_Line 测量、不展示折叠控制按钮、不应用渐变遮罩。
11. WHILE AI_Service 正在以流式方式输出 AI 回复且尚未结束，THE AI_Message_Bubble SHALL 实时展示已接收到的全部内容，不进行 Visual_Line 测量、不显示折叠按钮、不应用渐变遮罩；WHEN 流式输出结束，THE AI_Message_Bubble SHALL 按 Criterion 6 与 Criterion 7 的规则重新执行测量与折叠判定。
