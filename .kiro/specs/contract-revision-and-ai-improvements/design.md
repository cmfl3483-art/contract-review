# Design Document - Contract Revision & AI Improvements

## Overview

本文档描述合同预审看板系统第三轮功能增强的技术设计，覆盖三个相互独立的增强：

1. **合同修改触发重新审批**（含审计日志、Socket.IO 推送、通知）
2. **@ 提及候选人范围限制**（新增合同维度的候选人接口）
3. **AI 合同预审助理改造**（结构化引用标记 + 前端折叠展示）

所有改动均在现有技术栈（FastAPI + PostgreSQL + Redis + Socket.IO / React + Ant Design + Zustand + TanStack Query）上增量扩展，不引入新基础设施。

---

## Architecture

### 改动范围总览

```
┌─────────────────────────────────────────────────────────────┐
│                     前端层 (React)                           │
│                                                             │
│  ① ContractDetail / 编辑模式  ← 需求1: 发起人编辑面板        │
│  ② MentionPicker             ← 需求2: 改用合同维度接口      │
│  ③ AIAdvisor / Message       ← 需求3: 引用链接 + 折叠       │
│  ④ NotificationCenter         ← 需求1: 新增 contract_revised │
└─────────────────────────────────────────────────────────────┘
                          │ HTTP + Socket.IO
┌─────────────────────────────────────────────────────────────┐
│                     后端层 (FastAPI)                         │
│                                                             │
│  routes/contracts.py    ← 需求1: 新增 PATCH 端点 + 权限      │
│  services/contract_service.py ← 需求1: revise_contract()    │
│  routes/files.py        ← 需求1: 上传附件后触发重审         │
│  routes/contracts.py    ← 需求2: 新增 mentionable-users 端点 │
│  services/ai_service.py ← 需求3: prompt 改造 + 引用标记      │
│  services/notification_service_v2.py ← 需求1: contract_revised │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                     数据层                                   │
│                                                             │
│  contract_revision_logs 表  ← 需求1: 新建（审计日志）       │
│  notifications.type 枚举    ← 需求1: 新增 contract_revised  │
│  （无 Schema 变更）         ← 需求2+3: 纯查询/UI 改动       │
└─────────────────────────────────────────────────────────────┘
```

### 关键数据流

**需求 1 重审流程：**
```
Initiator 编辑合同 → PATCH /api/contracts/{id} 或上传附件
  → contract_service.revise_contract() 启动事务
    → 校验权限（initiator + progress）
    → 校验输入（name 长度、description 长度、文件大小）
    → 检测实际值变更（normalize 后比较）
    → UPDATE contracts SET name/description = ...
    → UPDATE reviews SET status='pending' WHERE contract_id = ...
    → INSERT INTO contract_revision_logs (...)
  → 提交事务
  → 异步：Socket.IO 推送 contract:revised 给所有 Reviewer
  → 异步：notification_service_v2.create_contract_revised_notifications()
  → 清除相关缓存（合同列表、待办数量、合同详情）
```

**需求 3 AI 引用渲染：**
```
用户问"总结" → AI_Service 调用 _ai_summary
  → system prompt 指示模型使用 [ref:review-{id}] / [ref:comment-{id}] 标记
  → 后端将 LLM 返回的纯文本作为 answer 返回（不解析）
  → 前端 AIAdvisor 拿到 answer
  → MessageContent 组件解析文本，正则匹配 [ref:...]
  → 把每个匹配渲染为 <button> 或 <a>，点击调 useFocusedAnchorStore + setSelectedContractId
  → 复用现有跳转 + 高亮 3 秒机制
```

---

## Components and Interfaces

### 后端新增/改造模块

#### 1. 数据库 Schema 变更

**`contract_revision_logs` 表（新建）：**

