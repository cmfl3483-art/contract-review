# Socket.IO 客户端配置

## 概述

Socket.IO 客户端提供实时通信功能,支持合同、评审、评论的实时更新。客户端与后端 Socket.IO 服务器无缝集成,并与 React Query 配合实现自动缓存刷新。

## 文件结构

```
src/
├── config/
│   ├── socket.ts           # Socket.IO 客户端核心配置
│   └── SOCKET_README.md    # 本文档
└── hooks/
    ├── useSocket.ts        # React Hooks 封装
    └── SOCKET_USAGE_EXAMPLE.tsx  # 使用示例
```

## 快速开始

### 1. 在 App 根组件中初始化

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

### 2. 在组件中使用房间

```typescript
import { useContractRoom } from './hooks';

function ContractDetail({ contractId }: { contractId: string }) {
  useContractRoom(contractId);
  return <div>{/* 合同详情 */}</div>;
}
```

### 3. 手动监听事件 (可选)

```typescript
import { useEffect } from 'react';
import { onCommentAdded } from './config/socket';

function Timeline() {
  useEffect(() => {
    const unsubscribe = onCommentAdded((data) => {
      console.log('新评论:', data);
    });
    return unsubscribe;
  }, []);

  return <div>{/* 时间线 */}</div>;
}
```

## API 文档

### 连接管理

#### `getSocket(token?: string): Socket`
获取或创建 Socket.IO 客户端实例。

**参数:**
- `token` (可选): JWT 认证 token

**返回:**
- Socket.IO 客户端实例

**示例:**
```typescript
import { getSocket } from './config/socket';

const socket = getSocket('your-jwt-token');
```

#### `connectSocket(token: string): void`
连接到 Socket.IO 服务器。

**参数:**
- `token`: JWT 认证 token

**示例:**
```typescript
import { connectSocket } from './config/socket';

connectSocket('your-jwt-token');
```

#### `disconnectSocket(): void`
断开 Socket.IO 连接。

**示例:**
```typescript
import { disconnectSocket } from './config/socket';

disconnectSocket();
```

#### `isConnected(): boolean`
检查当前连接状态。

**返回:**
- `true`: 已连接
- `false`: 未连接

**示例:**
```typescript
import { isConnected } from './config/socket';

if (isConnected()) {
  console.log('Socket.IO 已连接');
}
```

### 房间管理

#### `joinContractRoom(contractId: string): void`
加入合同房间,接收特定合同的实时更新。

**参数:**
- `contractId`: 合同 ID

**示例:**
```typescript
import { joinContractRoom } from './config/socket';

joinContractRoom('contract-123');
```

#### `leaveContractRoom(contractId: string): void`
离开合同房间。

**参数:**
- `contractId`: 合同 ID

**示例:**
```typescript
import { leaveContractRoom } from './config/socket';

leaveContractRoom('contract-123');
```

### 事件监听

所有事件监听函数都返回一个取消监听的函数。

#### `onContractUpdated(callback: (data: any) => void): () => void`
监听合同更新事件。

**参数:**
- `callback`: 回调函数,接收更新数据

**返回:**
- 取消监听的函数

**示例:**
```typescript
import { onContractUpdated } from './config/socket';

const unsubscribe = onContractUpdated((data) => {
  console.log('合同更新:', data);
});

// 取消监听
unsubscribe();
```

#### `onReviewAdded(callback: (data: any) => void): () => void`
监听评审添加事件。

#### `onCommentAdded(callback: (data: any) => void): () => void`
监听评论添加事件。

#### `onReplyAdded(callback: (data: any) => void): () => void`
监听回复添加事件。

#### `onLikeUpdated(callback: (data: any) => void): () => void`
监听点赞更新事件。

#### `onPendingChanged(callback: (data: any) => void): () => void`
监听待办数量变化事件。

#### `removeAllListeners(): void`
移除所有事件监听器。

## React Hooks

### `useSocket()`
管理 Socket.IO 连接的生命周期。

**返回:**
```typescript
{
  isConnected: boolean
}
```

**特性:**
- 用户登录时自动连接
- 用户登出时自动断开
- 组件卸载时自动清理

**示例:**
```typescript
import { useSocket } from './hooks';

function MyComponent() {
  const { isConnected } = useSocket();
  return <div>连接状态: {isConnected ? '已连接' : '未连接'}</div>;
}
```

### `useContractRoom(contractId?: string)`
自动管理合同房间的加入和离开。

**参数:**
- `contractId` (可选): 合同 ID

**特性:**
- contractId 变化时自动切换房间
- 组件卸载时自动离开房间

**示例:**
```typescript
import { useContractRoom } from './hooks';

function ContractDetail({ contractId }: { contractId: string }) {
  useContractRoom(contractId);
  return <div>{/* 合同详情 */}</div>;
}
```

### `useSocketEvents()`
监听所有 Socket.IO 事件并自动刷新 React Query 缓存。

**特性:**
- 自动失效相关查询缓存
- 触发 React Query 重新获取数据
- 组件卸载时自动取消监听

**示例:**
```typescript
import { useSocketEvents } from './hooks';

function App() {
  useSocketEvents();
  return <div>{/* 应用内容 */}</div>;
}
```

### `useSocketIntegration(contractId?: string)`
完整的 Socket.IO 集成 Hook (推荐使用)。

