# Task 17.1 完成报告 - 配置 Socket.IO 服务器

## 任务概述

**任务ID**: 17.1  
**任务描述**: 配置 Socket.IO 服务器  
**需求**: 4.1-4.9, 5.1-5.9

## 实施内容

### 1. 创建 Socket.IO 服务器配置 (`app/core/socketio_server.py`)

#### 核心功能

1. **Socket.IO 服务器实例**
   - 使用 `socketio.AsyncServer` 创建异步服务器
   - 配置 `async_mode='asgi'` 用于与 FastAPI 集成
   - 配置 CORS,使用与 FastAPI 相同的 `CORS_ORIGINS` 设置

2. **认证中间件**
   - 实现 `verify_token()` 函数验证 JWT Token
   - 在 `connect` 事件中验证客户端认证信息
   - 拒绝未认证或 Token 无效的连接

3. **连接事件处理**
   - `connect`: 处理客户端连接,验证 Token,将用户加入个人房间
   - `disconnect`: 处理客户端断开连接,清理会话信息
   - `join_contract`: 允许用户加入特定合同的房间
   - `leave_contract`: 允许用户离开合同房间

4. **实时通知函数**
   - `emit_contract_updated()`: 发送合同更新通知
   - `emit_review_added()`: 发送评审添加通知
   - `emit_comment_added()`: 发送评论添加通知
   - `emit_reply_added()`: 发送回复添加通知
   - `emit_like_updated()`: 发送点赞更新通知
   - `emit_pending_changed()`: 发送待办数量变化通知
   - `emit_to_user()`: 发送通知给特定用户

#### 房间机制

- **个人房间**: `user:{user_id}` - 用于发送个人通知(如待办数量变化)
- **合同房间**: `contract:{contract_id}` - 用于发送合同相关的实时更新

### 2. 创建实时通知服务 (`app/services/notification_service.py`)

#### NotificationService 类

提供统一的接口用于发送 Socket.IO 实时通知:

- `notify_contract_updated()`: 通知合同更新
- `notify_review_added()`: 通知评审添加
- `notify_comment_added()`: 通知评论添加
- `notify_reply_added()`: 通知回复添加
- `notify_like_updated()`: 通知点赞更新
- `notify_pending_changed()`: 通知待办数量变化
- `notify_user()`: 发送通知给特定用户

#### 全局实例

创建 `notification_service` 全局实例,供其他服务调用。

### 3. 集成到 FastAPI 主应用 (`app/main.py`)

1. 导入 `socket_app` 从 `app.core.socketio_server`
2. 使用 `app.mount('/socket.io', socket_app)` 挂载 Socket.IO 应用

## 技术实现细节

### Socket.IO 配置

```python
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS,
    logger=True,
    engineio_logger=True,
)

socket_app = socketio.ASGIApp(
    sio,
    socketio_path='socket.io'
)
```

### 认证流程

1. 客户端连接时传递 `auth` 参数,包含 JWT Token
2. 服务器验证 Token 的有效性和过期时间
3. 验证成功后,将用户 ID 保存到会话字典
4. 将用户加入个人房间 `user:{user_id}`

### 事件类型

| 事件名称 | 描述 | 房间 |
|---------|------|------|
| `contract:updated` | 合同信息更新 | `contract:{contract_id}` |
| `review:added` | 新增评审意见 | `contract:{contract_id}` |
| `comment:added` | 新增评论 | `contract:{contract_id}` |
| `reply:added` | 新增回复 | `contract:{contract_id}` |
| `like:updated` | 点赞更新 | `contract:{contract_id}` |
| `pending:changed` | 待办数量变化 | `user:{user_id}` |

## 客户端使用示例

### 连接 Socket.IO 服务器

```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:8000', {
  path: '/socket.io',
  auth: {
    token: 'your-jwt-token'
  }
});

// 连接成功
socket.on('connected', (data) => {
  console.log('连接成功:', data);
});

// 连接错误
socket.on('connect_error', (error) => {
  console.error('连接失败:', error);
});
```

### 加入合同房间

```javascript
// 加入合同房间以接收该合同的实时更新
socket.emit('join_contract', { contract_id: 'contract-123' });

// 确认加入
socket.on('joined_contract', (data) => {
  console.log('已加入合同房间:', data.contract_id);
});
```

### 监听实时事件

```javascript
// 监听合同更新
socket.on('contract:updated', (data) => {
  console.log('合同更新:', data);
  // 更新 UI
});

// 监听评审添加
socket.on('review:added', (data) => {
  console.log('新增评审:', data);
  // 刷新评审列表
});

// 监听评论添加
socket.on('comment:added', (data) => {
  console.log('新增评论:', data);
  // 添加评论到时间线
});

// 监听点赞更新
socket.on('like:updated', (data) => {
  console.log('点赞更新:', data);
  // 更新点赞数
});

// 监听待办数量变化
socket.on('pending:changed', (data) => {
  console.log('待办数量变化:', data);
  // 更新待办徽章
});
```