```python
# backend/app/models/contract_revision_log.py
class ContractRevisionLog(Base):
    __tablename__ = "contract_revision_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    revised_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 变更字段列表，PostgreSQL ARRAY，取值：'name' | 'description' | 'attachment'
    changed_fields: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False
    )
    revised_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    contract: Mapped["Contract"] = relationship("Contract", foreign_keys=[contract_id])
    revised_by_user: Mapped["User"] = relationship("User", foreign_keys=[revised_by])

    __table_args__ = (
        Index('ix_revision_logs_contract_revised_at', 'contract_id', 'revised_at'),
    )
```

**`notification_type` 枚举扩展：**
- 新增枚举值 `contract_revised`
- 通过 Alembic 迁移 `ALTER TYPE notification_type ADD VALUE 'contract_revised'`

**Alembic 迁移：**
```python
# backend/alembic/versions/xxxx_add_contract_revision_logs_and_revised_type.py
def upgrade():
    # 扩展 notification_type 枚举
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'contract_revised'")
    
    # 创建 contract_revision_logs 表
    op.execute("""
        CREATE TABLE IF NOT EXISTS contract_revision_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
            revised_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            changed_fields VARCHAR[] NOT NULL,
            revised_at TIMESTAMP NOT NULL DEFAULT now()
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_revision_logs_contract_revised_at
        ON contract_revision_logs (contract_id, revised_at DESC);
    """)

def downgrade():
    op.execute("DROP TABLE IF EXISTS contract_revision_logs")
    # PostgreSQL 不支持移除单个枚举值，downgrade 不处理
```

#### 2. ContractService 改造（需求1）

**新增方法：** `backend/app/services/contract_service.py`

```python
class ContractService:
    async def revise_contract(
        self,
        contract_id: str,
        user_id: str,
        new_name: Optional[str] = None,
        new_description: Optional[str] = None,
        attachment_added: bool = False,  # 是否新增了附件（由文件上传路径调用）
        db: AsyncSession = None,
    ) -> Contract:
        """
        修改合同关键字段并触发重新审批流程。
        
        Returns:
            更新后的 Contract 对象
        Raises:
            HTTPException(403): 非发起人
            HTTPException(409): 合同已完成
            HTTPException(422): 输入超限
            HTTPException(404): 合同不存在
        """
        async with db.begin():
            # 1. 锁住合同行（FOR UPDATE 避免并发）
            stmt = select(Contract).where(Contract.id == contract_id).with_for_update()
            contract = (await db.execute(stmt)).scalar_one_or_none()
            
            if not contract:
                raise HTTPException(404, "合同不存在")
            if str(contract.initiator_id) != str(user_id):
                raise HTTPException(403, "仅合同发起人可修改")
            if contract.status == "completed":
                raise HTTPException(409, "已完成的合同不允许修改")
            
            # 2. 校验输入（仅非 None 的字段才校验）
            changed_fields = []
            if new_name is not None:
                normalized = new_name.strip()
                if not (1 <= len(normalized) <= 200):
                    raise HTTPException(422, {"field": "name", "limit": "1-200 字符"})
                if normalized != (contract.name or "").strip():
                    contract.name = normalized
                    changed_fields.append("name")
            
            if new_description is not None:
                if len(new_description) > 5000:
                    raise HTTPException(422, {"field": "description", "limit": "≤5000 字符"})
                if (new_description or "").strip() != (contract.description or "").strip():
                    contract.description = new_description
                    changed_fields.append("description")
            
            if attachment_added:
                changed_fields.append("attachment")
            
            # 3. 没有实际变更，直接返回（不触发重审）
            if not changed_fields:
                await db.refresh(contract)
                return contract
            
            # 4. 重置所有 reviews 为 pending
            await db.execute(
                update(Review)
                .where(Review.contract_id == contract_id)
                .values(status="pending", updated_at=datetime.utcnow())
            )
            
            # 5. 写审计日志
            log = ContractRevisionLog(
                contract_id=contract_id,
                revised_by=user_id,
                changed_fields=changed_fields,
            )
            db.add(log)
            
            await db.commit()
        
        await db.refresh(contract)
        
        # 6. 事务外：推送 + 通知（失败不回滚事务）
        await self._notify_revision(contract, changed_fields, db)
        
        # 7. 清缓存
        await cache_invalidation.invalidate_contract_updated(
            contract_id=contract_id,
            affected_user_ids=self._get_affected_user_ids(contract, db),
        )
        
        return contract

    async def _notify_revision(
        self, contract: Contract, changed_fields: list[str], db: AsyncSession
    ):
        # Socket.IO 推送给所有评审人
        from app.core.socketio_server import sio
        reviews = (await db.execute(
            select(Review).where(Review.contract_id == contract.id)
        )).scalars().all()
        
        payload = {
            "contractId": str(contract.id),
            "contractName": contract.name,
            "changedFields": changed_fields,
        }
        for review in reviews:
            try:
                await sio.emit(
                    "contract:revised",
                    payload,
                    room=f"user:{review.reviewer_id}",
                )
            except Exception:
                pass  # 静默失败
        
        # 持久化通知
        await notification_service_v2.create_contract_revised_notifications(
            contract=contract,
            changed_fields=changed_fields,
            db=db,
        )
```

