# Design Document - Contract Enhancements

## Overview

本文档描述在现有合同预审看板系统基础上新增四项功能的技术设计：评论 @ 提及用户、消息通知机制、"我已审批"筛选项、数据权限隔离。

所有改动均在现有技术栈（FastAPI + PostgreSQL + Redis + Socket.IO / React + Ant Design + Zustand + TanStack Query）上进行增量扩展，不引入新的基础设施依赖。

---

## Architecture

### 改动范围总览

```
┌─────────────────────────────────────────────────────────────┐
│                     前端层 (React)                           │
│                                                             │
│  ① MentionInput      ← 需求1: @ 提及（改造 CommentInput）   │
│  ② NotificationCenter ← 需求2: 通知中心（新增组件）         │
│  ③ FilterBar         ← 需求3: 新增"我已审批"Tab             │
│  （无前端改动）       ← 需求4: 纯后端权限过滤               │
└─────────────────────────────────────────────────────────────┘
                          │ HTTP + Socket.IO
┌─────────────────────────────────────────────────────────────┐
│                     后端层 (FastAPI)                         │
│                                                             │
│  comment_service.py  ← 需求1: 写入 mentioned_user_ids       │
│  notification_service.py ← 需求2: 新增通知服务              │
│  routes/notifications.py ← 需求2: 新增通知路由              │
│  contract_service.py ← 需求3+4: 扩展 _apply_filter()        │
│  routes/users.py     ← 需求1: 确认用户搜索接口              │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                     数据层                                   │
│                                                             │
│  comments 表         ← 需求1: 新增 mentioned_user_ids 列    │
│  notifications 表    ← 需求2: 新建表                        │
│  （无 Schema 变更）  ← 需求3+4: 纯查询逻辑变更              │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

**需求1 @ 提及流程：**
```
用户输入 @ → MentionInput 弹出 Mention_Picker
→ 搜索 GET /api/users?search=xxx
→ 选中用户，插入 @{姓名} 文本
→ 提交评论 POST /api/contracts/{id}/comments { content, mentioned_user_ids }
→ comment_service 写入 DB
→ notification_service 为每个 mentioned_user 生成 user_mentioned 通知
→ Socket.IO 推送 notification:new 事件
```

**需求2 通知流程：**
```
触发操作（审批/评论/回复/@ 提及）
→ 对应 service 调用 notification_service.create_notification()
→ 写入 notifications 表
→ Socket.IO 推送 notification:new 到接收人房间
→ 前端 NotificationCenter 更新 Unread_Count 角标
→ 用户点击通知 → PATCH /api/notifications/{id}/read
→ 前端跳转合同 + 滚动到 anchor + 高亮 3 秒
```

---

## Components and Interfaces

### 前端新增/改造组件

#### 1. MentionInput（改造 CommentInput）

**文件：** `frontend/src/components/Timeline/CommentInput.tsx`（改造）

**核心逻辑：**
- 监听 `onChange`，检测 `@` 字符触发 Mention_Picker
- 使用 `useRef` 记录当前 `@` 触发位置（`mentionStartIndex`）
- 维护 `mentionQuery` state（`@` 后的搜索文本）
- 选中用户后替换 `@{query}` 为 `@{用户姓名}`，并将 `userId` 加入 `mentionedUserIds` 数组
- 提交时将 `mentionedUserIds` 随 `content` 一起发送

**新增 Hook：** `frontend/src/hooks/useMention.ts`
```typescript
interface UseMentionReturn {
  mentionQuery: string;           // @ 后的搜索文本
  isMentionOpen: boolean;         // Picker 是否展开
  mentionedUserIds: string[];     // 已选中的用户 ID 列表
  handleInputChange: (value: string) => void;
  handleUserSelect: (user: User) => void;
  handleMentionClose: () => void;
  processContent: (raw: string) => string; // 提取 @{姓名} 并映射 ID
}
```

**用户搜索：** 复用现有 `GET /api/users` 接口（需确认支持 `?search=` 参数），使用 `useQuery` + 200ms debounce。

#### 2. MentionPicker（新增子组件）

**文件：** `frontend/src/components/Timeline/MentionPicker.tsx`

```typescript
interface MentionPickerProps {
  query: string;
  contractId: string;       // 用于优先展示合同参与者
  onSelect: (user: User) => void;
  onClose: () => void;
  anchorEl: HTMLElement | null; // 定位参考元素
}
```

- 使用 Ant Design `Dropdown` 或绝对定位 `div` 实现
- 候选列表：先展示合同参与者（发起人+评审人+抄送人），再展示全员搜索结果
- 最多展示 10 条候选
- 空结果显示"无匹配用户"

#### 3. NotificationCenter（新增组件）

**文件：** `frontend/src/components/NotificationCenter/NotificationCenter.tsx`

```typescript
interface NotificationCenterProps {
  // 无 Props，从 store 读取数据
}
```

**子组件：**
- `NotificationBell`：铃铛图标 + 未读数角标（Ant Design `Badge` + `BellOutlined`）
- `NotificationList`：通知列表（Ant Design `Popover` 或 `Drawer`）
- `NotificationItem`：单条通知展示

**集成位置：** `frontend/src/pages/ContractBoard.tsx` 顶部 Header 区域

**新增 Store：** `frontend/src/stores/useNotificationStore.ts`
```typescript
interface NotificationState {
  unreadCount: number;
  notifications: Notification[];
  setUnreadCount: (count: number) => void;
  addNotification: (n: Notification) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
}
```

**新增 Hook：** `frontend/src/hooks/useNotifications.ts`
```typescript
// 获取通知列表
function useNotificationList(page: number): QueryResult<NotificationListResponse>
// 获取未读数
function useUnreadCount(): QueryResult<number>
// 标记已读
function useMarkNotificationRead(): MutationResult
// 全部已读
function useMarkAllRead(): MutationResult
```

**Socket.IO 事件监听：** 在现有 `useSocket.ts` 中新增：
```typescript
socket.on('notification:new', (data: Notification) => {
  notificationStore.addNotification(data);
  notificationStore.setUnreadCount(prev => prev + 1);
});
```

**点击通知跳转定位：**
```typescript
const handleNotificationClick = async (notification: Notification) => {
  // 1. 标记已读
  await markAsRead(notification.id);
  // 2. 切换合同
  setSelectedContractId(notification.contractId);
  // 3. 等待渲染后滚动
  setTimeout(() => {
    const el = document.getElementById(`anchor-${notification.anchorId}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('highlight-flash'); // CSS 动画 3 秒
      setTimeout(() => el.classList.remove('highlight-flash'), 3000);
    } else {
      // 关联内容已删除
      message.info('该内容已被删除');
    }
  }, 300);
};
```

#### 4. FilterBar 改造

**文件：** `frontend/src/components/ContractList/FilterBar.tsx`

在现有 `filters` 数组末尾追加：
```typescript
{ key: '我已审批', label: '我已审批' }
```

**类型更新：** `frontend/src/types/index.ts`
```typescript
export type FilterType =
  | 'all' | '进行中' | '已完成' | '待我处理'
  | '抄送我' | '我发起的' | '我已审批';  // 新增
```

---

### 后端新增/改造模块

#### 1. Comment 模型扩展

**文件：** `backend/app/models/comment.py`

新增字段：
```python
mentioned_user_ids: Mapped[list[str]] = mapped_column(
    ARRAY(String),
    nullable=False,
    default=list,
    comment="被@提及的用户ID列表"
)
```

**Alembic 迁移：**
```python
# alembic/versions/xxxx_add_mentioned_user_ids_to_comments.py
def upgrade():
    op.add_column('comments',
        sa.Column('mentioned_user_ids', postgresql.ARRAY(sa.String()),
                  nullable=False, server_default='{}')
    )

def downgrade():
    op.drop_column('comments', 'mentioned_user_ids')
```

#### 2. Notification 模型（新建）

**文件：** `backend/app/models/notification.py`

```python
class NotificationType(str, enum.Enum):
    REVIEW_APPROVED = "review_approved"
    COMMENT_ADDED = "comment_added"
    COMMENT_REPLIED = "comment_replied"
    USER_MENTIONED = "user_mentioned"

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType, ...), nullable=False)
    contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    anchor_id: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="关联的评论或评审ID，用于前端定位")
    preview: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="内容预览")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    recipient: Mapped["User"] = relationship("User", foreign_keys=[recipient_id])
    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])
    contract: Mapped["Contract"] = relationship("Contract", foreign_keys=[contract_id])

    __table_args__ = (
        Index('ix_notifications_recipient_read', 'recipient_id', 'is_read'),
        Index('ix_notifications_created_at_desc', 'created_at', postgresql_ops={'created_at': 'DESC'}),
    )
```

**Alembic 迁移：**
```python
# alembic/versions/xxxx_create_notifications_table.py
def upgrade():
    op.create_table('notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.Enum('review_approved','comment_added','comment_replied','user_mentioned', name='notification_type'), nullable=False),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('anchor_id', sa.String(100), nullable=True),
        sa.Column('preview', sa.String(200), nullable=True),
        sa.Column('is_read', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_notifications_recipient_read', 'notifications', ['recipient_id', 'is_read'])
    op.create_index('ix_notifications_created_at_desc', 'notifications', ['created_at'])

def downgrade():
    op.drop_table('notifications')
    op.execute("DROP TYPE IF EXISTS notification_type")
```

#### 3. NotificationService（新建）

**文件：** `backend/app/services/notification_service_v2.py`（或扩展现有 `notification_service.py`）

```python
class NotificationServiceV2:

    async def create_notification(
        self,
        recipient_id: str,
        actor_id: str,
        notification_type: NotificationType,
        contract_id: str,
        anchor_id: str | None,
        preview: str | None,
        db: AsyncSession
    ) -> Notification | None:
        """创建通知，自动跳过自通知"""
        if str(recipient_id) == str(actor_id):
            return None  # 不给自己发通知

        notification = Notification(
            recipient_id=recipient_id,
            actor_id=actor_id,
            type=notification_type,
            contract_id=contract_id,
            anchor_id=anchor_id,
            preview=preview[:200] if preview else None,
        )
        db.add(notification)
        await db.flush()

        # 通过 Socket.IO 推送
        await self._push_to_socket(notification, db)

        # 清除未读数缓存
        await redis_client.delete(f"notification:unread:{recipient_id}")

        return notification

    async def create_review_approved_notification(
        self, review: Review, db: AsyncSession
    ):
        """审批通过通知 → 发给合同发起人"""
        contract = await self._get_contract(review.contract_id, db)
        await self.create_notification(
            recipient_id=str(contract.initiator_id),
            actor_id=str(review.reviewer_id),
            notification_type=NotificationType.REVIEW_APPROVED,
            contract_id=str(review.contract_id),
            anchor_id=str(review.id),
            preview=f"{review.reviewer.name} 审批通过了合同",
            db=db
        )

    async def create_comment_added_notification(
        self, comment: Comment, db: AsyncSession
    ):
        """新评论通知 → 发给合同发起人（顶层评论）"""
        contract = await self._get_contract(comment.contract_id, db)
        await self.create_notification(
            recipient_id=str(contract.initiator_id),
            actor_id=str(comment.author_id),
            notification_type=NotificationType.COMMENT_ADDED,
            contract_id=str(comment.contract_id),
            anchor_id=str(comment.id),
            preview=comment.content[:100],
            db=db
        )

    async def create_comment_replied_notification(
        self, comment: Comment, db: AsyncSession
    ):
        """回复通知 → 发给被回复的评论作者"""
        if not comment.parent_comment_id:
            return
        parent = await self._get_comment(comment.parent_comment_id, db)
        await self.create_notification(
            recipient_id=str(parent.author_id),
            actor_id=str(comment.author_id),
            notification_type=NotificationType.COMMENT_REPLIED,
            contract_id=str(comment.contract_id),
            anchor_id=str(comment.id),
            preview=comment.content[:100],
            db=db
        )

    async def create_mention_notifications(
        self, comment: Comment, db: AsyncSession
    ):
        """@ 提及通知 → 发给每个被提及的用户"""
        for user_id in (comment.mentioned_user_ids or []):
            await self.create_notification(
                recipient_id=user_id,
                actor_id=str(comment.author_id),
                notification_type=NotificationType.USER_MENTIONED,
                contract_id=str(comment.contract_id),
                anchor_id=str(comment.id),
                preview=comment.content[:100],
                db=db
            )

    async def get_notifications(
        self, recipient_id: str, page: int, page_size: int, db: AsyncSession
    ) -> dict:
        query = select(Notification).options(
            selectinload(Notification.actor),
            selectinload(Notification.contract)
        ).where(
            Notification.recipient_id == recipient_id
        ).order_by(Notification.created_at.desc())

        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        items = (await db.execute(query.offset((page-1)*page_size).limit(page_size))).scalars().all()

        return {"notifications": items, "total": total, "page": page, "page_size": page_size}

    async def get_unread_count(self, recipient_id: str, db: AsyncSession) -> int:
        cache_key = f"notification:unread:{recipient_id}"
        cached = await redis_client.get(cache_key)
        if cached is not None:
            return int(cached)

        count = await db.scalar(
            select(func.count()).select_from(Notification).where(
                Notification.recipient_id == recipient_id,
                Notification.is_read == False
            )
        )
        await redis_client.set(cache_key, str(count), ex=60)
        return count

    async def mark_as_read(self, notification_id: str, recipient_id: str, db: AsyncSession):
        await db.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.recipient_id == recipient_id)
            .values(is_read=True)
        )
        await db.commit()
        await redis_client.delete(f"notification:unread:{recipient_id}")

    async def mark_all_as_read(self, recipient_id: str, db: AsyncSession):
        await db.execute(
            update(Notification)
            .where(Notification.recipient_id == recipient_id, Notification.is_read == False)
            .values(is_read=True)
        )
        await db.commit()
        await redis_client.set(f"notification:unread:{recipient_id}", "0", ex=60)

    async def _push_to_socket(self, notification: Notification, db: AsyncSession):
        try:
            await notification_service.sio.emit(
                'notification:new',
                {
                    "id": str(notification.id),
                    "type": notification.type,
                    "contractId": str(notification.contract_id),
                    "anchorId": notification.anchor_id,
                    "preview": notification.preview,
                    "createdAt": notification.created_at.isoformat(),
                },
                room=f"user:{notification.recipient_id}"
            )
        except Exception:
            pass  # Socket.IO 不可用时静默失败，通知已持久化
```

#### 4. 通知路由（新建）

**文件：** `backend/app/routes/notifications.py`

```
GET  /api/notifications                    # 获取通知列表（?page=1&page_size=20）
GET  /api/notifications/unread-count       # 获取未读数
PATCH /api/notifications/{id}/read        # 标记单条已读
POST /api/notifications/read-all          # 全部标为已读
```

#### 5. comment_service.py 改造

在 `create_comment` 方法中：
1. 接收 `mentioned_user_ids: list[str]` 参数
2. 写入 `comment.mentioned_user_ids`
3. 调用 `notification_service_v2.create_comment_added_notification()`
4. 调用 `notification_service_v2.create_comment_replied_notification()`
5. 调用 `notification_service_v2.create_mention_notifications()`

#### 6. review_service.py 改造

在 `approve_review` 方法中，事务提交后调用：
```python
await notification_service_v2.create_review_approved_notification(review, db)
```

#### 7. contract_service.py 改造（需求3+4）

**`_apply_filter` 方法扩展：**

```python
def _build_visibility_subquery(self, user_id: str):
    """构建当前用户可见合同的子查询（需求4）"""
    initiated = select(Contract.id).where(Contract.initiator_id == user_id)
    cc_to_me = select(Contract.id).where(Contract.cc_users.contains([user_id]))
    as_reviewer = select(Review.contract_id).where(Review.reviewer_id == user_id)
    return initiated.union(cc_to_me).union(as_reviewer)

async def _apply_filter(self, query, user_id: str, filter_type: str, db: AsyncSession):
    if filter_type == "all":
        # 需求4: 只返回与我有关的合同
        visible = self._build_visibility_subquery(user_id)
        query = query.where(Contract.id.in_(visible))

    elif filter_type == "进行中":
        # 需求4: 权限过滤 + 状态过滤
        visible = self._build_visibility_subquery(user_id)
        query = query.where(and_(Contract.status == "progress", Contract.id.in_(visible)))

    elif filter_type == "已完成":
        # 需求4: 权限过滤 + 状态过滤
        visible = self._build_visibility_subquery(user_id)
        query = query.where(and_(Contract.status == "completed", Contract.id.in_(visible)))

    elif filter_type == "待我处理":
        subquery = select(Review.contract_id).where(
            and_(Review.reviewer_id == user_id, Review.status == "pending")
        ).distinct()
        query = query.where(Contract.id.in_(subquery))

    elif filter_type == "抄送我":
        query = query.where(Contract.cc_users.contains([user_id]))

    elif filter_type == "我发起的":
        query = query.where(Contract.initiator_id == user_id)

    elif filter_type == "我已审批":
        # 需求3: 我已审批通过的合同（去重）
        subquery = select(Review.contract_id).where(
            and_(Review.reviewer_id == user_id, Review.status == "approved")
        ).distinct()
        query = query.where(Contract.id.in_(subquery))

    return query
```

#### 8. 评论接口扩展

**`AddCommentRequest`（`routes/contracts.py` 和 `routes/reviews.py`）：**
```python
class AddCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    review_id: Optional[str] = None
    parent_comment_id: Optional[str] = None
    mentioned_user_ids: Optional[List[str]] = Field(default=[], max_items=10)  # 新增
```

#### 9. 用户搜索接口确认

**文件：** `backend/app/routes/users.py`

确认或新增：
```
GET /api/users?search=张&limit=20
```
返回 `[{ id, name, avatar, department }]`，用于 Mention_Picker 搜索。

---

## Data Models

### 数据库变更汇总

| 变更类型 | 表/字段 | 说明 |
|---------|---------|------|
| 新增列 | `comments.mentioned_user_ids` | `VARCHAR[] NOT NULL DEFAULT '{}'` |
| 新建表 | `notifications` | 通知记录表 |
| 新建索引 | `ix_notifications_recipient_read` | 加速未读查询 |
| 新建索引 | `ix_notifications_created_at_desc` | 加速列表排序 |

### Notification 数据结构（前端类型）

```typescript
// frontend/src/types/index.ts 新增
export type NotificationType =
  | 'review_approved'
  | 'comment_added'
  | 'comment_replied'
  | 'user_mentioned';

export interface Notification {
  id: string;
  type: NotificationType;
  actorId: string;
  actor?: User;
  contractId: string;
  contractName?: string;
  anchorId?: string;
  preview?: string;
  isRead: boolean;
  createdAt: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  page: number;
  pageSize: number;
}
```

### Comment 类型扩展

```typescript
// frontend/src/types/index.ts 修改
export interface Comment {
  // ... 现有字段 ...
  mentionedUserIds?: string[];  // 新增
}
```

### Redis 缓存新增

| 缓存键 | 内容 | TTL |
|--------|------|-----|
| `notification:unread:{userId}` | 未读通知数量（整数字符串） | 60 秒 |

缓存失效时机：
- 创建新通知时删除接收人的未读数缓存
- 标记已读时删除接收人的未读数缓存

---

## API Interfaces

### 新增 API 端点

#### 通知相关

```
GET /api/notifications
  Query: page=1, page_size=20
  Response: { success, data: NotificationListResponse }

GET /api/notifications/unread-count
  Response: { success, data: { count: number } }

PATCH /api/notifications/{id}/read
  Response: { success, data: { id, is_read: true } }

POST /api/notifications/read-all
  Response: { success, data: { updated_count: number } }
```

#### 用户搜索（确认/新增）

```
GET /api/users?search=xxx&limit=20
  Response: { success, data: { users: User[] } }
```

### 修改的 API 端点

#### 评论接口（新增 mentioned_user_ids 字段）

```
POST /api/contracts/{id}/comments
  Body: { content, review_id?, parent_comment_id?, mentioned_user_ids?: string[] }
  Response: { success, data: { comment: Comment } }  // comment 包含 mentionedUserIds
```

### Socket.IO 新增事件

```
# 服务端 → 客户端
notification:new  →  { id, type, contractId, anchorId, preview, createdAt }
```

---

## Error Handling

### 通知相关错误处理

| 场景 | 处理方式 |
|------|---------|
| Socket.IO 推送失败 | 静默失败，通知已持久化，用户下次请求时可获取 |
| 通知关联内容已删除 | 前端跳转合同页，显示"该内容已被删除"提示 |
| 标记已读时通知不存在 | 返回 404，前端忽略错误 |

### 权限过滤错误处理

| 场景 | 处理方式 |
|------|---------|
| JWT 缺失/无效/过期 | 现有 AuthMiddleware 返回 401，无需额外处理 |
| 用户 ID 无法从 Token 解析 | 现有 `get_current_user()` 抛出 401 |

### @ 提及错误处理

| 场景 | 处理方式 |
|------|---------|
| `mentioned_user_ids` 包含无效 ID | 后端静默忽略，不报错 |
| 超过 10 人限制 | 前端阻止，后端 `max_items=10` 校验返回 422 |

---

## Testing Strategy

### 单元测试重点

**后端：**
- `NotificationServiceV2.create_notification()` - 验证自通知跳过逻辑
- `NotificationServiceV2.create_review_approved_notification()` - 验证接收人为发起人
- `contract_service._build_visibility_subquery()` - 验证三种可见性条件的 OR 逻辑
- `contract_service._apply_filter("我已审批")` - 验证去重逻辑

**前端：**
- `useMention` hook - 验证 `@` 触发、用户选中、内容替换逻辑
- `NotificationCenter` - 验证未读数角标显示/隐藏
- `FilterBar` - 验证"我已审批"Tab 渲染

### 集成测试重点

- `POST /api/contracts/{id}/comments`（含 `mentioned_user_ids`）→ 验证通知生成
- `POST /api/contracts/{id}/reviews/{id}/approve` → 验证通知生成
- `GET /api/contracts?filter=all` → 验证只返回与当前用户有关的合同
- `GET /api/contracts?filter=我已审批` → 验证去重和排序

### 迁移验证

部署前需验证：
1. `alembic upgrade head` 成功执行两个迁移
2. 现有评论数据的 `mentioned_user_ids` 默认为空数组
3. 现有合同列表在权限过滤后结果符合预期（不影响已有用户的可见合同）

---

## Correctness Properties

### Property 1: 自通知不生成
`actor_id == recipient_id` 时，`create_notification` 必须返回 `None` 且不写入数据库。

**Validates: Requirements 2.5**

### Property 2: 权限隔离完整性
`filter=all/进行中/已完成` 返回的合同集合，不包含与当前用户无任何关联的合同（即不是发起人、不是评审人、不在抄送列表中的合同不可见）。

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 3: 我已审批去重
同一合同有多条 `approved` 评审记录时，该合同在 `filter=我已审批` 结果中只出现一次。

**Validates: Requirements 3.2**

### Property 4: 通知持久化优先
Socket.IO 推送失败不影响通知写入数据库，用户下次拉取通知列表时仍可获取未读通知。

**Validates: Requirements 2.6**

### Property 5: @ 提及上限
单条评论的 `mentioned_user_ids` 长度不超过 10，超出时后端返回 422 错误。

**Validates: Requirements 1.6**

### Property 6: 缓存一致性
标记已读操作完成后，`notification:unread:{userId}` 缓存必须被删除或更新，确保下次查询返回最新未读数。

**Validates: Requirements 2.11, 2.12**
