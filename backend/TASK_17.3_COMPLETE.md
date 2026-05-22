# Task 17.3 完成报告 - 集成 WebSocket 到业务逻辑

## 任务概述

**任务ID**: 17.3  
**任务描述**: 集成 WebSocket 到业务逻辑  
**需求**: 9.8, 9.9

## 实施内容

### 1. CommentService 集成

**文件**: `app/services/comment_service.py`

#### 1.1 添加评论时发送通知

在 `create_comment()` 方法中集成了 WebSocket 通知:

- **直接评论或回复评审**: 发送 `comment:added` 事件
- **嵌套回复**: 发送 `reply:added` 事件

```python
# 发送实时通知
if parent_comment_id:
    # 嵌套回复 - 发送 reply:added 事件
    await notification_service.notify_reply_added(
        contract_id=contract_id,
        reply_data={
            "id": str(comment.id),
            "contract_id": contract_id,
            "parent_comment_id": str(parent_comment_id),
            "author_id": str(comment.author_id),
            "author_name": comment.author.name,
            "content": comment.content,
            "created_at": comment.created_at.isoformat()
        }
    )
else:
    # 直接评论或回复评审 - 发送 comment:added 事件
    await notification_service.notify_comment_added(
        contract_id=contract_id,
        comment_data={
            "id": str(comment.id),
            "contract_id": contract_id,
            "review_id": str(review_id) if review_id else None,
            "author_id": str(comment.author_id),
            "author_name": comment.author.name,
            "content": comment.content,
            "created_at": comment.created_at.isoformat()
        }
    )
```

#### 1.2 点赞评论时发送通知

在 `like_comment()` 方法中集成了点赞更新通知:

```python
# 发送点赞更新通知
await notification_service.notify_like_updated(
    contract_id=str(comment.contract_id),
    like_data={
        "target_type": "comment",
        "target_id": str(comment_id),
        "likes": comment.likes,
        "user_id": user_id,
        "action": "unlike" if user_id not in liked_by else "like"
    }
)
```

### 2. ReviewService 集成

**文件**: `app/services/review_service.py`

#### 2.1 同意评审时发送通知

在 `approve_review()` 方法中集成了多个 WebSocket 通知:

**评审更新通知**:
```python
# 发送评审更新通知
await notification_service.notify_review_added(
    contract_id=str(review.contract_id),
    review_data={
        "id": str(review.id),
        "contract_id": str(review.contract_id),
        "reviewer_id": str(review.reviewer_id),
        "reviewer_name": review.reviewer.name,
        "role": review.role,
        "opinion": review.opinion,
        "status": review.status,
        "created_at": review.created_at.isoformat()
    }
)
```

**待办数量变化通知**:
```python
# 计算新的待办数量并发送通知
pending_count = await self._get_pending_count(reviewer_id, db)
await notification_service.notify_pending_changed(
    user_id=reviewer_id,
    pending_count=pending_count,
    contract_id=str(review.contract_id)
)
```

#### 2.2 点赞评审时发送通知

在 `like_review()` 方法中集成了点赞更新通知:

```python
# 发送点赞更新通知
await notification_service.notify_like_updated(
    contract_id=str(review.contract_id),
    like_data={
        "target_type": "review",
        "target_id": str(review_id),
        "likes": review.likes,
        "user_id": user_id,
        "action": "unlike" if user_id not in liked_by else "like"
    }
)
```

#### 2.3 合同状态变更时发送通知

在 `_check_and_update_contract_status()` 方法中,当所有评审通过时发送合同更新通知:

```python
if contract and contract.status != "completed":
    contract.status = "completed"
    await db.commit()
    
    # 发送合同更新通知
    await notification_service.notify_contract_updated(
        contract_id=str(contract_id),
        contract_data={
            "id": str(contract.id),
            "name": contract.name,
            "status": contract.status,
            "updated_at": contract.updated_at.isoformat()
        }
    )
```

#### 2.4 新增辅助方法

添加了 `_get_pending_count()` 方法用于计算用户待办数量:

