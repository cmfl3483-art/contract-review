# Implementation Plan: Contract Enhancements

## Overview

按照风险由低到高、依赖由少到多的顺序，分五个阶段实现：数据库迁移 → 后端基础服务 → 后端业务逻辑改造 → 前端类型和 Store → 前端组件。每个阶段完成后均有检查点确保增量验证。

## Tasks

- [x] 1. 阶段1：数据库迁移（无依赖）
  - [x] 1.1 为 comments 表新增 mentioned_user_ids 列（Alembic 迁移）
    - 在 `backend/alembic/versions/` 下新建迁移文件 `xxxx_add_mentioned_user_ids_to_comments.py`
    - `upgrade()`：`op.add_column('comments', sa.Column('mentioned_user_ids', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'))`
    - `downgrade()`：`op.drop_column('comments', 'mentioned_user_ids')`
    - _Requirements: 1.5_

  - [x] 1.2 新建 notifications 表（Alembic 迁移）
    - 在 `backend/alembic/versions/` 下新建迁移文件 `xxxx_create_notifications_table.py`
    - 建表字段：`id`（UUID PK）、`recipient_id`（UUID FK→users）、`actor_id`（UUID FK→users）、`type`（Enum）、`contract_id`（UUID FK→contracts）、`anchor_id`（VARCHAR 100）、`preview`（VARCHAR 200）、`is_read`（BOOLEAN DEFAULT false）、`created_at`（DATETIME DEFAULT now()）
    - 创建枚举类型 `notification_type`：`review_approved`、`comment_added`、`comment_replied`、`user_mentioned`
    - 创建索引：`ix_notifications_recipient_read`（recipient_id, is_read）、`ix_notifications_created_at_desc`（created_at）
    - `downgrade()`：`op.drop_table('notifications')`，`op.execute("DROP TYPE IF EXISTS notification_type")`
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. 阶段1检查点 - 验证迁移
  - 确认两个迁移文件语法正确，`alembic upgrade head` 可成功执行
  - 验证现有 comments 数据的 `mentioned_user_ids` 默认为空数组 `{}`
  - 如有问题请告知

