# Task 19.3 完成报告: 配置 React Query

## 任务概述

配置 React Query 用于数据获取和缓存管理,实现前端的服务端状态管理。

## 实施内容

### 1. 核心配置文件

#### `src/config/queryClient.ts`
- 创建并配置 QueryClient 实例
- 设置全局缓存策略:
  - `staleTime`: 5分钟 (数据新鲜时间)
  - `gcTime`: 10分钟 (缓存保留时间)
  - `refetchOnWindowFocus`: true (窗口聚焦时重新获取)
  - `refetchOnReconnect`: true (重新连接时重新获取)
  - `retry`: 1 (失败重试1次)
- 定义统一的 Query Keys 常量,用于缓存管理

### 2. React Query Hooks

#### `src/hooks/useContracts.ts` - 合同相关
- `useContractList`: 获取合同列表,支持筛选和搜索
- `useContractDetail`: 获取合同详情
- `useCreateContract`: 创建新合同
- `usePendingCount`: 获取待办数量,每30秒自动刷新

#### `src/hooks/useReviews.ts` - 评审相关
- `useReviews`: 获取合同的评审记录和AI总结
- `useApproveReview`: 同意评审
- `useAddComment`: 添加评论或回复
- `useLikeReview`: 点赞评审
- `useLikeComment`: 点赞评论

#### `src/hooks/useAttachments.ts` - 附件相关
- `useUploadAttachment`: 上传附件
- `getAttachmentDownloadUrl`: 获取附件下载URL

#### `src/hooks/useAI.ts` - AI功能相关
- `useAISummary`: 获取AI智能总结
- `useAIAdvisor`: AI顾问问答

#### `src/hooks/useAuth.ts` - 用户认证相关
- `useCurrentUser`: 获取当前用户信息
- `getDingTalkLoginUrl`: 获取钉钉登录URL

### 3. 应用集成

#### `src/App.tsx`
- 使用 `QueryClientProvider` 包裹应用
- 集成 React Query Devtools (仅开发环境)

#### `src/hooks/index.ts`
- 统一导出所有 hooks,便于使用

### 4. 文档和示例

#### `src/hooks/README.md`
- 详细的使用文档
- 缓存策略说明
- WebSocket 集成指南
- 错误处理最佳实践

#### `src/hooks/USAGE_EXAMPLE.tsx`
- 12个实际使用示例
- 涵盖所有主要功能场景

## 缓存策略

不同类型的数据采用不同的缓存策略:

| 数据类型 | staleTime | 特殊配置 | 说明 |
|---------|-----------|---------|------|
| 合同列表 | 5分钟 | - | 频繁变化,需要较短的新鲜时间 |
| 合同详情 | 10分钟 | - | 相对稳定,可以缓存更久 |
| 评审记录 | 5分钟 | - | 频繁变化,需要较短的新鲜时间 |
| 待办数量 | 1分钟 | refetchInterval: 30秒 | 需要实时更新,自动刷新 |
| AI总结 | 30分钟 | retry: false | 生成成本高,可以缓存更久 |
| 用户信息 | Infinity | - | 会话期间不变 |

## 缓存失效机制

实现了智能的缓存失效策略:

1. **创建合同**: 使合同列表和待办数量缓存失效
2. **同意评审**: 使评审记录、合同详情、合同列表和待办数量缓存失效
3. **添加评论**: 使评审记录缓存失效
4. **点赞**: 使评审记录缓存失效
5. **上传附件**: 使合同详情缓存失效

## 技术特性

### 1. 类型安全
- 所有 hooks 都有完整的 TypeScript 类型定义
- 使用泛型确保 API 响应类型安全

### 2. 错误处理
- 统一的错误处理机制
- 友好的错误提示
- 支持自定义错误处理回调

### 3. 性能优化
- 智能缓存减少不必要的网络请求
- 后台自动更新保持数据新鲜
- 请求去重避免重复请求

### 4. 开发体验
- React Query Devtools 用于调试
- 详细的文档和示例
- 统一的 API 调用方式

## 依赖包

安装的新依赖:
```json
{
  "@tanstack/react-query": "^5.100.10",
  "@tanstack/react-query-devtools": "^5.100.10"
}
```

## 使用示例

### 基础查询
```typescript
import { useContractList } from '@/hooks';

function ContractList() {
  const { data, isLoading, error } = useContractList('进行中', '');
  
  if (isLoading) return <Spin />;
  if (error) return <div>错误: {error.message}</div>;
  
  return (
    <List
      dataSource={data?.contracts}
      renderItem={(contract) => (
        <List.Item>{contract.name}</List.Item>
      )}
    />
  );
}
```

### Mutation 操作
```typescript
import { useCreateContract } from '@/hooks';

function CreateButton() {
  const { mutate, isPending } = useCreateContract();
  
  const handleCreate = () => {
    mutate({
      name: '新合同',
      reviewers: ['user1'],
      ccUsers: [],
    }, {
      onSuccess: () => message.success('创建成功'),
      onError: (error) => message.error(error.message),
    });
  };
  
  return <Button onClick={handleCreate} loading={isPending}>创建</Button>;
}
```

## 与 WebSocket 集成

React Query 可以与 WebSocket 集成,实现实时数据更新:

```typescript
import { queryClient, queryKeys } from '@/config/queryClient';

// 监听 WebSocket 事件
socket.on('contract:updated', (data) => {
  queryClient.invalidateQueries({
    queryKey: queryKeys.contracts.detail(data.contractId),
  });
});

socket.on('review:added', (data) => {
  queryClient.invalidateQueries({
    queryKey: queryKeys.reviews.list(data.contractId),
  });
});
```

## 验证结果

✅ TypeScript 编译通过,无类型错误
✅ 构建成功,生成生产环境代码
✅ 所有 hooks 都有完整的类型定义
✅ 缓存策略配置合理
✅ 文档和示例完整

## 后续任务

下一步可以进行:
- Task 19.4: 配置 Socket.IO 客户端
- Task 20.1: 创建布局组件
- 在实际组件中使用这些 hooks

## 文件清单

创建的文件:
1. `src/config/queryClient.ts` - QueryClient 配置和 Query Keys
2. `src/hooks/useContracts.ts` - 合同相关 hooks
3. `src/hooks/useReviews.ts` - 评审相关 hooks
4. `src/hooks/useAttachments.ts` - 附件相关 hooks
5. `src/hooks/useAI.ts` - AI功能相关 hooks
6. `src/hooks/useAuth.ts` - 用户认证相关 hooks
7. `src/hooks/index.ts` - 统一导出
8. `src/hooks/README.md` - 使用文档
9. `src/hooks/USAGE_EXAMPLE.tsx` - 使用示例

修改的文件:
1. `src/App.tsx` - 添加 QueryClientProvider
2. `package.json` - 添加 react-query-devtools 依赖

## 总结

成功配置了 React Query,为前端应用提供了强大的数据获取和缓存管理能力。实现了:

1. ✅ 统一的数据获取接口
2. ✅ 智能的缓存策略
3. ✅ 自动的缓存失效机制
4. ✅ 完整的类型安全
5. ✅ 友好的错误处理
6. ✅ 详细的文档和示例

React Query 配置已完成,可以在后续的组件开发中使用这些 hooks 进行数据管理。