```python
async def _get_pending_count(self, user_id: str, db: AsyncSession) -> int:
    """
    获取用户待办数量
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        待办数量
    """
    query = select(func.count()).select_from(Review).where(
        and_(
            Review.reviewer_id == user_id,
            Review.status == "pending"
        )
    )
    
    result = await db.execute(query)
    return result.scalar() or 0
```

### 3. ContractService 集成

**文件**: `app/services/contract_service.py`

#### 3.1 更新合同状态时发送通知

在 `update_contract_status()` 方法中集成了合同更新通知:

```python
contract.status = status
await db.commit()
await db.refresh(contract)

# 发送合同更新通知
await notification_service.notify_contract_updated(
    contract_id=contract_id,
    contract_data={
        "id": str(contract.id),
        "name": contract.name,
        "status": contract.status,
        "updated_at": contract.updated_at.isoformat()
    }
)
```

## 集成的事件类型

### 1. comment:added (评论添加)
- **触发场景**: 用户添加新评论或回复评审意见
- **发送位置**: `CommentService.create_comment()`
- **数据内容**: 评论ID、合同ID、评审ID(可选)、作者信息、内容、创建时间

### 2. reply:added (回复添加)
- **触发场景**: 用户回复其他评论(嵌套回复)
- **发送位置**: `CommentService.create_comment()`
- **数据内容**: 回复ID、合同ID、父评论ID、作者信息、内容、创建时间

### 3. review:added (评审添加)
- **触发场景**: 评审人同意评审项
- **发送位置**: `ReviewService.approve_review()`
- **数据内容**: 评审ID、合同ID、评审人信息、角色、意见、状态、创建时间

### 4. pending:changed (待办数量变化)
- **触发场景**: 用户同意评审后,待办数量发生变化
- **发送位置**: `ReviewService.approve_review()`
- **数据内容**: 用户ID、待办数量、合同ID

### 5. like:updated (点赞更新)
- **触发场景**: 用户点赞或取消点赞评审意见/评论
- **发送位置**: 
  - `ReviewService.like_review()` - 点赞评审
  - `CommentService.like_comment()` - 点赞评论
- **数据内容**: 目标类型(review/comment)、目标ID、点赞数、用户ID、操作类型(like/unlike)

### 6. contract:updated (合同更新)
- **触发场景**: 
  - 所有评审通过,合同状态变为已完成
  - 手动更新合同状态
- **发送位置**: 
  - `ReviewService._check_and_update_contract_status()` - 自动更新
  - `ContractService.update_contract_status()` - 手动更新
- **数据内容**: 合同ID、名称、状态、更新时间

## 实时通知流程

### 场景 1: 用户添加评论

```
用户提交评论
    ↓
CommentService.create_comment()
    ↓
保存评论到数据库
    ↓
判断是否为嵌套回复
    ↓
├─ 是 → 发送 reply:added 事件
└─ 否 → 发送 comment:added 事件
    ↓
WebSocket 推送到合同房间
    ↓
所有在该合同房间的客户端收到通知
    ↓
前端更新时间线显示
```

### 场景 2: 用户同意评审

```
用户点击同意按钮
    ↓
ReviewService.approve_review()
    ↓
更新评审状态为 approved
    ↓
发送 review:added 事件
    ↓
检查是否所有评审都已通过
    ↓
├─ 是 → 更新合同状态为 completed
│        ↓
│        发送 contract:updated 事件
└─ 否 → 继续
    ↓
计算新的待办数量
    ↓
发送 pending:changed 事件到用户个人房间
    ↓
WebSocket 推送通知
    ↓
前端更新评审状态、合同状态和待办徽章
```

### 场景 3: 用户点赞

```
用户点击点赞按钮
    ↓
ReviewService.like_review() 或 CommentService.like_comment()
    ↓
切换点赞状态(点赞/取消点赞)
    ↓
更新点赞数
    ↓
发送 like:updated 事件
    ↓
WebSocket 推送到合同房间
    ↓
所有在该合同房间的客户端收到通知
    ↓
前端更新点赞数显示
```

## 技术实现细节

### 1. 异步通知

所有通知发送都是异步的,不会阻塞主业务逻辑:

```python
await notification_service.notify_comment_added(...)
```

### 2. 错误处理

NotificationService 内部已实现错误处理,通知失败不会影响业务逻辑:

```python
try:
    await emit_comment_added(contract_id, data)
    logger.info(f"评论添加通知已发送: contract_id={contract_id}")
except Exception as e:
    logger.error(f"发送评论添加通知失败: contract_id={contract_id}, error={e}")
```

### 3. 数据格式化

所有通知数据都经过格式化,确保前端可以直接使用:

- UUID 转换为字符串
- 日期时间转换为 ISO 格式字符串
- 包含必要的关联数据(如作者姓名)

### 4. 房间机制

- **合同房间** (`contract:{contract_id}`): 用于发送合同相关的实时更新
- **个人房间** (`user:{user_id}`): 用于发送个人待办数量变化通知

## 验证结果

运行验证脚本 `verify_websocket_integration.py`:

```
============================================================
验证 WebSocket 集成到业务逻辑
============================================================

✅ 文件存在: app/services/comment_service.py
✅ 文件存在: app/services/review_service.py
✅ 文件存在: app/services/contract_service.py

------------------------------------------------------------
检查导入 notification_service
------------------------------------------------------------
✅ comment_service.py 已导入 notification_service
✅ review_service.py 已导入 notification_service
✅ contract_service.py 已导入 notification_service

------------------------------------------------------------
检查 WebSocket 通知调用
------------------------------------------------------------

CommentService:
  ✅ 添加评论时发送通知 (notify_comment_added) - 第 [95] 行
  ✅ 添加回复时发送通知 (notify_reply_added) - 第 [81] 行
  ✅ 点赞评论时发送通知 (notify_like_updated) - 第 [334] 行

ReviewService:
  ✅ 同意评审时发送通知 (notify_review_added) - 第 [147] 行
  ✅ 待办数量变化时发送通知 (notify_pending_changed) - 第 [170] 行
  ✅ 点赞评审时发送通知 (notify_like_updated) - 第 [219] 行
  ✅ 合同状态变更时发送通知 (notify_contract_updated) - 第 [318] 行

ContractService:
  ✅ 更新合同状态时发送通知 (notify_contract_updated) - 第 [227] 行

------------------------------------------------------------
集成检查总结
------------------------------------------------------------
✅ WebSocket 通知已成功集成到业务逻辑!

集成的功能:
  1. ✅ 创建评论时发送 comment:added 事件
  2. ✅ 创建回复时发送 reply:added 事件
  3. ✅ 同意评审时发送 review:added 事件
  4. ✅ 同意评审时发送 pending:changed 事件
  5. ✅ 点赞评审时发送 like:updated 事件
  6. ✅ 点赞评论时发送 like:updated 事件
  7. ✅ 合同状态变更时发送 contract:updated 事件

所有必需的 WebSocket 通知都已集成!
```

## 代码质量

### 1. 类型安全
- 所有通知数据都经过类型转换
- UUID 转换为字符串
- 日期时间转换为 ISO 格式

### 2. 数据完整性
- 在发送通知前刷新关联数据(如 author)
- 确保通知数据包含所有必要字段

### 3. 性能优化
- 异步通知不阻塞主业务逻辑
- 通知失败不影响业务操作
- 使用房间机制避免广播给所有客户端

### 4. 可维护性
- 统一使用 notification_service 发送通知
- 清晰的通知数据结构
- 详细的日志记录

## 前端集成指南

### 1. 监听评论添加事件

```javascript
socket.on('comment:added', (data) => {
  const { comment } = data;
  // 添加评论到时间线
  addCommentToTimeline(comment);
});
```

### 2. 监听回复添加事件

```javascript
socket.on('reply:added', (data) => {
  const { reply } = data;
  // 添加回复到对应的评论下
  addReplyToComment(reply.parent_comment_id, reply);
});
```

### 3. 监听评审更新事件

```javascript
socket.on('review:added', (data) => {
  const { review } = data;
  // 更新评审状态
  updateReviewStatus(review.id, review.status);
  // 刷新时间线
  refreshTimeline();
});
```

### 4. 监听待办数量变化事件

```javascript
socket.on('pending:changed', (data) => {
  const { pending_count } = data;
  // 更新待办徽章
  updatePendingBadge(pending_count);
});
```

### 5. 监听点赞更新事件