- [x] 3. 阶段2：后端基础服务（依赖阶段1）
  - [x] 3.1 更新 Comment 模型（新增 mentioned_user_ids 字段）
    - 修改 `backend/app/models/comment.py`
    - 新增字段：`mentioned_user_ids: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list, comment="被@提及的用户ID列表")`
    - 确保导入 `from sqlalchemy.dialects.postgresql import ARRAY`
    - _Requirements: 1.5_

  - [x] 3.2 新建 Notification 模型
    - 新建文件 `backend/app/models/notification.py`
    - 定义 `NotificationType` 枚举（`REVIEW_APPROVED`、`COMMENT_ADDED`、`COMMENT_REPLIED`、`USER_MENTIONED`）
    - 定义 `Notification` SQLAlchemy 模型，包含所有字段、外键关系（recipient、actor、contract）和复合索引
    - 在 `backend/app/models/__init__.py` 中导出 `Notification` 和 `NotificationType`
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.3 新建 NotificationService
    - 新建文件 `backend/app/services/notification_service_v2.py`（或扩展现有 `notification_service.py`）
    - 实现以下9个方法：
      - `create_notification()`：创建通知，自动跳过 `actor_id == recipient_id` 的自通知，写入 DB 后调用 `_push_to_socket()`，删除 Redis 缓存 `notification:unread:{recipient_id}`
      - `create_review_approved_notification(review, db)`：通知接收人为合同发起人
      - `create_comment_added_notification(comment, db)`：通知接收人为合同发起人（顶层评论）
      - `create_comment_replied_notification(comment, db)`：通知接收人为被回复评论的作者
      - `create_mention_notifications(comment, db)`：遍历 `mentioned_user_ids`，为每个用户创建通知
      - `get_notifications(recipient_id, page, page_size, db)`：分页查询，按 `created_at` 倒序，`selectinload` actor 和 contract
      - `get_unread_count(recipient_id, db)`：先查 Redis 缓存 `notification:unread:{recipient_id}`（TTL 60s），未命中则查 DB
      - `mark_as_read(notification_id, recipient_id, db)`：更新单条，删除 Redis 缓存
      - `mark_all_as_read(recipient_id, db)`：批量更新，将 Redis 缓存设为 "0"
    - `_push_to_socket()` 推送失败时静默忽略（try/except pass）
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 3.4 为 NotificationService 编写属性测试
    - **Property 1: 自通知不生成**
    - **Validates: Requirements 2.5**
    - 使用 pytest + hypothesis，生成随机 `actor_id` 和 `recipient_id`，当两者相等时验证 `create_notification()` 返回 `None` 且不写入数据库
    - 测试文件：`backend/tests/test_notification_service_properties.py`

  - [ ]* 3.5 为 NotificationService 编写单元测试
    - 测试 `create_review_approved_notification` 接收人为合同发起人
    - 测试 `create_comment_replied_notification` 接收人为被回复评论作者
    - 测试 `get_unread_count` Redis 缓存命中和未命中两种路径
    - 测试文件：`backend/tests/test_notification_service.py`
    - _Requirements: 2.1, 2.2, 2.3, 2.5_

  - [x] 3.6 新建通知路由
    - 新建文件 `backend/app/routes/notifications.py`
    - 实现4个端点（均需 JWT 认证，使用 `get_current_user` 依赖）：
      - `GET /api/notifications?page=1&page_size=20` → 调用 `notification_service.get_notifications()`
      - `GET /api/notifications/unread-count` → 调用 `notification_service.get_unread_count()`
      - `PATCH /api/notifications/{id}/read` → 调用 `notification_service.mark_as_read()`，通知不存在时返回 404
      - `POST /api/notifications/read-all` → 调用 `notification_service.mark_all_as_read()`
    - 在 `backend/app/main.py` 中注册路由：`app.include_router(notifications_router, prefix="/api")`
    - _Requirements: 2.7, 2.11, 2.12, 2.13_

  - [x] 3.7 确认/新增用户搜索接口 GET /api/users?search=
    - 检查 `backend/app/routes/users.py` 是否已支持 `?search=xxx&limit=20` 查询参数
    - 若不支持，新增查询逻辑：按 `name` 字段模糊匹配（`ILIKE %search%`），返回 `[{ id, name, avatar, department }]`
    - 确保接口需要 JWT 认证
    - _Requirements: 1.2, 1.8_

- [x] 4. 阶段2检查点 - 验证后端基础服务
  - 确认所有新增模型可正常导入，路由注册无冲突
  - 确认 `GET /api/notifications/unread-count` 和 `GET /api/users?search=` 可正常响应
  - 如有问题请告知

