# Timeline 组件

## 概述

Timeline 组件是合同预审看板系统的核心组件之一,用于展示合同的评审时间线。它集成了 AI 智能总结、评审意见、评论和回复等功能,为用户提供完整的合同审批进度视图。

## 功能特性

- ✅ 显示 AI 智能总结卡片(如果存在)
- ✅ 按时间倒序显示所有评审记录
- ✅ 自动过滤空评审记录(待评审等占位文本)
- ✅ 显示评审意见和回复列表
- ✅ 支持点赞评审和评论
- ✅ 支持添加新评论
- ✅ 显示加载状态、错误状态和空状态
- ✅ 响应式设计,适配不同屏幕尺寸

## Props

```typescript
interface TimelineProps {
  contractId: string; // 合同ID(必填)
}
```

## 使用示例

### 基础用法

```tsx
import { Timeline } from '@/components/Timeline';

function ContractDetailPage() {
  const contractId = 'contract-123';

  return (
    <div className="contract-detail">
      <Timeline contractId={contractId} />
    </div>
  );
}
```

### 在布局中使用

```tsx
import { Timeline } from '@/components/Timeline';

function MainLayout() {
  const [selectedContractId, setSelectedContractId] = useState<string>();

  return (
    <div className="layout">
      <div className="sidebar">
        <ContractList onSelect={setSelectedContractId} />
      </div>
      <div className="main">
        {selectedContractId && <Timeline contractId={selectedContractId} />}
      </div>
    </div>
  );
}
```

## 组件结构

Timeline 组件由以下子组件组成:

1. **AISummaryCard** - AI 智能总结卡片
   - 显示审批进度状态
   - 显示已完成人数/总人数
   - 显示关键问题列表

2. **CommentInput** - 评论输入框
   - 支持添加新评论
   - 支持回车键发送
   - 显示加载状态

3. **ReviewCard** - 评审意见卡片
   - 显示评审人信息
   - 显示评审意见内容
   - 支持点赞功能

4. **ReplyList** - 回复列表
   - 显示评论回复
   - 支持嵌套回复
   - 支持折叠/展开

## 数据流

```
Timeline
  ├─ useReviews(contractId)          // 获取评审数据
  │   └─ API: GET /api/contracts/:id/reviews
  │
  ├─ useLikeReview()                 // 点赞评审
  │   └─ API: POST /api/reviews/:id/like
  │
  └─ useLikeComment()                // 点赞评论
      └─ API: POST /api/comments/:id/like
```

## 状态管理

### 加载状态

```tsx
if (isLoading) {
  return <Spin size="large" tip="加载中..." />;
}
```

### 错误状态

```tsx
if (error) {
  return <Empty description="加载失败,请稍后重试" />;
}
```

### 空状态

```tsx
if (sortedReviews.length === 0) {
  return (
    <Empty description="暂无评审记录">
      <CommentInput placeholder="添加第一条评论..." />
    </Empty>
  );
}
```

## 数据过滤

Timeline 组件会自动过滤以下类型的空评审记录:

- 意见内容为"待评审"
- 意见内容为"待评审,请反馈"
- 意见内容为"待评审,请反馈"
- 没有意见内容且没有回复的记录

保留的记录:

- 有有效意见内容的记录
- 没有意见但有回复的记录(显示"参与了讨论")

## 排序规则

评审记录按创建时间倒序排列,最新的评审显示在最上方。

```typescript
const sortedReviews = useMemo(() => {
  return [...filteredReviews].sort((a, b) => {
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
  });
}, [filteredReviews]);
```

## 样式定制

### CSS 变量

Timeline 组件使用以下 CSS 类名,可以通过覆盖样式进行定制:

- `.timeline` - 主容器
- `.timeline-ai-summary` - AI 总结区域
- `.timeline-comment-input-wrapper` - 评论输入框容器
- `.timeline-reviews` - 评审列表
- `.timeline-review-item` - 单个评审项
- `.timeline-replies` - 回复区域

### 自定义样式示例

```css
/* 修改时间线背景色 */
.timeline {
  background-color: #ffffff;
}

/* 修改回复区域缩进 */
.timeline-replies {
  margin-left: 60px;
  padding-left: 20px;
}
```

## 性能优化

1. **useMemo 优化**
   - 使用 `useMemo` 缓存过滤和排序后的评审列表
   - 避免不必要的重新计算

2. **React Query 缓存**
   - 评审数据缓存 5 分钟
   - 自动处理数据刷新和失效

3. **虚拟滚动**
   - 对于大量评审记录,建议使用虚拟滚动优化性能
   - 可以集成 `react-window` 或 `react-virtualized`

## 实时更新

Timeline 组件通过 React Query 的缓存失效机制实现实时更新:

- 添加评论后自动刷新评审列表
- 点赞后自动更新点赞数
- WebSocket 推送时自动刷新数据

## 需求覆盖

该组件实现了以下需求:

- **需求 4.1-4.4**: 评审时间线展示
- **需求 5.1-5.9**: 评论和回复功能
- **需求 6.1-6.8**: AI 智能总结

## 测试

### 单元测试

```bash
npm run test Timeline.test.tsx
```

测试覆盖:

- ✅ 加载状态显示
- ✅ 错误状态显示
- ✅ 空状态显示
- ✅ AI 智能总结显示
- ✅ 评审记录按时间倒序排列
- ✅ 空评审记录过滤
- ✅ 评论输入框显示

### 集成测试

```bash
npm run test:e2e
```

## 常见问题

### Q: 为什么评审记录没有显示?

A: 检查以下几点:
1. 确认 `contractId` 是否正确
2. 检查 API 是否返回数据
3. 确认评审记录是否被过滤(空记录)

### Q: 如何自定义评论输入框的占位符?

A: 可以通过修改 `CommentInput` 组件的 `placeholder` prop:

```tsx
<CommentInput contractId={contractId} placeholder="自定义占位符..." />
```

### Q: 如何处理大量评审记录的性能问题?

A: 建议使用虚拟滚动:

```tsx
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={sortedReviews.length}
  itemSize={200}
>
  {({ index, style }) => (
    <div style={style}>
      <ReviewCard review={sortedReviews[index]} />
    </div>
  )}
</FixedSizeList>
```

## 相关组件

- [AISummaryCard](./AISummaryCard.md) - AI 智能总结卡片
- [ReviewCard](./ReviewCard.md) - 评审意见卡片
- [ReplyList](./ReplyList.md) - 回复列表
- [CommentInput](./CommentInput.md) - 评论输入框

## 更新日志

### v1.0.0 (2025-01-15)

- ✅ 初始版本发布
- ✅ 实现基础时间线功能
- ✅ 集成 AI 智能总结
- ✅ 支持评论和回复
- ✅ 支持点赞功能
