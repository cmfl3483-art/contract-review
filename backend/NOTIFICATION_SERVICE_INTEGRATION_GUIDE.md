# NotificationService 集成指南

## 概述

本指南说明如何在业务逻辑中集成 NotificationService,实现实时通知推送功能。

## 集成位置

NotificationService 应该在以下场景中调用:

### 1. 评论相关操作 (app/routes/reviews.py)

#### 1.1 添加评论时

```python
from app.services.notification_service import notification_service

@router.post("/contracts/{contract_id}/comments")
async def create_comment(
    contract_id: str,
    comment_data: CommentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # 获取当前用户
    current_user = get_current_user(request)
    
    # 创建评论
    comment = await comment_service.create_comment(
        contract_id=contract_id,
        content=comment_data.content,
        author_id=current_user.id,
        review_id=comment_data.review_id,
        parent_comment_id=comment_data.parent_comment_id,
        db=db
    )
    
    # 🔔 发送实时通知
    if comment_data.parent_comment_id:
        # 这是一个回复
        await notification_service.notify_reply_added(
            contract_id=contract_id,
            reply_data={
                "id": comment.id,
                "contract_id": contract_id,
                "parent_comment_id": comment.parent_comment_id,
                "author_id": current_user.id,
                "author_name": current_user.name,
                "content": comment.content,
                "created_at": comment.created_at.isoformat()
            }
        )
    else:
        # 这是一个评论
        await notification_service.notify_comment_added(
            contract_id=contract_id,
            comment_data={
                "id": comment.id,
                "contract_id": contract_id,
                "review_id": comment.review_id,
                "author_id": current_user.id,
                "author_name": current_user.name,
                "content": comment.content,
                "created_at": comment.created_at.isoformat()
            }
        )
    
    return {"success": True, "data": comment}
```

#### 1.2 点赞评审意见时

```python
@router.post("/reviews/{review_id}/like")
async def like_review(
    review_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    current_user = get_current_user(request)
    
    # 切换点赞状态
    review = await review_service.toggle_like(
        review_id=review_id,
        user_id=current_user.id,
        db=db
    )
    
    # 🔔 发送实时通知
    await notification_service.notify_like_updated(
        contract_id=review.contract_id,
        like_data={
            "target_type": "review",
            "target_id": review_id,
            "likes": review.likes,
            "user_id": current_user.id,
            "action": "like" if current_user.id in review.liked_by else "unlike"
        }
    )
    
    return {"success": True, "data": {"likes": review.likes}}
```

#### 1.3 点赞评论时

```python
@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    current_user = get_current_user(request)
    
    # 切换点赞状态
    comment = await comment_service.toggle_like(
        comment_id=comment_id,
        user_id=current_user.id,
        db=db
    )
    
    # 🔔 发送实时通知
    await notification_service.notify_like_updated(
        contract_id=comment.contract_id,
        like_data={
            "target_type": "comment",
            "target_id": comment_id,
            "likes": comment.likes,
            "user_id": current_user.id,
            "action": "like" if current_user.id in comment.liked_by else "unlike"
        }
    )
    
    return {"success": True, "data": {"likes": comment.likes}}
```

### 2. 评审相关操作 (app/routes/reviews.py)

#### 2.1 同意评审时

```python
@router.post("/contracts/{contract_id}/reviews/{review_id}/approve")
async def approve_review(
    contract_id: str,
    review_id: str,
    approval_data: ApprovalData,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    current_user = get_current_user(request)
    
    # 更新评审状态
    review = await review_service.approve_review(
        review_id=review_id,
        opinion=approval_data.opinion,
        db=db
    )
    
    # 🔔 发送评审更新通知
    await notification_service.notify_review_added(
        contract_id=contract_id,
        review_data={
            "id": review.id,
            "contract_id": contract_id,
            "reviewer_id": review.reviewer_id,
            "reviewer_name": review.reviewer.name,
            "role": review.role,
            "opinion": review.opinion,
            "status": review.status,
            "created_at": review.created_at.isoformat()
        }
    )
    
    # 计算新的待办数量
    pending_count = await contract_service.get_pending_count(
        user_id=current_user.id,
        db=db
    )
    
    # 🔔 发送待办变化通知
    await notification_service.notify_pending_changed(
        user_id=current_user.id,
        pending_count=pending_count,
        contract_id=contract_id
    )
    
    # 检查是否所有评审都已完成
    contract = await contract_service.update_contract_status_if_all_approved(
        contract_id=contract_id,
        db=db
    )
    
    if contract and contract.status == "completed":
        # 🔔 发送合同状态更新通知
        await notification_service.notify_contract_updated(
            contract_id=contract_id,
            contract_data={
                "id": contract.id,
                "name": contract.name,
                "status": contract.status,
                "updated_at": contract.updated_at.isoformat()
            }
        )
    
    return {"success": True, "data": review}
```

### 3. 合同相关操作 (app/routes/contracts.py)

#### 3.1 创建合同时

```python
@router.post("/contracts")
async def create_contract(
    contract_data: ContractCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    current_user = get_current_user(request)
    
    # 创建合同
    contract = await contract_service.create_contract(
        name=contract_data.name,
        description=contract_data.description,
        initiator_id=current_user.id,
        reviewers=contract_data.reviewers,
        cc_users=contract_data.cc_users,
        db=db
    )
    
    # 🔔 通知所有评审人待办数量变化
    reviewer_ids = [r["user_id"] for r in contract_data.reviewers]
    pending_counts = {}
    
    for reviewer_id in reviewer_ids:
        count = await contract_service.get_pending_count(
            user_id=reviewer_id,
            db=db
        )
        pending_counts[reviewer_id] = count
    
    await notification_service.notify_multiple_users_pending_changed(
        user_ids=reviewer_ids,
        pending_counts=pending_counts,
        contract_id=contract.id
    )
    
    return {"success": True, "data": {"contract_id": contract.id}}
```