- [ ] 5. 阶段3：后端业务逻辑改造（依赖阶段2）
  - [x] 5.1 更新评论接口 AddCommentRequest（新增 mentioned_user_ids 字段）
    - 修改 `backend/app/routes/contracts.py`（以及 `backend/app/routes/reviews.py` 如有独立的评论接口）
    - 在 `AddCommentRequest` Pydantic 模型中新增：`mentioned_user_ids: Optional[List[str]] = Field(default=[], max_items=10)`
    - 确保导入 `Optional, List` 和 `Field`
    - _Requirements: 1.5, 1.6_

  - [x] 5.2 改造 comment_service：接收 mentioned_user_ids，触发通知
    - 修改 `backend/app/services/comment_service.py`
    - `create_comment()` 方法新增参数 `mentioned_user_ids: list[str] = []`
    - 将 `mentioned_user_ids` 写入 `comment.mentioned_user_ids`
    - 事务提交后依次调用：
      1. `notification_service_v2.create_comment_added_notification(comment, db)`（顶层评论）
      2. `notification_service_v2.create_comment_replied_notification(comment, db)`（回复评论）
      3. `notification_service_v2.create_mention_notifications(comment, db)`
    - 更新路由调用处，将请求体中的 `mentioned_user_ids` 传入
    - _Requirements: 1.5, 2.2, 2.3, 2.4_

  - [x] 5.3 改造 review_service：approve_review 后触发通知
    - 修改 `backend/app/services/review_service.py`
    - 在 `approve_review()` 方法中，事务提交后调用：`await notification_service_v2.create_review_approved_notification(review, db)`
    - _Requirements: 2.1_

  - [~] 5.4 改造 contract_service：扩展 _apply_filter（需求3"我已审批" + 需求4数据权限隔离）
    - 修改 `backend/app/services/contract_service.py`
    - 新增私有方法 `_build_visibility_subquery(user_id)`：构建三路 UNION 子查询（发起人 OR 抄送人 OR 评审人）
    - 修改 `_apply_filter()` 方法：
      - `all`、`进行中`、`已完成`：在现有状态过滤基础上叠加 `Contract.id.in_(visibility_subquery)`
      - `我已审批`（新增分支）：查询 `reviews` 表中 `reviewer_id = user_id AND status = 'approved'` 的 `contract_id`，使用 `.distinct()` 去重
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 4.1, 4.2, 4.3, 4.4_

  - [ ]* 5.5 为 contract_service 编写属性测试
    - **Property 2: 权限隔离完整性**
    - **Validates: Requirements 4.1, 4.2, 4.3**
    - 使用 pytest + hypothesis，生成随机用户和合同数据，验证 `filter=all/进行中/已完成` 返回结果不包含与当前用户无任何关联的合同
    - **Property 3: 我已审批去重**
    - **Validates: Requirements 3.2**
    - 生成同一合同有多条 `approved` 评审记录的场景，验证 `filter=我已审批` 结果中该合同只出现一次
    - 测试文件：`backend/tests/test_contract_service_properties.py`

  - [ ]* 5.6 为 comment_service 和 review_service 改造编写集成测试
    - 测试 `POST /api/contracts/{id}/comments`（含 `mentioned_user_ids`）后通知记录正确生成
    - 测试 `POST /api/contracts/{id}/reviews/{id}/approve` 后通知记录正确生成
    - 测试 `mentioned_user_ids` 超过10个时返回 422
    - 测试文件：`backend/tests/test_comment_review_integration.py`
    - _Requirements: 1.6, 1.7, 2.1, 2.2, 2.4_

- [x] 6. 阶段3检查点 - 验证后端业务逻辑
  - 确认 `GET /api/contracts?filter=all` 只返回与当前用户有关的合同
  - 确认 `GET /api/contracts?filter=我已审批` 返回去重结果
  - 确认评论和审批操作后通知记录正确写入 notifications 表
  - 如有问题请告知

- [x] 7. 阶段4：前端类型和 Store（依赖阶段3）
  - [x] 7.1 更新 types/index.ts（新增 Notification 类型，扩展 FilterType 和 Comment）
    - 修改 `frontend/src/types/index.ts`
    - `FilterType` 新增 `'我已审批'`
    - `Comment` 接口新增 `mentionedUserIds?: string[]`
    - 新增类型：
      ```typescript
      export type NotificationType = 'review_approved' | 'comment_added' | 'comment_replied' | 'user_mentioned';
      export interface Notification { id, type, actorId, actor?, contractId, contractName?, anchorId?, preview?, isRead, createdAt }
      export interface NotificationListResponse { notifications, total, page, pageSize }
      ```
    - _Requirements: 2.7, 2.9, 3.1_

  - [x] 7.2 新建 useNotificationStore
    - 新建文件 `frontend/src/stores/useNotificationStore.ts`
    - 使用 Zustand 定义 `NotificationState`：`unreadCount`、`notifications`、`setUnreadCount`、`addNotification`、`markAsRead`、`markAllAsRead`
    - `addNotification` 将新通知插入列表头部
    - `markAsRead` 更新对应通知的 `isRead` 为 true，并将 `unreadCount` 减1（最小为0）
    - `markAllAsRead` 将所有通知 `isRead` 设为 true，`unreadCount` 设为 0
    - _Requirements: 2.7, 2.8, 2.11, 2.12_

  - [x] 7.3 新建 useNotifications hooks
    - 新建文件 `frontend/src/hooks/useNotifications.ts`
    - 实现4个 hooks（使用 TanStack Query）：
      - `useNotificationList(page)` → `GET /api/notifications?page={page}&page_size=20`，成功后同步到 store
      - `useUnreadCount()` → `GET /api/notifications/unread-count`，成功后调用 `store.setUnreadCount()`
      - `useMarkNotificationRead()` → `PATCH /api/notifications/{id}/read`，成功后调用 `store.markAsRead(id)`，invalidate 相关 query
      - `useMarkAllRead()` → `POST /api/notifications/read-all`，成功后调用 `store.markAllAsRead()`，invalidate 相关 query
    - _Requirements: 2.9, 2.11, 2.12, 2.13_

  - [x] 7.4 在 useSocket.ts 中新增 notification:new 事件监听
    - 修改 `frontend/src/hooks/useSocket.ts`（或对应的 Socket.IO 初始化文件）
    - 新增监听：`socket.on('notification:new', (data: Notification) => { notificationStore.addNotification(data); notificationStore.setUnreadCount(prev => prev + 1); })`
    - 组件卸载时移除监听：`socket.off('notification:new')`
    - _Requirements: 2.6, 2.7_

