# Message Component

AI 合同顾问的消息组件，用于显示用户和 AI 助手之间的对话消息。

## 功能特性

- ✅ 显示用户消息气泡（蓝色背景，右对齐）
- ✅ 显示 AI 消息气泡（灰色背景，左对齐）
- ✅ 显示用户和 AI 的头像
- ✅ 显示相对时间戳
- ✅ 支持多行文本和长文本自动换行
- ✅ 响应式设计，适配移动端
- ✅ 平滑的进入动画效果

## Props

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| message | Message | 是 | - | 消息对象 |
| currentUserName | string | 否 | - | 当前用户名称，用于显示头像 |

### Message 类型

```typescript
interface Message {
  id: string;              // 消息唯一标识
  role: 'user' | 'assistant';  // 消息角色
  content: string;         // 消息内容
  timestamp: string;       // 消息时间戳（ISO 8601 格式）
}
```

## 使用示例

### 基础用法

```tsx
import Message from './Message';

const userMessage = {
  id: '1',
  role: 'user',
  content: '法务意见是什么？',
  timestamp: new Date().toISOString(),
};

const assistantMessage = {
  id: '2',
  role: 'assistant',
  content: '根据评审记录，法务部门提出了以下意见...',
  timestamp: new Date().toISOString(),
};

function ChatView() {
  return (
    <div>
      <Message message={userMessage} currentUserName="张三" />
      <Message message={assistantMessage} />
    </div>
  );
}
```

### 对话列表

```tsx
import Message from './Message';

function ConversationView({ messages, currentUserName }) {
  return (
    <div className="conversation">
      {messages.map((message) => (
        <Message
          key={message.id}
          message={message}
          currentUserName={currentUserName}
        />
      ))}
    </div>
  );
}
```

### 多行内容

```tsx
const multilineMessage = {
  id: '3',
  role: 'assistant',
  content: '当前合同存在以下风险项：\n\n1. 付款条件不明确\n2. 违约责任条款缺失\n3. 交付时间过于紧张',
  timestamp: new Date().toISOString(),
};

<Message message={multilineMessage} />
```

## 样式说明

### 用户消息样式
- 蓝色背景 (#1890ff)
- 白色文字
- 右对齐
- 右下角圆角较小（4px）

### AI 消息样式
- 灰色背景 (#f0f2f5)
- 深色文字 (#262626)
- 左对齐
- 左下角圆角较小（4px）

### 头像
- 用户头像：蓝色背景，显示用户名首字母
- AI 头像：绿色背景，显示机器人图标

### 时间戳
- 灰色文字 (#8c8c8c)
- 相对时间格式（如"5分钟前"、"刚刚"）
- 悬停时颜色加深

## 响应式设计

组件在移动端会自动调整：
- 消息气泡最大宽度从 70% 增加到 80%
- 字体大小略微减小
- 内边距适当缩小

## 动画效果

消息出现时有平滑的滑入动画：
- 从下方滑入（translateY）
- 淡入效果（opacity）
- 动画时长 0.3 秒

## 可访问性

- 使用语义化的 HTML 结构
- 头像使用 Ant Design 的 Avatar 组件，支持屏幕阅读器
- 文本内容支持自动换行，确保可读性
- 时间戳提供额外的上下文信息

## 注意事项

1. **时间戳格式**：timestamp 必须是有效的 ISO 8601 格式字符串
2. **长文本处理**：组件会自动换行，但建议在后端控制单条消息的长度
3. **性能优化**：在渲染大量消息时，建议使用虚拟滚动或分页加载
4. **头像显示**：如果不提供 currentUserName，用户头像会显示默认的 'U'

## 相关组件

- `AIAdvisor` - AI 合同顾问主组件
- `ChatInput` - 聊天输入框组件

## 需求覆盖

- ✅ 需求 7.1: 在右侧显示 AI 合同顾问聊天界面
- ✅ 需求 7.3: 在聊天区域显示用户消息
- ✅ 创建用户消息气泡
- ✅ 创建 AI 消息气泡
- ✅ 实现不同样式区分用户和 AI
- ✅ 显示时间戳
