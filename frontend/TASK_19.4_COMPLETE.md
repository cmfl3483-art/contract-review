# Task 19.4 Complete: 配置 Socket.IO 客户端

## 实现概述

已成功配置 Socket.IO 客户端,实现了与后端的实时通信功能。客户端支持自动连接管理、房间管理、事件监听,并与 React Query 无缝集成。

## 实现的文件

### 1. `/frontend/src/config/socket.ts`
Socket.IO 客户端核心配置文件,提供以下功能:

#### 核心功能
- **连接管理**
  - `getSocket(token?)`: 获取或创建 Socket.IO 客户端实例
  - `connectSocket(token)`: 连接到服务器
  - `disconnectSocket()`: 断开连接
  - `isConnected()`: 检查连接状态

- **房间管理**
  - `joinContractRoom(contractId)`: 加入合同房间
  - `leaveContractRoom(contractId)`: 离开合同房间

- **事件监听**
  - `onContractUpdated(callback)`: 监听合同更新
  - `onReviewAdded(callback)`: 监听评审添加
  - `onCommentAdded(callback)`: 监听评论添加
  - `onReplyAdded(callback)`: 监听回复添加
  - `onLikeUpdated(callback)`: 监听点赞更新
  - `onPendingChanged(callback)`: 监听待办数量变化

#### 配置特性
- **自动重连**: 最多重连 5 次,延迟 1-5 秒
- **传输方式**: WebSocket 优先,降级到 polling
- **认证**: 使用 JWT token 进行身份验证
- **超时设置**: 连接超时 20 秒
- **日志记录**: 完整的连接状态日志

### 2. `/frontend/src/hooks/useSocket.ts`
React Hooks 封装,提供以下 Hooks:

#### `useSocket()`
管理 Socket.IO 连接的生命周期
- 用户登录时自动连接
- 用户登出时自动断开
- 返回连接状态

```typescript
const { isConnected } = useSocket();
```

#### `useContractRoom(contractId?)`
自动管理合同房间的加入和离开
- 当 contractId 变化时自动切换房间
- 组件卸载时自动离开房间

```typescript
useContractRoom(selectedContractId);
```

#### `useSocketEvents()`
监听所有 Socket.IO 事件并自动刷新 React Query 缓存
- 收到事件时自动失效相关查询缓存
- 触发 React Query 重新获取数据

```typescript
useSocketEvents();
```

#### `useSocketIntegration(contractId?)`
完整的 Socket.IO 集成 Hook (推荐使用)
- 结合连接管理、房间管理和事件监听
- 一行代码完成所有 Socket.IO 配置

```typescript
const { isConnected } = useSocketIntegration(selectedContractId);
```

### 3. `/frontend/src/hooks/index.ts`
更新了 hooks 导出,添加了 Socket.IO 相关 hooks

## 技术实现细节

### 连接认证
```typescript
// 使用 JWT token 进行认证
socket = io(API_BASE_URL, {
  auth: { token },
  // ...其他配置
});
```

### 自动重连策略
```typescript
reconnection: true,
reconnectionAttempts: 5,
reconnectionDelay: 1000,
reconnectionDelayMax: 5000,
```

### 事件处理流程
1. Socket.IO 收到服务器事件
2. 触发对应的事件监听器
3. 自动失效 React Query 缓存
4. React Query 重新获取数据
5. UI 自动更新

### 房间机制
- **用户房间**: `user:{user_id}` - 接收个人通知
- **合同房间**: `contract:{contract_id}` - 接收特定合同的更新

## 支持的事件

| 事件名称 | 触发时机 | 数据结构 | 缓存失效 |
|---------|---------|---------|---------|
| `contract:updated` | 合同信息更新 | `{ contract_id, ...data }` | 合同列表、合同详情 |
| `review:added` | 新增评审意见 | `{ contract_id, review_id, ...data }` | 评审列表、合同详情、合同列表 |
| `comment:added` | 新增评论 | `{ contract_id, comment_id, ...data }` | 评审列表 |
| `reply:added` | 新增回复 | `{ contract_id, reply_id, ...data }` | 评审列表 |
| `like:updated` | 点赞更新 | `{ contract_id, target_id, likes }` | 评审列表 |
| `pending:changed` | 待办数量变化 | `{ pending_count }` | 待办数量、合同列表 |

## 使用示例

### 基础使用 (在 App 组件中)
```typescript
import { useSocketIntegration } from './hooks';
import { useSelectedContractStore } from './stores';

function App() {
  const selectedContractId = useSelectedContractStore((state) => state.selectedContractId);
  const { isConnected } = useSocketIntegration(selectedContractId);

  return (
    <div>
      {isConnected && <span>🟢 实时连接已建立</span>}
      {/* 其他组件 */}
    </div>
  );
}
```