#### 3. ContractService API 路由扩展（需求1）

**`backend/app/routes/contracts.py` 新增端点：**

```python
class ReviseContractRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)

@router.patch("/{contract_id}")
async def revise_contract(
    contract_id: str,
    request: Request,
    data: ReviseContractRequest,
    db: AsyncSession = Depends(get_db),
):
    current_user = get_current_user(request)
    contract = await contract_service.revise_contract(
        contract_id=contract_id,
        user_id=current_user["user_id"],
        new_name=data.name,
        new_description=data.description,
        attachment_added=False,
        db=db,
    )
    return {"success": True, "data": {"contract": _serialize_contract(contract)}}
```

**附件上传路径（`backend/app/routes/files.py`）改造：**

在 `POST /api/contracts/{id}/attachments` 成功落库后调用：
```python
await contract_service.revise_contract(
    contract_id=contract_id,
    user_id=current_user["user_id"],
    attachment_added=True,
    db=db,
)
```

附件上传同样需要校验：
- 仅 Initiator 可上传（403）
- 仅 progress 状态可上传（409）
- 文件大小 ≤ 50MB（422）

#### 4. NotificationService 扩展（需求1）

**`backend/app/services/notification_service_v2.py` 新增方法：**

```python
async def create_contract_revised_notifications(
    self,
    contract: Contract,
    changed_fields: list[str],
    db: AsyncSession,
) -> None:
    """为合同所有评审人生成 contract_revised 通知"""
    reviews = (await db.execute(
        select(Review).where(Review.contract_id == contract.id)
    )).scalars().all()
    
    preview = f"{contract.name} 已修改：{', '.join(changed_fields)}，请重新审批"
    
    for review in reviews:
        await self.create_notification(
            recipient_id=str(review.reviewer_id),
            actor_id=str(contract.initiator_id),
            notification_type=NotificationType.CONTRACT_REVISED,
            contract_id=str(contract.id),
            anchor_id=None,  # 没有具体锚点，跳合同详情页即可
            preview=preview,
            db=db,
        )
```

**`backend/app/models/notification.py` 枚举扩展：**
```python
class NotificationType(str, enum.Enum):
    REVIEW_APPROVED = "review_approved"
    COMMENT_ADDED = "comment_added"
    COMMENT_REPLIED = "comment_replied"
    USER_MENTIONED = "user_mentioned"
    CONTRACT_REVISED = "contract_revised"  # 新增
```

#### 5. Mentionable Users API（需求2）

**`backend/app/routes/contracts.py` 新增端点：**

