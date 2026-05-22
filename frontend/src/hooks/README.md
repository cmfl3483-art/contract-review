# React Query Hooks

本目录包含所有使用 React Query 实现的数据获取和状态管理 hooks。

## 概述

React Query 是一个强大的数据同步库,用于管理服务端状态。它提供了以下功能:

- **自动缓存**: 减少不必要的网络请求
- **后台更新**: 自动在后台重新获取数据
- **乐观更新**: 提供更好的用户体验
- **请求去重**: 避免重复请求
- **错误处理**: 统一的错误处理机制

## 配置

### QueryClient 配置

在 `config/queryClient.ts` 中配置了全局的 React Query 设置:

```typescript
{
  staleTime: 5 * 60 * 1000,      // 数据新鲜时间: 5分钟
  gcTime: 10 * 60 * 1000,        // 缓存时间: 10分钟
  refetchOnWindowFocus: true,     // 窗口聚焦时重新获取
  refetchOnReconnect: true,       // 重新连接时重新获取
  retry: 1,                       // 失败重试次数: 1次
}
```

### Query Keys

使用统一的 Query Keys 管理缓存:

```typescript
queryKeys.contracts.list(filter, search); // 合同列表
queryKeys.contracts.detail(id); // 合同详情
queryKeys.reviews.list(contractId); // 评审记录
queryKeys.pending.count(); // 待办数量
queryKeys.user.current(); // 当前用户
queryKeys.ai.summary(contractId); // AI总结
```

## Hooks 使用指南

### 合同相关 (useContracts.ts)

#### useContractList

获取合同列表,支持筛选和搜索。

```typescript
const { data, isLoading, error } = useContractList(
  '进行中', // filter: 'all' | '进行中' | '已完成' | '待我处理' | '抄送我'
  '关键词', // search: 搜索关键词
  1, // page: 页码
  50 // limit: 每页数量
);

// data 结构:
// {
//   contracts: Contract[],
//   total: number,
//   pendingCount: number
// }
```

#### useContractDetail

获取合同详情。

```typescript
const { data, isLoading, error } = useContractDetail(contractId);

// data 结构:
// {
//   contract: Contract,
//   attachments: AttachmentGroup[],
//   reviewers: ReviewerStatus[]
// }
```

#### useCreateContract

创建新合同。

```typescript
const { mutate, isPending } = useCreateContract();

mutate(
  {
    name: '合同名称',
    description: '合同描述',
    reviewers: ['user1', 'user2'],
    ccUsers: ['user3'],
  },
  {
    onSuccess: (data) => {
      console.log('创建成功:', data.contractId);
    },
    onError: (error) => {
      console.error('创建失败:', error.message);
    },
  }
);
```

#### usePendingCount

获取待办数量,每30秒自动刷新。

```typescript
const { data: pendingCount } = usePendingCount();
```

### 评审相关 (useReviews.ts)

#### useReviews

获取合同的评审记录和AI总结。

```typescript
const { data, isLoading } = useReviews(contractId);

// data 结构:
// {
//   reviews: Review[],
//   aiSummary: AISummary | null
// }
```

#### useApproveReview

同意评审。

```typescript
const { mutate } = useApproveReview();

mutate({
  contractId: 'contract-id',
  reviewId: 'review-id',
  opinion: '同意并通过',
});
```

#### useAddComment

添加评论或回复。

```typescript
const { mutate } = useAddComment();

// 添加评论
mutate({
  contractId: 'contract-id',
  reviewId: 'review-id', // 可选,回复评审意见
  content: '评论内容',
});

// 嵌套回复
mutate({
  contractId: 'contract-id',
  parentCommentId: 'comment-id', // 可选,回复评论
  content: '回复内容',
});
```

#### useLikeReview / useLikeComment

点赞评审或评论。

```typescript
const { mutate: likeReview } = useLikeReview();
const { mutate: likeComment } = useLikeComment();

likeReview({ reviewId: 'review-id', contractId: 'contract-id' });
likeComment({ commentId: 'comment-id', contractId: 'contract-id' });
```

### 附件相关 (useAttachments.ts)

#### useUploadAttachment

上传附件。

```typescript
const { mutate, isPending } = useUploadAttachment();

mutate({
  contractId: 'contract-id',
  file: fileObject,
  version: 'v1.0', // 可选
});
```