```javascript
socket.on('like:updated', (data) => {
  const { target_type, target_id, likes } = data;
  // 更新点赞数
  if (target_type === 'review') {
    updateReviewLikes(target_id, likes);
  } else if (target_type === 'comment') {
    updateCommentLikes(target_id, likes);
  }
});
```

### 6. 监听合同更新事件

```javascript
socket.on('contract:updated', (data) => {
  const { contract } = data;
  // 更新合同状态
  updateContractStatus(contract.id, contract.status);
  // 刷新合同列表
  refreshContractList();
});
```

## 测试建议

### 1. 单元测试
- Mock notification_service 测试业务逻辑
- 验证通知数据格式正确
- 验证通知在正确的时机被调用

### 2. 集成测试
- 测试完整的评论流程(创建评论 → 发送通知 → 前端接收)
- 测试完整的评审流程(同意评审 → 发送通知 → 更新待办)
- 测试点赞流程(点赞 → 发送通知 → 更新点赞数)

### 3. 端到端测试
- 使用真实的 Socket.IO 客户端连接
- 测试多客户端同步
- 测试断线重连

## 文件清单

### 修改的文件

1. **app/services/comment_service.py**
   - 添加 notification_service 导入
   - 在 create_comment() 中添加通知发送
   - 在 like_comment() 中添加通知发送

2. **app/services/review_service.py**
   - 添加 notification_service 导入
   - 在 approve_review() 中添加通知发送
   - 在 like_review() 中添加通知发送
   - 在 _check_and_update_contract_status() 中添加通知发送
   - 添加 _get_pending_count() 辅助方法

3. **app/services/contract_service.py**
   - 添加 notification_service 导入
   - 在 update_contract_status() 中添加通知发送

### 新增的文件

1. **verify_websocket_integration.py** - 验证脚本
2. **test_websocket_integration.py** - 测试脚本
3. **TASK_17.3_COMPLETE.md** - 本文档

## 依赖关系

### 依赖的模块
- `app.services.notification_service` - 实时通知服务
- `app.core.socketio_server` - Socket.IO 服务器(间接依赖)

### 被依赖的模块
- 前端 Socket.IO 客户端将监听这些事件

## 下一步

1. **前端集成** (Task 19.4): 在前端实现 Socket.IO 客户端连接和事件监听
2. **端到端测试**: 测试完整的实时通信流程
3. **性能优化**: 监控 WebSocket 连接数和消息吞吐量

## 注意事项

### 1. 数据刷新
在发送通知前,确保关联数据已加载:
```python
await db.refresh(comment, ["author"])
```

### 2. UUID 转换
所有 UUID 对象都需要转换为字符串:
```python
"id": str(comment.id)
```

### 3. 日期格式化
所有日期时间都需要转换为 ISO 格式:
```python
"created_at": comment.created_at.isoformat()
```

### 4. 错误处理
通知失败不应影响业务逻辑,NotificationService 已处理错误

### 5. 性能考虑
- 通知是异步的,不会阻塞主业务逻辑
- 使用房间机制避免不必要的广播
- 只向相关用户发送通知

## 总结

✅ Task 17.3 已完成!

成功集成了 WebSocket 通知到以下业务逻辑:

**CommentService**:
- ✅ 创建评论时发送 comment:added 事件
- ✅ 创建回复时发送 reply:added 事件
- ✅ 点赞评论时发送 like:updated 事件

**ReviewService**:
- ✅ 同意评审时发送 review:added 事件
- ✅ 同意评审时发送 pending:changed 事件
- ✅ 点赞评审时发送 like:updated 事件
- ✅ 合同状态变更时发送 contract:updated 事件

**ContractService**:
- ✅ 更新合同状态时发送 contract:updated 事件

**实现质量**:
- ✅ 异步通知不阻塞业务逻辑
- ✅ 完整的错误处理
- ✅ 数据格式化和类型转换
- ✅ 详细的日志记录
- ✅ 使用房间机制优化性能

系统现在具备了完整的实时通信能力,所有关键业务操作都会实时推送通知给相关用户,为前端提供了流畅的实时更新体验。

准备进入前端开发阶段,实现 Socket.IO 客户端连接和事件监听。