```python
@router.get("/{contract_id}/mentionable-users")
async def get_mentionable_users(
    contract_id: str,
    request: Request,
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    current_user = get_current_user(request)
    user_id = current_user["user_id"]
    
    # 1. 加载合同 + 评审人
    contract = (await db.execute(
        select(Contract)
        .options(selectinload(Contract.reviews).selectinload(Review.reviewer))
        .where(Contract.id == contract_id)
    )).scalar_one_or_none()
    
    if not contract:
        raise HTTPException(404, "合同不存在")
    
    # 2. 收集相关用户 ID
    related_ids = set()
    related_ids.add(str(contract.initiator_id))
    for review in contract.reviews:
        related_ids.add(str(review.reviewer_id))
    related_ids.update(contract.cc_users or [])
    
    # 3. 权限检查：当前用户必须是相关人员
    if str(user_id) not in related_ids:
        raise HTTPException(403, "您不是该合同的相关人员")
    
    # 4. 批量加载用户信息
    users = (await db.execute(
        select(User).where(User.id.in_(list(related_ids)))
    )).scalars().all()
    
    # 5. 应用搜索过滤
    search_value = (search or "").strip()
    if search_value and len(search_value) <= 50:
        lower = search_value.lower()
        users = [u for u in users if lower in (u.name or "").lower()]
    
    # 6. 排序 + 截断
    users.sort(key=lambda u: u.name or "")
    users = users[:100]
    
    return {
        "success": True,
        "data": {
            "users": [
                {
                    "id": str(u.id),
                    "name": u.name,
                    "avatar": u.avatar,
                    "department": u.department,
                }
                for u in users
            ]
        },
    }
```

#### 6. AI Service 改造（需求3）

**`backend/app/services/ai_service.py` 改动：**

修改 `_ai_summary` 方法的 system prompt，加入引用标记规则：

```python
system_prompt = (
    "你是「AI 合同预审助理」，负责对合同评审进度做简洁总结。\n\n"
    "输出格式严格如下，不要加多余标题或分隔线：\n\n"
    "⚠️ 当前风险/问题\n"
    "  逐条列出当前存在的风险和未解决的问题，指明是谁提出的、是否已有应对措施。\n\n"
    "👤 责任归属人\n"
    "  列出每个待处理事项对应的责任人（姓名+角色）及当前状态。\n\n"
    "📋 具体推进事项\n"
    "  列出接下来需要推进的具体事项，明确谁需要做什么。\n\n"
    "**引用规则（必须遵守）**：\n"
    "1. 当你在总结中引用某条评审意见时，在该引用之后追加结构化标记：[ref:review-{review_id}]\n"
    "2. 当你在总结中引用某条评论时，在该引用之后追加结构化标记：[ref:comment-{comment_id}]\n"
    "3. {review_id} 与 {comment_id} 必须严格使用上下文「评审进度」和「评论记录」中实际出现的 ID，禁止杜撰。\n"
    "4. 如果某条总结来自多条引用，可追加多个 [ref:...] 标记。\n"
    "5. 如果某条总结无具体引用来源，不追加标记。\n\n"
    "其他规则：\n"
    "1. 内容务必简洁，每条不超过两句话。\n"
    "2. 使用评审人和评论者的真实姓名。\n"
    "3. 总字数控制在 400 字以内（不含 [ref:...] 标记）。"
)
```

`_build_contract_context` 中已经有 `Review` 和 `Comment` 的 ID 信息（之前是 `name + role`），需要扩展为同时输出 ID 给 prompt 使用：

```python
sections.append(f"## 评审进度（共 {len(sorted_reviews)} 位评审人）")
for r in sorted_reviews:
    name = r.reviewer.name if r.reviewer else "未知用户"
    sections.append(
        f"- [review-{r.id}] {name}（{r.role}）：{status_text} | 意见：{opinion_text}"
    )
# ...
sections.append(f"## 评论记录（共 {len(all_comments)} 条）")
for c in all_comments:
    sections.append(
        f"- [comment-{c.id}] {author_name}{reply_to}：{c.content or ''}"
    )
```

**`answer_question` 不需要改动**——后端不解析 `[ref:...]`，原样返回给前端，由前端解析。

---

### 前端新增/改造组件

#### 1. ContractDetail 编辑模式（需求1）

**改造 `frontend/src/components/ContractDetail/ContractDetail.tsx`：**

新增"编辑"按钮（仅当 `currentUser.id === contract.initiator.id && contract.status === 'progress'` 时显示）。

