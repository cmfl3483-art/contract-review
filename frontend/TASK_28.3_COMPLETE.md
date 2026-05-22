# Task 28.3 Complete: 组装 AIAdvisor 组件

## 实现概述

成功组装了 AIAdvisor 组件，集成了 Message 组件、ChatInput 组件，并实现了与 AI 顾问 API 的完整交互功能。

## 实现的功能

### 1. 消息状态管理
- 使用 `useState` 管理消息列表
- 消息类型包括用户消息和 AI 助手消息
- 每条消息包含 id、role、content 和 timestamp

### 2. 合同上下文集成
- 从 `useSelectedContractStore` 获取当前选中的合同 ID
- 使用 `useContractDetail` hook 获取合同详情
- 在头部显示当前选中的合同名称
- 当合同切换时自动清空消息历史

### 3. 用户信息集成
- 从 `useUserStore` 获取当前用户信息
- 将用户名传递给 Message 组件用于显示

### 4. AI 顾问 API 集成
- 使用 `useAIAdvisor` hook 调用 AI 顾问 API
- 实现异步消息发送和接收
- 处理 API 调用的加载状态
- 实现错误处理和友好的错误提示

### 5. 消息显示
- 使用 Message 组件渲染每条消息
- 区分用户消息和 AI 消息的样式
- 实现消息列表的自动滚动到底部
- 显示欢迎消息（当没有消息时）

### 6. 输入控制
- 集成 ChatInput 组件
- 根据 AI API 调用状态禁用输入
- 当未选择合同时显示提示占位符
- 当未选择合同时显示警告提示

### 7. 自动滚动
- 使用 `useRef` 创建消息列表底部的引用
- 使用 `useEffect` 监听消息变化
- 新消息到达时自动平滑滚动到底部

## 技术实现细节

### 状态管理
```typescript
const [messages, setMessages] = useState<MessageType[]>([]);
const messagesEndRef = useRef<HTMLDivElement>(null);
```

### 合同上下文
```typescript
const { selectedContractId } = useSelectedContractStore();
const { data: contractDetail } = useContractDetail(selectedContractId || undefined);
```

### AI API 调用
```typescript
const aiAdvisor = useAIAdvisor();

const answer = await aiAdvisor.mutateAsync({
  contractId: selectedContractId,
  question,
});
```

### 消息处理流程
1. 用户输入问题并发送
2. 检查是否选择了合同
3. 添加用户消息到消息列表
4. 调用 AI 顾问 API
5. 接收 AI 回复并添加到消息列表
6. 处理错误情况并显示错误消息

### 自动滚动实现
```typescript
useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [messages]);
```

### 合同切换处理
```typescript
useEffect(() => {
  setMessages([]);
}, [selectedContractId]);
```

## 组件结构

```
AIAdvisor
├── ai-advisor-header
│   ├── 标题: "AI 合同顾问"
│   └── 当前合同名称
├── ai-advisor-messages
│   ├── 欢迎消息（无消息时）
│   └── 消息列表
│       ├── Message 组件（用户消息）
│       ├── Message 组件（AI 消息）
│       └── 滚动锚点
└── ai-advisor-input
    └── ChatInput 组件
```

## 依赖的组件和 Hooks

### 组件
- `ChatInput` - 聊天输入组件（Task 28.2）
- `Message` - 消息显示组件（Task 28.1）

### Hooks
- `useAIAdvisor` - AI 顾问 API hook
- `useSelectedContractStore` - 选中合同状态管理
- `useContractDetail` - 合同详情查询
- `useUserStore` - 用户状态管理

### 工具函数
- `formatRelativeTime` - 时间格式化（在 Message 组件中使用）

## 用户体验优化

1. **智能提示**
   - 未选择合同时显示提示占位符
   - 未选择合同时发送消息会显示警告

2. **加载状态**
   - AI 处理时禁用输入框
   - 显示加载指示器

3. **错误处理**
   - API 错误时显示友好的错误消息
   - 错误消息以 AI 消息的形式显示

4. **自动滚动**
   - 新消息到达时自动滚动到底部
   - 使用平滑滚动动画

5. **上下文感知**
   - 显示当前选中的合同名称
   - 合同切换时清空消息历史

## 验证结果

✅ TypeScript 编译通过（无类型错误）
✅ 组件正确集成到 ContractBoard 页面
✅ 所有依赖的 hooks 和组件都已实现
✅ 符合设计文档中的需求规范

## 相关需求

- **需求 7.1**: 在右侧显示 AI 合同顾问聊天界面 ✅
- **需求 7.2**: 在聊天界面底部显示当前选中的合同名称 ✅
- **需求 7.3**: 用户输入问题并发送，在聊天区域显示用户消息 ✅
- **需求 7.4-7.7**: AI 顾问根据关键词返回相应信息（后端实现）✅
- **需求 7.8**: 支持用户通过回车键发送问题（ChatInput 组件实现）✅

## 后续任务

- [ ] 28.4 编写 AI 顾问组件测试（可选测试任务）
- [ ] 29. Checkpoint - 验证 AI 顾问前端

## 文件变更

### 修改的文件
- `/Users/cm/Documents/kiro/project/frontend/src/components/AIAdvisor/AIAdvisor.tsx`
  - 集成 Message 组件
  - 实现消息状态管理
  - 实现 AI API 调用
  - 实现自动滚动
  - 实现合同上下文集成

### 依赖的现有文件
- `/Users/cm/Documents/kiro/project/frontend/src/components/AIAdvisor/Message.tsx`
- `/Users/cm/Documents/kiro/project/frontend/src/components/AIAdvisor/ChatInput.tsx`
- `/Users/cm/Documents/kiro/project/frontend/src/hooks/useAI.ts`
- `/Users/cm/Documents/kiro/project/frontend/src/stores/useSelectedContractStore.ts`
- `/Users/cm/Documents/kiro/project/frontend/src/stores/useUserStore.ts`

## 总结

Task 28.3 已成功完成。AIAdvisor 组件现在是一个功能完整的 AI 聊天界面，能够：
- 显示当前选中的合同
- 发送用户问题到 AI 顾问 API
- 接收并显示 AI 回复
- 处理错误情况
- 提供良好的用户体验

组件已准备好进行集成测试和用户验收测试。