**参数:**
- `contractId` (可选): 当前选中的合同 ID

**返回:**
```typescript
{
  isConnected: boolean
}
```

**特性:**
- 结合连接管理、房间管理和事件监听
- 一行代码完成所有 Socket.IO 配置

**示例:**
```typescript
import { useSocketIntegration } from './hooks';

function App() {
  const { isConnected } = useSocketIntegration(selectedContractId);
  return <div>{/* 应用内容 */}</div>;
}
```

## 事件数据结构

### contract:updated
```typescript
{
  contract_id: string;
  // 其他合同数据
}
```

### review:added
```typescript
{
  contract_id: string;
  review_id: string;
  // 其他评审数据
}
```

### comment:added
```typescript
{
  contract_id: string;
  comment_id: string;
  // 其他评论数据
}
```

### reply:added
```typescript
{
  contract_id: string;
  reply_id: string;
  // 其他回复数据
}
```

### like:updated
```typescript
{
  contract_id: string;
  target_id: string;  // 评审或评论 ID
  likes: number;
}
```

### pending:changed
```typescript
{
  pending_count: number;
}
```

## 配置选项

Socket.IO 客户端配置 (在 `socket.ts` 中):

```typescript
{
  path: '/socket.io',              // Socket.IO 路径
  transports: ['websocket', 'polling'],  // 传输方式
  autoConnect: false,              // 手动控制连接
  reconnection: true,              // 启用自动重连
  reconnectionAttempts: 5,         // 最多重连5次
  reconnectionDelay: 1000,         // 重连延迟1秒
  reconnectionDelayMax: 5000,      // 最大重连延迟5秒
  timeout: 20000,                  // 连接超时20秒
  auth: { token }                  // JWT 认证
}
```

## 错误处理

### 连接错误
```typescript
socket.on('connect_error', (error) => {
  console.error('[Socket.IO] 连接错误:', error.message);
});
```

### 认证失败
```typescript
// 如果 token 无效,服务器会拒绝连接
// 触发 connect_error 事件
```

### 重连失败
```typescript
socket.on('reconnect_failed', () => {
  console.error('[Socket.IO] 重连失败');
  // 提示用户刷新页面
});
```

## 调试

### 启用详细日志
Socket.IO 客户端已配置详细日志,在浏览器控制台可以看到:

- `[Socket.IO] 连接成功`
- `[Socket.IO] 断开连接`
- `[Socket.IO] 尝试重连`
- `[Socket.IO Event] contract:updated`
- 等等

### 检查 WebSocket 连接
1. 打开浏览器开发者工具
2. 切换到 Network 标签
3. 筛选 WS (WebSocket)
4. 查看 Socket.IO 连接状态和消息

### 测试实时更新
1. 打开两个浏览器窗口
2. 在一个窗口添加评论
3. 在另一个窗口检查是否实时更新

## 性能优化

1. **懒加载**: Socket 实例只在需要时创建
2. **自动清理**: 使用 React useEffect 的清理函数
3. **缓存失效**: 只失效相关的查询缓存
4. **房间管理**: 只加入当前查看的合同房间

## 最佳实践

1. **在 App 根组件使用 useSocketIntegration**
   - 自动管理连接、房间和事件监听
   - 一行代码完成所有配置

2. **在需要实时更新的组件使用 useContractRoom**
   - 自动加入和离开合同房间
   - 组件卸载时自动清理

3. **使用 React Query 的自动刷新机制**
   - useSocketEvents 会自动失效相关缓存
   - 不需要手动更新状态

4. **只在需要自定义处理时手动监听事件**
   - 大多数情况下 useSocketEvents 已经足够
   - 手动监听适用于显示通知、播放声音等场景

5. **使用 isConnected() 检查连接状态**
   - 可以在 UI 中显示连接状态
   - 可以在连接断开时显示提示

## 故障排除

### 问题: 无法连接到 Socket.IO 服务器

**可能原因:**
1. 后端服务器未启动
2. Token 无效或过期
3. CORS 配置错误

**解决方案:**
1. 检查后端服务器是否运行
2. 检查 token 是否有效
3. 检查浏览器控制台的错误信息

### 问题: 收不到实时更新

**可能原因:**
1. 未加入合同房间
2. 事件监听器未正确设置
3. React Query 缓存未失效

**解决方案:**
1. 确保调用了 `useContractRoom(contractId)`
2. 确保调用了 `useSocketEvents()`
3. 检查浏览器控制台的事件日志

### 问题: 频繁断开重连

**可能原因:**
1. 网络不稳定
2. 服务器负载过高
3. Token 过期

**解决方案:**
1. 检查网络连接
2. 检查服务器状态
3. 刷新 token

## 相关资源

- [Socket.IO Client API](https://socket.io/docs/v4/client-api/)
- [React Query Documentation](https://tanstack.com/query/latest/docs/react/overview)
- [Backend Socket.IO Server](/backend/app/core/socketio_server.py)
- [Usage Examples](../hooks/SOCKET_USAGE_EXAMPLE.tsx)

## 更新日志

### v1.0.0 (2025-01-XX)
- ✅ 初始实现
- ✅ 支持所有 6 种事件
- ✅ 与 React Query 集成
- ✅ 自动重连机制
- ✅ 房间管理
- ✅ React Hooks 封装