点击后：
- 标题、描述变为可编辑（`<Input>` / `<Input.TextArea>`）
- 提供"保存"和"取消"按钮
- 顶部显示警告提示："修改后所有评审人需重新审批"
- "保存"调用 `PATCH /api/contracts/{id}`，仅传变更字段（用 `dirty` flag 控制）

附件上传：
- 现有"上传新版本"按钮继续可用，但仅 Initiator + progress 状态可见
- 上传成功后会自动触发后端重审，前端 `useReviews` query invalidate 即可

**新增 hook：** `frontend/src/hooks/useReviseContract.ts`

```typescript
export function useReviseContract(contractId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { name?: string; description?: string }) => {
      const response = await axios.patch(
        `${API_BASE_URL}/api/contracts/${contractId}`,
        data
      );
      if (!response.data.success) throw new Error(response.data.error);
      return response.data.data.contract;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.contracts.detail(contractId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.list(contractId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.contracts.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.pending.count() });
    },
  });
}
```

#### 2. MentionPicker 改造（需求2）

**`frontend/src/components/Timeline/MentionPicker.tsx` 改动：**

将原来的 `GET /api/users?search=` 替换为 `GET /api/contracts/{contractId}/mentionable-users?search=`。

```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['mentionable-users', contractId, debouncedQuery],
  queryFn: async () => {
    const response = await axios.get(
      `${API_BASE_URL}/api/contracts/${contractId}/mentionable-users`,
      {
        params: debouncedQuery ? { search: debouncedQuery } : {},
        timeout: 5000,
      }
    );
    return (response.data.data?.users ?? []) as UserCandidate[];
  },
  enabled: !!contractId,
  retry: false,  // 失败不重试，由组件提示
});
```

错误处理：
- `error` 存在时显示"加载候选人失败，请重试"
- 列表为空时显示"无匹配用户"
- 仅渲染最新查询结果（TanStack Query 默认行为）

#### 3. AI Advisor 引用解析与折叠（需求3）

**新增组件：** `frontend/src/components/AIAdvisor/MessageContent.tsx`

```typescript
import { useFocusedAnchorStore } from '../../stores/useFocusedAnchorStore';
import { useSelectedContractStore } from '../../stores/useSelectedContractStore';

interface MessageContentProps {
  text: string;
  contractId?: string;
  reviewMap?: Map<string, { authorName: string }>;
  commentMap?: Map<string, { authorName: string }>;
}

const REF_REGEX = /\[ref:(review|comment)-([a-f0-9-]+)\]/g;

export const MessageContent: React.FC<MessageContentProps> = ({
  text, contractId, reviewMap, commentMap,
}) => {
  const setAnchorId = useFocusedAnchorStore((s) => s.setAnchorId);
  const setSelectedContractId = useSelectedContractStore((s) => s.setSelectedContractId);

  // 解析文本，把 [ref:xxx-yyy] 替换为 React 节点
  const parts: Array<string | React.ReactNode> = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  REF_REGEX.lastIndex = 0;
  while ((match = REF_REGEX.exec(text)) !== null) {
    const [full, type, id] = match;
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const map = type === 'review' ? reviewMap : commentMap;
    const target = map?.get(id);
    if (!target) {
      parts.push(<span className="ai-ref-invalid" key={`${type}-${id}-${match.index}`}>引用不可用</span>);
    } else {
      const label = type === 'review' ? `@${target.authorName}的评审` : `@${target.authorName}的评论`;
      parts.push(
        <a
          key={`${type}-${id}-${match.index}`}
          className="ai-ref-link"
          onClick={(e) => {
            e.preventDefault();
            if (contractId) setSelectedContractId(contractId);
            setAnchorId(id);
            // 复用 NotificationItem 里的 findAnchorWithRetry 逻辑
            setTimeout(() => {
              const el = document.getElementById(`anchor-${id}`);
              if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                el.classList.add('highlight-flash');
                setTimeout(() => el.classList.remove('highlight-flash'), 3000);
              }
            }, 200);
          }}
        >
          {label}
        </a>
      );
    }
    lastIndex = match.index + full.length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));

  return <>{parts}</>;
};
```