- [x] 8. 阶段4检查点 - 验证前端类型和 Store
  - 确认 TypeScript 编译无类型错误
  - 确认 useNotificationStore 状态更新逻辑正确
  - 如有问题请告知

- [x] 9. 阶段5：前端组件（依赖阶段4）
  - [x] 9.1 改造 FilterBar（新增"我已审批"Tab）
    - 修改 `frontend/src/components/ContractList/FilterBar.tsx`
    - 在现有 `filters` 数组末尾追加 `{ key: '我已审批', label: '我已审批' }`
    - 确保 `FilterType` 类型已在 7.1 中更新，此处无需额外类型修改
    - _Requirements: 3.1, 3.4_

  - [x] 9.2 新建 useMention hook
    - 新建文件 `frontend/src/hooks/useMention.ts`
    - 实现 `UseMentionReturn` 接口：`mentionQuery`、`isMentionOpen`、`mentionedUserIds`、`handleInputChange`、`handleUserSelect`、`handleMentionClose`、`processContent`
    - `handleInputChange`：检测 `@` 字符，记录 `mentionStartIndex`，提取 `@` 后的搜索文本更新 `mentionQuery`
    - `handleUserSelect`：替换 `@{query}` 为 `@{用户姓名}`，将 `userId` 加入 `mentionedUserIds`，关闭 Picker
    - 当 `mentionedUserIds.length >= 10` 时，`handleInputChange` 不触发 Picker 展开
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_

  - [x] 9.3 新建 MentionPicker 组件
    - 新建文件 `frontend/src/components/Timeline/MentionPicker.tsx`
    - Props：`query`、`contractId`、`onSelect(user: User)`、`onClose`、`anchorEl`
    - 使用 `useQuery` + 200ms debounce 调用 `GET /api/users?search={query}&limit=20`
    - 候选列表优先展示合同参与者（发起人+评审人+抄送人），最多展示10条
    - 空结果显示"无匹配用户"
    - 使用 Ant Design `Dropdown` 或绝对定位 `div` 实现，点击外部区域触发 `onClose`
    - _Requirements: 1.1, 1.2, 1.4, 1.8_

  - [x] 9.4 改造 CommentInput（集成 @ 提及功能）
    - 修改 `frontend/src/components/Timeline/CommentInput.tsx`
    - 引入 `useMention` hook，将 `handleInputChange` 绑定到输入框 `onChange`
    - 在输入框下方条件渲染 `MentionPicker`（`isMentionOpen` 为 true 时展示）
    - 当 `mentionedUserIds.length >= 10` 时，在输入框下方显示"最多可提及 10 人"提示
    - 提交时将 `mentionedUserIds` 随 `content` 一起发送到后端
    - 监听 Escape 键触发 `handleMentionClose`
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6_

  - [ ]* 9.5 为 useMention hook 编写单元测试
    - 测试 `@` 触发 Picker 展开
    - 测试用户选中后内容替换和 `mentionedUserIds` 更新
    - 测试第11个用户不触发 Picker
    - 测试文件：`frontend/src/hooks/__tests__/useMention.test.ts`
    - _Requirements: 1.1, 1.3, 1.6_

  - [x] 9.6 新建 NotificationCenter 组件
    - 新建目录 `frontend/src/components/NotificationCenter/`
    - 新建 `NotificationCenter.tsx`：组合 `NotificationBell` 和 `NotificationList`，挂载时调用 `useUnreadCount()` 初始化未读数
    - 新建 `NotificationBell.tsx`：Ant Design `Badge`（count=`unreadCount`，`showZero=false`）+ `BellOutlined` 图标，点击切换列表展开/收起
    - 新建 `NotificationList.tsx`：使用 Ant Design `Popover` 或 `Drawer`，调用 `useNotificationList(page)` 加载数据，支持分页（每页20条），顶部显示"全部标为已读"按钮
    - 新建 `NotificationItem.tsx`：展示操作类型、操作人姓名、合同名称、相对时间（刚刚/X分钟前/X小时前/具体日期），未读条目高亮背景，点击触发跳转定位逻辑
    - 跳转定位逻辑：标记已读 → 切换合同 → 300ms 后 `scrollIntoView` + 添加 `highlight-flash` CSS 类 → 3秒后移除；关联内容已删除时显示 `message.info('该内容已被删除')`
    - 新增 CSS：`highlight-flash` 动画（黄色背景渐变，持续3秒）
    - _Requirements: 2.7, 2.8, 2.9, 2.10, 2.11, 2.12, 2.13, 2.14_

  - [ ]* 9.7 为 NotificationCenter 编写属性测试
    - **Property 4: 通知持久化优先**
    - **Validates: Requirements 2.6**
    - 模拟 Socket.IO 不可用场景，验证通知仍可通过 `GET /api/notifications` 接口获取
    - 测试文件：`frontend/src/components/NotificationCenter/__tests__/NotificationCenter.test.tsx`

  - [ ]* 9.8 为 NotificationCenter 编写属性测试（缓存一致性）
    - **Property 6: 缓存一致性**
    - **Validates: Requirements 2.11, 2.12**
    - 验证标记已读后 `unreadCount` 正确递减，全部已读后 `unreadCount` 为0
    - 测试文件：`frontend/src/components/NotificationCenter/__tests__/NotificationCenter.test.tsx`

  - [x] 9.9 集成 NotificationCenter 到 ContractBoard 顶部
    - 修改 `frontend/src/pages/ContractBoard.tsx`
    - 在顶部 Header 区域引入并渲染 `<NotificationCenter />`
    - 确保 `useSocket` 的 `notification:new` 监听在此页面生效
    - _Requirements: 2.7_

  - [ ]* 9.10 为 @ 提及上限编写属性测试
    - **Property 5: @ 提及上限**
    - **Validates: Requirements 1.6**
    - 使用 hypothesis 生成长度超过10的 `mentioned_user_ids` 列表，验证后端返回 422
    - 测试文件：`backend/tests/test_mention_limit_property.py`

- [x] 10. 最终检查点 - 确保所有测试通过
  - 确保所有测试通过，ask the user if questions arise.

## Notes

- 标有 `*` 的子任务为可选项，可跳过以加快 MVP 交付
- 每个任务均引用具体需求条款以保证可追溯性
- 阶段间检查点确保增量验证，降低集成风险
- Property 测试验证系统级不变量（自通知、权限隔离、去重、持久化、上限、缓存一致性）
- Socket.IO 推送失败时静默忽略，通知已持久化，不影响核心功能

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["3.1", "3.2"] },
    { "id": 2, "tasks": ["3.3", "3.6", "3.7"] },
    { "id": 3, "tasks": ["3.4", "3.5", "5.1"] },
    { "id": 4, "tasks": ["5.2", "5.3", "5.4"] },
    { "id": 5, "tasks": ["5.5", "5.6", "7.1"] },
    { "id": 6, "tasks": ["7.2", "7.3", "7.4"] },
    { "id": 7, "tasks": ["9.1", "9.2"] },
    { "id": 8, "tasks": ["9.3", "9.6"] },
    { "id": 9, "tasks": ["9.4", "9.7", "9.8"] },
    { "id": 10, "tasks": ["9.5", "9.9", "9.10"] }
  ]
}
```