### 离开合同房间

```javascript
// 离开合同房间
socket.emit('leave_contract', { contract_id: 'contract-123' });

// 确认离开
socket.on('left_contract', (data) => {
  console.log('已离开合同房间:', data.contract_id);
});
```

## 后端服务集成示例

### 在业务逻辑中发送实时通知

```python
from app.services.notification_service import notification_service

# 示例 1: 创建评论后发送通知
async def create_comment(contract_id: str, comment_data: dict):
    # 保存评论到数据库
    comment = await save_comment(comment_data)
    
    # 发送实时通知
    await notification_service.notify_comment_added(
        contract_id=contract_id,
        comment_data={
            'id': comment.id,
            'content': comment.content,
            'author': comment.author,
            'created_at': comment.created_at.isoformat()
        }
    )
    
    return comment

# 示例 2: 同意评审后发送通知
async def approve_review(contract_id: str, review_id: str, user_id: str):
    # 更新评审状态
    review = await update_review_status(review_id, 'approved')
    
    # 发送评审更新通知
    await notification_service.notify_review_added(
        contract_id=contract_id,
        review_data={
            'id': review.id,
            'status': review.status,
            'opinion': review.opinion,
            'updated_at': review.updated_at.isoformat()
        }
    )
    
    # 计算新的待办数量
    pending_count = await calculate_pending_count(user_id)
    
    # 发送待办数量变化通知
    await notification_service.notify_pending_changed(
        user_id=user_id,
        pending_count=pending_count
    )
    
    return review

# 示例 3: 点赞后发送通知
async def like_review(contract_id: str, review_id: str, user_id: str):
    # 更新点赞
    review = await toggle_like(review_id, user_id)
    
    # 发送点赞更新通知
    await notification_service.notify_like_updated(
        contract_id=contract_id,
        target_type='review',
        target_id=review_id,
        likes=review.likes,
        liked_by=review.liked_by
    )
    
    return review
```

## 验证结果

运行验证脚本 `verify_socketio_simple.py`:

```bash
python verify_socketio_simple.py
```

### 验证结果

✅ 所有文件已创建  
✅ Socket.IO 服务器配置完整  
✅ 实时通知服务完整  
✅ FastAPI 集成完成  
✅ Python 语法正确  

## 文件清单

1. **app/core/socketio_server.py** - Socket.IO 服务器配置
2. **app/services/notification_service.py** - 实时通知服务
3. **app/main.py** - FastAPI 主应用(已更新)

## 依赖项

- `python-socketio==5.11.0` - Socket.IO 服务器库
- `python-engineio>=4.8.0` - Engine.IO 引擎(自动安装)
- `bidict>=0.21.0` - 双向字典(自动安装)

## 下一步

1. **Task 17.2**: 实现实时通知服务的具体业务逻辑
2. **Task 17.3**: 集成 WebSocket 到业务逻辑(评论、评审、点赞等)
3. **前端集成**: 在前端实现 Socket.IO 客户端连接和事件监听

## 注意事项

1. **认证安全**: 
   - 客户端必须提供有效的 JWT Token 才能连接
   - Token 验证使用与 HTTP API 相同的密钥和算法

2. **房间管理**:
   - 用户自动加入个人房间 `user:{user_id}`
   - 需要手动加入/离开合同房间 `contract:{contract_id}`

3. **错误处理**:
   - 所有通知函数都包含 try-except 错误处理
   - 通知失败不会影响业务逻辑执行

4. **性能考虑**:
   - 使用房间机制避免广播给所有连接的客户端
   - 只向相关用户发送通知

5. **日志记录**:
   - 所有连接、断开、加入/离开房间事件都有日志记录
   - 通知发送成功/失败都有日志记录

## 测试建议

1. **单元测试**: 测试 `verify_token()` 函数
2. **集成测试**: 测试连接、断开、加入/离开房间事件
3. **端到端测试**: 使用 Socket.IO 客户端测试完整的通知流程

## 总结

Task 17.1 已成功完成,实现了:

✅ Socket.IO 服务器配置  
✅ CORS 配置  
✅ JWT 认证中间件  
✅ 连接和断开事件处理  
✅ 房间管理(个人房间和合同房间)  
✅ 实时通知函数(6 种事件类型)  
✅ 实时通知服务封装  
✅ FastAPI 集成  

系统现在具备了完整的实时通信能力,可以支持合同预审看板系统的实时更新需求。