### 在特定组件中使用
```typescript
import { useContractRoom } from './hooks';

function ContractDetail({ contractId }: { contractId: string }) {
  // 自动加入和离开合同房间
  useContractRoom(contractId);

  return <div>{/* 合同详情 */}</div>;
}
```

### 手动监听事件
```typescript
import { useEffect } from 'react';
import { onCommentAdded } from './config/socket';

function Timeline({ contractId }: { contractId: string }) {
  useEffect(() => {
    const unsubscribe = onCommentAdded((data) => {
      console.log('新评论:', data);
      // 自定义处理逻辑
    });

    return unsubscribe;
  }, []);

  return <div>{/* 时间线 */}</div>;
}
```

## 错误处理

### 连接错误
```typescript
socket.on('connect_error', (error) => {
  console.error('[Socket.IO] 连接错误:', error.message);
  // 可以在这里显示用户友好的错误提示
});
```

### 认证失败
如果 token 无效,服务器会拒绝连接:
```typescript
// 服务器返回 false,触发 connect_error
socket.on('connect_error', (error) => {
  // 可能需要重新登录
});
```

### 重连失败
```typescript
socket.on('reconnect_failed', () => {
  console.error('[Socket.IO] 重连失败,已达到最大重连次数');
  // 可以提示用户刷新页面
});
```

## 性能优化

1. **懒加载**: Socket 实例只在需要时创建
2. **自动清理**: 使用 React useEffect 的清理函数自动取消监听
3. **缓存失效**: 只失效相关的查询缓存,避免不必要的重新获取
4. **房间管理**: 只加入当前查看的合同房间,减少不必要的事件

## 测试建议

### 手动测试步骤
1. **连接测试**
   - 登录后检查浏览器控制台是否显示 "连接成功"
   - 检查 Network 标签是否有 WebSocket 连接

2. **事件测试**
   - 在一个浏览器窗口添加评论
   - 在另一个窗口检查是否实时更新

3. **重连测试**
   - 停止后端服务器
   - 检查是否显示 "尝试重连"
   - 重启服务器,检查是否自动重连

4. **房间测试**
   - 切换不同的合同
   - 检查是否正确加入和离开房间

### 单元测试 (可选)
```typescript
// 测试 Socket.IO 连接
describe('Socket.IO Client', () => {
  it('should connect with valid token', () => {
    const token = 'valid-token';
    connectSocket(token);
    expect(isConnected()).toBe(true);
  });

  it('should disconnect on logout', () => {
    disconnectSocket();
    expect(isConnected()).toBe(false);
  });
});
```

## 与后端的集成

### 后端配置
- **路径**: `/socket.io`
- **认证**: JWT token 通过 `auth.token` 传递
- **CORS**: 使用与 FastAPI 相同的 CORS 配置

### 事件流程
```
客户端                    服务器
  |                        |
  |--- connect (token) --->|
  |<--- connected ---------|
  |                        |
  |--- join_contract ----->|
  |<--- joined_contract ---|
  |                        |
  |<--- contract:updated --|
  |<--- review:added ------|
  |<--- comment:added -----|
```

## 下一步

Socket.IO 客户端配置已完成,可以继续以下任务:

1. **Task 20.1**: 创建布局组件 (集成 Socket.IO 连接状态显示)
2. **Task 22.5**: 组装合同列表组件 (使用实时更新)
3. **Task 26.5**: 组装时间线组件 (使用实时评论更新)

## 相关文档

- [Socket.IO Client API](https://socket.io/docs/v4/client-api/)
- [React Query Integration](https://tanstack.com/query/latest/docs/react/overview)
- [Backend Socket.IO Server](/backend/app/core/socketio_server.py)

## 验收标准

✅ Socket.IO 客户端配置完成
✅ 支持自动连接和断开
✅ 支持自动重连 (最多 5 次)
✅ 支持房间管理 (加入/离开合同房间)
✅ 支持所有 6 种事件监听
✅ 与 React Query 集成 (自动刷新缓存)
✅ 提供 React Hooks 封装
✅ 完整的错误处理和日志记录
✅ 文档完整

## 注意事项

1. **Token 管理**: 确保在用户登录后调用 `connectSocket(token)`
2. **清理**: 组件卸载时会自动清理事件监听器
3. **性能**: 只在需要时加入合同房间,避免接收不必要的事件
4. **调试**: 开发环境下可以在控制台看到详细的 Socket.IO 日志