#### 3.2 更新合同状态时

```python
@router.patch("/contracts/{contract_id}/status")
async def update_contract_status(
    contract_id: str,
    status_data: StatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    # 更新状态
    contract = await contract_service.update_contract_status(
        contract_id=contract_id,
        status=status_data.status,
        db=db
    )
    
    # 🔔 发送合同更新通知
    await notification_service.notify_contract_updated(
        contract_id=contract_id,
        contract_data={
            "id": contract.id,
            "name": contract.name,
            "status": contract.status,
            "updated_at": contract.updated_at.isoformat()
        }
    )
    
    return {"success": True, "data": contract}
```

## 最佳实践

### 1. 错误处理

通知发送失败不应该影响主业务逻辑:

```python
try:
    # 主业务逻辑
    comment = await comment_service.create_comment(...)
    
    # 发送通知 (即使失败也不影响业务)
    try:
        await notification_service.notify_comment_added(...)
    except Exception as e:
        logger.error(f"发送通知失败: {e}")
        # 不抛出异常,继续执行
    
    return {"success": True, "data": comment}
except Exception as e:
    # 业务逻辑错误才返回失败
    return {"success": False, "error": str(e)}
```

### 2. 数据格式

确保发送的数据包含前端需要的所有字段:

```python
# ✅ 好的做法 - 包含完整信息
await notification_service.notify_comment_added(
    contract_id=contract_id,
    comment_data={
        "id": comment.id,
        "contract_id": contract_id,
        "author_id": current_user.id,
        "author_name": current_user.name,  # 前端需要显示
        "author_avatar": current_user.avatar,  # 前端需要显示
        "content": comment.content,
        "created_at": comment.created_at.isoformat()
    }
)

# ❌ 不好的做法 - 缺少信息
await notification_service.notify_comment_added(
    contract_id=contract_id,
    comment_data={
        "id": comment.id,
        "content": comment.content
    }
)
```

### 3. 时间格式

使用 ISO 8601 格式的时间字符串:

```python
# ✅ 好的做法
"created_at": comment.created_at.isoformat()  # "2025-03-15T10:30:00"

# ❌ 不好的做法
"created_at": str(comment.created_at)  # 格式不统一
```

### 4. 批量通知

当一个操作影响多个用户时,使用批量通知:

```python
# ✅ 好的做法 - 批量通知
await notification_service.notify_multiple_users_pending_changed(
    user_ids=["user1", "user2", "user3"],
    pending_counts={"user1": 2, "user2": 3, "user3": 1},
    contract_id=contract_id
)

# ❌ 不好的做法 - 循环单个通知
for user_id in user_ids:
    await notification_service.notify_pending_changed(
        user_id=user_id,
        pending_count=pending_counts[user_id],
        contract_id=contract_id
    )
```

## 测试建议

### 1. 单元测试

测试通知服务的方法调用:

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_notify_comment_added():
    with patch('app.core.socketio_server.emit_comment_added') as mock_emit:
        mock_emit.return_value = None
        
        await notification_service.notify_comment_added(
            contract_id="test-123",
            comment_data={"id": "comment-123", "content": "测试"}
        )
        
        mock_emit.assert_called_once()
```

### 2. 集成测试

测试完整的业务流程:

```python
@pytest.mark.asyncio
async def test_create_comment_with_notification(client, db):
    # 创建评论
    response = await client.post(
        "/api/contracts/test-123/comments",
        json={"content": "测试评论"}
    )
    
    assert response.status_code == 200
    
    # 验证通知已发送 (需要 mock Socket.IO)
    # ...
```

## 前端集成

前端需要监听这些事件:

```typescript
// Socket.IO 客户端
import io from 'socket.io-client';

const socket = io('http://localhost:8000', {
  path: '/socket.io',
  auth: {
    token: localStorage.getItem('token')
  }
});

// 监听合同更新
socket.on('contract:updated', (data) => {
  console.log('合同更新:', data);
  // 更新 UI
});

// 监听评审添加
socket.on('review:added', (data) => {
  console.log('评审添加:', data);
  // 更新时间线
});

// 监听评论添加
socket.on('comment:added', (data) => {
  console.log('评论添加:', data);
  // 更新时间线
});

// 监听回复添加
socket.on('reply:added', (data) => {
  console.log('回复添加:', data);
  // 更新时间线
});

// 监听点赞更新
socket.on('like:updated', (data) => {
  console.log('点赞更新:', data);
  // 更新点赞数
});

// 监听待办变化
socket.on('pending:changed', (data) => {
  console.log('待办变化:', data);
  // 更新待办徽章
});
```

## 总结

NotificationService 提供了统一的实时通知接口,使用时需要:

1. ✅ 在业务逻辑完成后调用通知方法
2. ✅ 提供完整的数据给前端
3. ✅ 处理通知发送失败的情况
4. ✅ 使用批量通知优化性能
5. ✅ 编写测试验证功能

下一步 (Task 17.3) 将在实际的路由中集成这些通知调用。