**新增组件：** `frontend/src/components/AIAdvisor/CollapsibleMessage.tsx`

```typescript
const LINE_HEIGHT_PX = 22; // 与 .message-text 的 line-height 对齐
const MAX_LINES = 10;

export const CollapsibleMessage: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [needCollapse, setNeedCollapse] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useLayoutEffect(() => {
    if (!ref.current) return;
    // 临时移除 max-height 测量真实高度
    const el = ref.current;
    el.style.maxHeight = 'none';
    const fullHeight = el.scrollHeight;
    const threshold = LINE_HEIGHT_PX * MAX_LINES;
    setNeedCollapse(fullHeight > threshold);
    el.style.maxHeight = '';
  }, [/* 依赖 children 文本 */]);

  return (
    <div className={`collapsible-message ${needCollapse && !expanded ? 'collapsed' : ''}`}>
      <div ref={ref} className="collapsible-content">{children}</div>
      {needCollapse && (
        <>
          {!expanded && <div className="fade-mask" />}
          <button className="toggle-btn" onClick={() => setExpanded(!expanded)}>
            {expanded ? '收起' : '展开全部'}
          </button>
        </>
      )}
    </div>
  );
};
```

CSS：
```css
.collapsible-message { position: relative; }
.collapsible-message.collapsed .collapsible-content {
  max-height: 220px;  /* 22 * 10 */
  overflow: hidden;
}
.collapsible-message .fade-mask {
  position: absolute;
  bottom: 28px;  /* 给按钮留位置 */
  left: 0; right: 0;
  height: 40px;
  background: linear-gradient(to bottom, transparent, white);
  pointer-events: none;
}
.collapsible-message .toggle-btn {
  background: none;
  border: none;
  color: #1677ff;
  cursor: pointer;
  padding: 4px 0;
  font-size: 13px;
}

.ai-ref-link {
  color: #1677ff;
  cursor: pointer;
  text-decoration: underline dotted;
}
.ai-ref-invalid { color: #999; }
```

**改造 `frontend/src/components/AIAdvisor/Message.tsx`：**

```typescript
import { MessageContent } from './MessageContent';
import { CollapsibleMessage } from './CollapsibleMessage';

const Message = memo(({ message, currentUserName, reviewMap, commentMap, contractId }) => {
  const isUser = message.role === 'user';

  const body = (
    <div className="message-bubble">
      <p className="message-text">
        <MessageContent
          text={message.content}
          contractId={contractId}
          reviewMap={reviewMap}
          commentMap={commentMap}
        />
      </p>
    </div>
  );

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      {/* avatar 不变 */}
      <div className="message-content-wrapper">
        {isUser ? body : <CollapsibleMessage>{body}</CollapsibleMessage>}
        <div className="message-timestamp">{formatRelativeTime(message.timestamp)}</div>
      </div>
    </div>
  );
});
```

**`AIAdvisor.tsx` 改造：**

获取当前合同的 reviews + comments，构建 ID → 作者姓名映射，传给 `Message`：

```typescript
const { data: reviewsData } = useReviews(selectedContractId);

const { reviewMap, commentMap } = useMemo(() => {
  const reviewMap = new Map<string, { authorName: string }>();
  const commentMap = new Map<string, { authorName: string }>();
  
  for (const r of reviewsData?.reviews ?? []) {
    reviewMap.set(r.id, { authorName: r.reviewer?.name ?? '未知' });
    for (const c of r.replies ?? []) {
      commentMap.set(c.id, { authorName: c.author?.name ?? '未知' });
    }
  }
  for (const c of reviewsData?.topLevelComments ?? []) {
    commentMap.set(c.id, { authorName: c.author?.name ?? '未知' });
  }
  return { reviewMap, commentMap };
}, [reviewsData]);
```

#### 4. NotificationCenter 扩展（需求1）

