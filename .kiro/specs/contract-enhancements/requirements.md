# Requirements Document

## Introduction

本文档描述合同预审看板系统的四项功能增强需求：评论 @ 提及用户、消息通知机制、"我已审批"筛选项，以及数据权限隔离。这些功能在现有 FastAPI + React 技术栈基础上扩展，旨在提升协作效率和数据安全性。

现有系统技术栈：后端 FastAPI + PostgreSQL + Redis + Socket.IO（Python），前端 React + TypeScript + Ant Design + Zustand + TanStack Query，认证采用钉钉 OAuth2 + JWT，部署于 Docker Compose 腾讯云生产环境。

## Glossary

- **System**：合同预审看板系统整体
- **Comment_Box**：评论输入框组件，支持新增评论和回复
- **Mention_Picker**：@ 提及时弹出的人员选择框组件（复用现有选人组件）
- **Notification_Service**：后端消息通知服务，负责生成和推送通知
- **Notification_Center**：前端通知中心组件，包含铃铛图标、未读数角标和通知列表
- **Filter_Service**：后端合同列表筛选服务，对应现有 `_apply_filter()` 方法
- **Contract**：合同记录，对应 `contracts` 表
- **Review**：评审记录，对应 `reviews` 表
- **Comment**：评论记录，对应 `comments` 表
- **Current_User**：当前已登录的用户
- **Initiator**：合同发起人，即 `contracts.initiator_id` 对应的用户
- **Reviewer**：评审人，即在 `reviews` 表中存在记录的用户
- **CC_User**：抄送用户，即出现在 `contracts.cc_users` 数组中的用户
- **Mentioned_User**：在评论内容中被 @ 提及的用户
- **Notification**：通知记录，包含类型、关联资源、已读状态等信息
- **Unread_Count**：当前用户未读通知数量

---

## Requirements

### Requirement 1: 评论与回复中 @ 提及用户

**User Story:** 作为评审参与者，我希望在评论或回复时能够 @ 提及其他用户，以便明确告知相关人员关注特定内容。

#### Acceptance Criteria

1. WHEN Current_User 在 Comment_Box 中输入 `@` 字符，THE Comment_Box SHALL 在光标位置下方弹出 Mention_Picker。
2. WHEN Mention_Picker 处于展开状态且 Current_User 继续输入字符（最多 20 个字符），THE Mention_Picker SHALL 根据输入字符对用户姓名进行实时过滤，并在 200ms 内更新候选列表；IF 过滤结果为空，THEN THE Mention_Picker SHALL 显示"无匹配用户"提示。
3. WHEN Current_User 在 Mention_Picker 中选中一名用户，THE Comment_Box SHALL 将 `@` 及后续输入字符替换为 `@{用户姓名}` 标记，并关闭 Mention_Picker。
4. WHEN Current_User 按下 Escape 键或点击 Mention_Picker 以外的区域，THE Mention_Picker SHALL 关闭并保留已输入的原始文本。
5. WHEN Current_User 提交包含 @ 标记的评论，THE System SHALL 将被提及用户的 ID 列表记录在 `comments.mentioned_user_ids` 字段中。
6. THE Comment_Box SHALL 支持在同一条评论中提及最多 10 名用户；IF Current_User 尝试提及第 11 名用户，THEN THE Mention_Picker SHALL 不弹出并在输入框下方显示"最多可提及 10 人"提示。
7. IF Current_User 提交评论时 `mentioned_user_ids` 包含不存在于系统中的用户 ID，THEN THE System SHALL 静默忽略无效 ID（不向用户显示错误），并正常保存其余有效 ID。
8. THE Mention_Picker 的候选列表 SHALL 包含当前合同的所有参与者（发起人、评审人、抄送人），并支持按姓名搜索系统内所有用户。

---

### Requirement 2: 消息通知机制

**User Story:** 作为合同相关人员，我希望在发生与我相关的操作时收到通知，以便及时跟进合同进展和互动。

#### Acceptance Criteria