#### getAttachmentDownloadUrl

获取附件下载URL。

```typescript
const downloadUrl = getAttachmentDownloadUrl(attachmentId);
```

### AI相关 (useAI.ts)

#### useAISummary

获取AI智能总结。

```typescript
const { data: summary, isLoading } = useAISummary(contractId);

// summary 结构:
// {
//   approvalStatus: 'completed' | 'in_progress',
//   completedCount: number,
//   totalCount: number,
//   reviewCount: number,
//   keyIssues: KeyIssue[]
// }
```

#### useAIAdvisor

AI顾问问答。

```typescript
const { mutate, isPending } = useAIAdvisor();

mutate(
  {
    contractId: 'contract-id',
    question: '有哪些法务意见?',
  },
  {
    onSuccess: (answer) => {
      console.log('AI回答:', answer);
    },
  }
);
```

### 用户认证相关 (useAuth.ts)

#### useCurrentUser

获取当前用户信息。

```typescript
const { data: user, isLoading } = useCurrentUser();
```

#### getDingTalkLoginUrl

获取钉钉登录URL。

```typescript
const loginUrl = await getDingTalkLoginUrl();
window.location.href = loginUrl;
```

## 缓存策略

不同类型的数据有不同的缓存策略:

| 数据类型 | staleTime | 说明                        |
| -------- | --------- | --------------------------- |
| 合同列表 | 5分钟     | 频繁变化,需要较短的新鲜时间 |
| 合同详情 | 10分钟    | 相对稳定,可以缓存更久       |
| 评审记录 | 5分钟     | 频繁变化,需要较短的新鲜时间 |
| 待办数量 | 1分钟     | 需要实时更新,每30秒自动刷新 |
| AI总结   | 30分钟    | 生成成本高,可以缓存更久     |
| 用户信息 | Infinity  | 会话期间不变                |

## 缓存失效

当数据发生变化时,相关的缓存会自动失效:

- **创建合同**: 使合同列表和待办数量缓存失效
- **同意评审**: 使评审记录、合同详情、合同列表和待办数量缓存失效
- **添加评论**: 使评审记录缓存失效
- **点赞**: 使评审记录缓存失效
- **上传附件**: 使合同详情缓存失效

## WebSocket 集成

当收到 WebSocket 事件时,应该手动使相关缓存失效:

```typescript
import { queryClient } from '../config/queryClient';
import { queryKeys } from '../config/queryClient';

// 监听合同更新事件
socket.on('contract:updated', (data) => {
  queryClient.invalidateQueries({
    queryKey: queryKeys.contracts.detail(data.contractId),
  });
});

// 监听评审添加事件
socket.on('review:added', (data) => {
  queryClient.invalidateQueries({
    queryKey: queryKeys.reviews.list(data.contractId),
  });
});

// 监听待办变化事件
socket.on('pending:changed', () => {
  queryClient.invalidateQueries({
    queryKey: queryKeys.pending.count(),
  });
});
```

## 错误处理

所有 hooks 都会抛出错误,可以在组件中统一处理:

```typescript
const { data, error, isLoading } = useContractList();

if (error) {
  return <div>错误: {error.message}</div>;
}

if (isLoading) {
  return <div>加载中...</div>;
}

return <div>{/* 渲染数据 */}</div>;
```

## 最佳实践

1. **使用 enabled 选项**: 当依赖数据不存在时,禁用查询

   ```typescript
   useContractDetail(contractId, { enabled: !!contractId });
   ```

2. **使用 onSuccess/onError 回调**: 处理 mutation 的成功和失败

   ```typescript
   mutate(data, {
     onSuccess: () => message.success('操作成功'),
     onError: (error) => message.error(error.message),
   });
   ```

3. **避免过度获取**: 使用 staleTime 控制数据新鲜度,避免不必要的请求

4. **合理使用缓存失效**: 只使相关的缓存失效,避免过度失效

5. **使用 React Query Devtools**: 在开发环境中使用 Devtools 调试缓存状态

## 参考资料

- [React Query 官方文档](https://tanstack.com/query/latest)
- [React Query 最佳实践](https://tkdodo.eu/blog/practical-react-query)