**`frontend/src/components/NotificationCenter/NotificationItem.tsx` 改动：**

`TYPE_ICONS` 新增 `contract_revised`:
```typescript
const TYPE_ICONS: Record<NotificationType, string> = {
  review_approved: '✅',
  comment_added: '💬',
  comment_replied: '↩️',
  user_mentioned: '@',
  contract_revised: '📝',  // 新增
};
```

`NotificationType` 类型（`frontend/src/types/index.ts`）扩展：
```typescript
export type NotificationType =
  | 'review_approved' | 'comment_added' | 'comment_replied'
  | 'user_mentioned' | 'contract_revised';
```

通知点击：anchor_id 为 null 时仅切换合同，不滚动锚点。

#### 5. Socket.IO 监听 contract:revised（需求1）

**`frontend/src/config/socket.ts` 新增：**

```typescript
export const onContractRevised = (
  callback: SocketEventCallback<{ contractId: string; contractName: string; changedFields: string[] }>
): UnsubscribeFunction => {
  const socketInstance = getSocket();
  socketInstance.on('contract:revised', callback);
  return () => socketInstance.off('contract:revised', callback);
};
```

**`frontend/src/hooks/useSocket.ts` 中新增监听：**

```typescript
const unsubscribeContractRevised = onContractRevised((data) => {
  // 刷新合同详情、评审记录、待办数量
  queryClient.invalidateQueries({ queryKey: queryKeys.contracts.detail(data.contractId) });
  queryClient.invalidateQueries({ queryKey: queryKeys.reviews.list(data.contractId) });
  queryClient.invalidateQueries({ queryKey: queryKeys.contracts.lists() });
  queryClient.invalidateQueries({ queryKey: queryKeys.pending.count() });
  
  // 如果当前选中的就是这个合同，弹个 toast
  message.warning(`合同「${data.contractName}」已被发起人修改（${data.changedFields.join('、')}），请重新审批`);
});
```

---

## Data Models

### 数据库变更汇总

| 变更 | 详情 |
|------|------|
| 新建表 | `contract_revision_logs` |
| 新建索引 | `ix_revision_logs_contract_revised_at` |
| 枚举扩展 | `notification_type` 新增 `'contract_revised'` |

### 前端类型扩展

```typescript
// frontend/src/types/index.ts
export type NotificationType =
  | 'review_approved' | 'comment_added' | 'comment_replied'
  | 'user_mentioned' | 'contract_revised';

export interface ContractRevisionLog {
  id: string;
  contractId: string;
  revisedBy: string;
  changedFields: ('name' | 'description' | 'attachment')[];
  revisedAt: string;
}

export interface MentionableUser {
  id: string;
  name: string;
  avatar?: string;
  department?: string;
}
```

---

## API Interfaces

### 新增/修改端点

```
PATCH /api/contracts/{contract_id}
  Body: { name?: string, description?: string }
  Response: { success, data: { contract } }
  Error: 401/403/404/409/422

POST /api/contracts/{contract_id}/attachments  (现有，行为扩展)
  上传成功后自动触发重审（仅 Initiator + progress）
  Error: 401/403/404/409/413

GET /api/contracts/{contract_id}/mentionable-users?search=xxx
  Response: { success, data: { users: MentionableUser[] } }
  Error: 401/403/404
```

### Socket.IO 新增事件

```
contract:revised
  Payload: { contractId, contractName, changedFields }
  Room: user:{reviewer_id}
```

### 通知类型扩展

```
notification.type 新增 'contract_revised'
  preview: "{合同名} 已修改：{字段列表}，请重新审批"
  anchor_id: null（点击跳合同详情即可）
```

---

## Error Handling

### 需求1错误处理

| 场景 | HTTP | 处理 |
|------|------|------|
| 非发起人编辑 | 403 | 前端不显示编辑按钮 + 后端兜底 |
| 已完成合同编辑 | 409 | 前端检查 status 隐藏编辑按钮 + 后端兜底 |
| 输入超限 | 422 | 前端 Form 校验 + 后端兜底 |
| 合同不存在 | 404 | 前端跳合同列表 |