1. WHEN 某用户对 Current_User 发起的 Contract 执行审批通过操作（`review.status` 变更为 `approved`），THE Notification_Service SHALL 为 Current_User 生成一条类型为 `review_approved` 的通知，并关联对应的 Review 记录。
2. WHEN 某用户在 Current_User 发起的 Contract 下添加评论，THE Notification_Service SHALL 为 Current_User 生成一条类型为 `comment_added` 的通知，并关联对应的 Comment 记录。
3. WHEN 某用户回复了 Current_User 发表的评论，THE Notification_Service SHALL 为 Current_User 生成一条类型为 `comment_replied` 的通知，并关联对应的 Comment 记录。
4. WHEN 某用户在评论中提及了 Current_User（`mentioned_user_ids` 包含 Current_User 的 ID），THE Notification_Service SHALL 为 Current_User 生成一条类型为 `user_mentioned` 的通知，并关联对应的 Comment 记录。
5. IF 操作者与通知接收者为同一用户（包括用户审批自己发起的合同的情形），THEN THE Notification_Service SHALL 不生成任何通知。
6. WHEN Notification_Service 生成新通知，THE System SHALL 通过现有 Socket.IO 连接向对应用户实时推送通知事件，使 Unread_Count 在 1 秒内更新；IF Socket.IO 连接不可用，THEN THE System SHALL 将通知持久化存储，待用户下次请求通知列表时返回。
7. THE Notification_Center SHALL 在界面顶部以铃铛图标展示，并在图标右上角显示 Unread_Count 角标。
8. WHEN Unread_Count 为 0，THE Notification_Center SHALL 不显示角标。
9. WHEN Current_User 点击铃铛图标，THE Notification_Center SHALL 展开通知列表，按创建时间倒序排列，每条通知显示操作类型、操作人姓名、合同名称和相对时间（1 分钟内显示"刚刚"，1 小时内显示"X 分钟前"，24 小时内显示"X 小时前"，超过 24 小时显示具体日期）。
10. WHEN Current_User 点击通知列表中的某条通知，THE System SHALL 导航至对应合同详情页，并将页面滚动至关联的评论或评审卡片位置，同时对该元素应用高亮样式持续 3 秒。
11. WHEN Current_User 点击某条通知，THE Notification_Service SHALL 将该通知的状态标记为已读，并更新 Unread_Count。
12. WHEN Current_User 点击"全部标为已读"操作，THE Notification_Service SHALL 将 Current_User 的所有未读通知标记为已读，并将 Unread_Count 更新为 0。
13. THE Notification_Center SHALL 支持分页加载通知列表，每页加载 20 条。
14. IF Current_User 点击通知时关联的评论或评审记录已被删除，THEN THE System SHALL 仍导航至对应合同详情页，并显示"该内容已被删除"的提示信息。

---

### Requirement 3: 合同列表新增"我已审批"筛选项

**User Story:** 作为评审人，我希望能够快速查看我已经审批通过的合同列表，以便追溯历史审批记录。

#### Acceptance Criteria

1. THE System SHALL 在现有筛选条件（`all`、`进行中`、`已完成`、`待我处理`、`抄送我`、`我发起的`）基础上新增 `我已审批` 筛选项，并在前端筛选栏中展示。
2. WHEN Current_User 选择 `我已审批` 筛选项，THE Filter_Service SHALL 返回所有存在 `reviews` 记录满足 `reviewer_id = Current_User.id AND status = 'approved'` 的 Contract 列表，且每个 Contract 在结果中仅出现一次（对多条 approved 记录去重）。
3. WHEN Current_User 选择 `我已审批` 筛选项，THE Filter_Service SHALL 按 Contract 的 `created_at` 字段倒序排列结果。
4. WHEN Current_User 选择 `我已审批` 筛选项且无符合条件的合同，THE System SHALL 显示空状态提示"暂无已审批的合同"。
5. WHEN Current_User 选择 `我已审批` 筛选项，THE Filter_Service SHALL 支持与现有分页参数（`page`、`page_size`，其中 `page_size` 上限为 100）的组合查询。

---

### Requirement 4: 数据权限隔离

**User Story:** 作为系统用户，我希望"全部"、"进行中"、"已完成"筛选项只显示与我有关的合同，以避免看到无关合同信息，保护数据隐私。

#### Acceptance Criteria

1. WHEN Current_User 选择 `all`、`进行中` 或 `已完成` 筛选项，THE Filter_Service SHALL 仅返回满足以下任一条件的 Contract：`initiator_id = Current_User.id`（我发起的）OR `Current_User.id` 存在于 `cc_users` 数组中（抄送我）OR 存在 `reviews` 记录满足 `reviewer_id = Current_User.id`（我是评审人）。
2. WHEN Current_User 选择 `进行中` 筛选项，THE Filter_Service SHALL 在数据权限过滤基础上进一步限定 `contracts.status = 'progress'`。
3. WHEN Current_User 选择 `已完成` 筛选项，THE Filter_Service SHALL 在数据权限过滤基础上进一步限定 `contracts.status = 'completed'`。
4. WHEN Current_User 选择 `待我处理`、`抄送我`、`我发起的` 或 `我已审批` 筛选项，THE Filter_Service SHALL 按各筛选项原有逻辑处理，不额外叠加数据权限过滤条件。
5. IF 请求中 JWT Token 缺失、格式无效或已过期，THEN THE Filter_Service SHALL 返回 HTTP 401 错误，响应体包含认证失败说明，且不返回任何合同数据。
