# CommentInput 组件

## 概述

CommentInput 是一个用于添加评论的输入框组件,支持回复评审意见和嵌套回复功能。

## 功能特性

- ✅ 支持输入评论内容
- ✅ 支持回车键发送评论
- ✅ 支持点击发送按钮发送评论
- ✅ 支持回复评审意见 (提供 reviewId)
- ✅ 支持嵌套回复 (提供 parentCommentId)
- ✅ 发送成功后自动清空输入框
- ✅ 显示加载状态
- ✅ 输入验证 (不允许空内容)
- ✅ 字符长度限制 (最多 2000 字符)
- ✅ 输入焦点效果
- ✅ 禁用状态处理

## Props

| 属性名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| contractId | string | 是 | - | 合同ID |
| reviewId | string | 否 | undefined | 评审ID (回复评审意见时提供) |
| parentCommentId | string | 否 | undefined | 父评论ID (嵌套回复时提供) |
| placeholder | string | 否 | '输入评论内容...' | 输入框占位符文本 |
| onCommentAdded | () => void | 否 | undefined | 评论添加成功后的回调函数 |

## 使用示例

### 基本使用 - 添加新评论

```tsx
import { CommentInput } from '../../components/Timeline';

function Timeline() {
  return (
    <div className="timeline">
      <CommentInput 
        contractId="contract-123"
        placeholder="输入评论内容..."
      />
    </div>
  );
}
```

### 回复评审意见

```tsx
import { CommentInput } from '../../components/Timeline';

function ReviewCard({ review }) {
  return (
    <div className="review-card">
      <div className="review-content">{review.opinion}</div>
      <CommentInput 
        contractId={review.contractId}
        reviewId={review.id}
        placeholder="回复评审意见..."
      />
    </div>
  );
}
```

### 嵌套回复

```tsx
import { CommentInput } from '../../components/Timeline';

function CommentItem({ comment }) {
  const [showReply, setShowReply] = useState(false);

  return (
    <div className="comment-item">
      <div className="comment-content">{comment.content}</div>
      <button onClick={() => setShowReply(!showReply)}>回复</button>
      
      {showReply && (
        <CommentInput 
          contractId={comment.contractId}
          parentCommentId={comment.id}
          placeholder="回复评论..."
          onCommentAdded={() => setShowReply(false)}
        />
      )}
    </div>
  );
}
```

### 带回调函数

```tsx
import { CommentInput } from '../../components/Timeline';
import { message } from 'antd';

function Timeline() {
  const handleCommentAdded = () => {
    message.success('评论已添加');
    // 执行其他操作,如滚动到底部
    scrollToBottom();
  };

  return (
    <div className="timeline">
      <CommentInput 
        contractId="contract-123"
        onCommentAdded={handleCommentAdded}
      />
    </div>
  );
}
```

## 交互行为

### 发送评论

1. **点击发送按钮**: 点击"发送"按钮提交评论
2. **按回车键**: 在输入框中按 Enter 键提交评论
3. **Shift + Enter**: 不会触发发送 (预留用于多行输入)

### 输入验证

- 空内容或只包含空格的内容无法发送
- 尝试发送空内容时会显示警告提示: "评论内容不能为空"
- 输入长度限制为 2000 字符

### 加载状态

- 提交评论时,输入框和发送按钮会被禁用
- 发送按钮显示加载动画
- 加载完成后自动恢复可用状态

### 成功反馈

- 评论发送成功后显示成功提示: "评论发送成功"
- 输入框自动清空
- 调用 onCommentAdded 回调函数 (如果提供)

## 样式定制

组件使用独立的 CSS 文件 `CommentInput.css`,可以通过覆盖以下类名来定制样式:

```css
/* 容器 */
.comment-input {
  width: 100%;
  padding: 12px 0;
}

/* 输入框 */
.comment-input .ant-input {
  border-radius: 4px 0 0 4px;
}

/* 输入框焦点状态 */
.comment-input .ant-input:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

/* 发送按钮 */
.comment-input .ant-btn {
  border-radius: 0 4px 4px 0;
}

/* 发送按钮悬停状态 */
.comment-input .ant-btn:hover:not(:disabled) {
  background-color: #40a9ff;
}
```

## API 集成

组件使用 `useAddComment` hook 与后端 API 交互:

- **端点**: `POST /api/contracts/:contractId/comments`
- **请求体**:
  ```json
  {
    "content": "评论内容",
    "reviewId": "review-123",  // 可选
    "parentCommentId": "comment-456"  // 可选
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "data": {
      "comment": {
        "id": "comment-789",
        "content": "评论内容",
        "authorId": "user-123",
        "createdAt": "2025-03-01T12:00:00Z"
      }
    }
  }
  ```

## 错误处理

- 网络错误: 显示错误提示并保留输入内容
- 验证错误: 显示具体的验证错误信息
- 服务器错误: 显示通用错误提示

## 可访问性

- 输入框具有清晰的占位符文本
- 发送按钮具有图标和文本标签
- 加载状态通过 `aria-busy` 属性标识
- 禁用状态通过 `disabled` 属性标识

## 依赖项

- `react`: React 核心库
- `antd`: Ant Design 组件库 (Input, Button, Space, message)
- `@ant-design/icons`: Ant Design 图标库 (SendOutlined)
- `@tanstack/react-query`: 数据获取和缓存库
- `../../hooks/useReviews`: 评审相关的 React Query hooks

## 相关组件

- `ReviewCard`: 评审意见卡片组件
- `ReplyList`: 回复列表组件
- `Timeline`: 时间线组件

## 需求覆盖

该组件实现了以下需求:

- **需求 5.1**: 支持用户在底部输入框添加新评论
- **需求 5.2**: 按回车键或点击发送按钮提交评论
- **需求 5.3**: 支持用户回复任何评审意见
- **需求 5.4**: 支持用户回复其他用户的回复 (嵌套回复)
- **需求 10.5**: 为输入框提供占位符文本提示
- **需求 10.6**: 输入框获得焦点时改变边框颜色提供视觉反馈
- **需求 11.3**: 将回复数据添加到对应评审意见的回复列表中
- **需求 11.7**: 为每条新增的评论和回复自动生成时间戳
- **需求 11.8**: 为每条新增的评论和回复自动设置创建人为当前用户

## 测试

组件包含完整的单元测试,覆盖以下场景:

- ✅ 基本渲染
- ✅ 自定义占位符
- ✅ 输入验证
- ✅ 发送按钮状态
- ✅ 点击发送
- ✅ 回车键发送
- ✅ 成功后清空输入框
- ✅ 回调函数调用
- ✅ 回复评审意见
- ✅ 嵌套回复
- ✅ 空内容警告
- ✅ 加载状态
- ✅ 字符长度限制

运行测试:

```bash
npm test -- CommentInput.test.tsx
```

## 版本历史

- **v1.0.0** (2025-03-01): 初始版本
  - 基本评论输入功能
  - 回复评审意见
  - 嵌套回复
  - 输入验证
  - 加载状态