### 需求2错误处理

| 场景 | HTTP/UI | 处理 |
|------|---------|------|
| 非相关人员调用 | 403 | 前端理论上不会触发（只有相关人员能进合同详情）|
| 合同不存在 | 404 | 显示错误提示 |
| 网络/超时 | UI | "加载候选人失败，请重试"提示 |

### 需求3错误处理

| 场景 | 处理 |
|------|------|
| LLM 杜撰不存在的 ID | 前端渲染为"引用不可用"纯文本 |
| LLM 输出格式错误（标记残缺） | 正则匹配不到，原样保留为文本 |
| 流式输出中断 | 已接收内容仍可见，按完整文本重新判定折叠 |

---

## Testing Strategy

### 单元测试

**后端：**
- `contract_service.revise_contract()`：权限分支（403/409）、输入校验（422）、实际值变更检测、reviews 重置、审计日志写入、Socket.IO + 通知触发
- `mentionable_users` 端点：去重逻辑、search 过滤、权限检查
- `_ai_summary` 的 prompt 拼接：上下文中包含 `[review-{id}]`/`[comment-{id}]` 标记

**前端：**
- `MessageContent`：解析正确的 `[ref:...]` 标记，渲染可点击链接；ID 不存在时降级为"引用不可用"
- `CollapsibleMessage`：根据测量高度决定是否折叠；`maxLines=10` 边界
- `useReviseContract` hook：mutation 成功后 invalidate 相关 query

### 集成测试

- `PATCH /api/contracts/{id}` + `POST /attachments` → 验证 reviews 全部 status=pending、审计日志写入、`contract_revised` 通知生成
- `GET /api/contracts/{id}/mentionable-users` → 验证返回结果是 initiator + reviewer + cc 的去重并集
- AI 总结端到端：用户问"总结" → AI 返回带 `[ref:...]` 标记 → 前端正确渲染为可点击链接

### 部署前验证

1. `alembic upgrade head` 成功执行新迁移（`contract_revision_logs` 表 + `contract_revised` 枚举值）
2. 现有合同/评审/通知数据完整性不受影响
3. 现有 `/api/users?search=` 接口保留不删除（向后兼容）

---

## Correctness Properties

### Property 1: 重审原子性
WHEN Initiator 触发 Re_Review_Event，THE Revision_Service 必须在同一数据库事务中完成「Contract 字段更新 + Reviews 状态重置 + 审计日志写入」三项操作；任意一项失败，事务全部回滚。

**Validates: Requirements 1.5, 1.7, 1.8**

### Property 2: 实际值变更检测
仅当 `name` 或 `description` 提交值（去除首尾空白）与持久化值不同，或新增了 Attachment 记录时，才触发 Re_Review_Event。提交相同值不触发重审。

**Validates: Requirements 1.5**

### Property 3: 候选人完整性
`Mentionable_Users_API` 返回结果必须等于 `{Initiator} ∪ {所有 Reviewer} ∪ {所有 CC_User}`（按 ID 去重），不多不少。

**Validates: Requirements 2.2**

### Property 4: 引用 ID 真实性
AI 总结回复中所有 `[ref:review-{id}]` 与 `[ref:comment-{id}]` 标记的 ID，必须在当前合同的 reviews 表或 comments 表中真实存在；前端必须对不存在的 ID 降级为"引用不可用"，不报错、不静默丢弃。

**Validates: Requirements 3.2, 3.5**

### Property 5: 折叠测量幂等性
`AI_Message_Bubble` 的折叠判定（是否显示"展开全部"按钮）必须基于真实 DOM 渲染高度；同一文本在固定渲染宽度下的判定结果必须一致。

**Validates: Requirements 3.6, 3.7**

### Property 6: 流式输出折叠延迟
WHILE AI 流式输出未结束，AI_Message_Bubble 不应用任何折叠逻辑；WHEN 流式输出结束，必须重新执行测量与折叠判定。

**Validates: Requirements 3.11**
