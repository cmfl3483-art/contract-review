import { useState } from 'react';
import { Card, Space, Divider } from 'antd';
import CommentInput from './CommentInput';

/**
 * CommentInput 组件使用示例
 */
const CommentInputExample: React.FC = () => {
  const [lastComment, setLastComment] = useState<string>('');

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>CommentInput 组件示例</h1>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 示例 1: 基本使用 */}
        <Card title="示例 1: 基本使用 - 添加新评论">
          <p>在底部输入框添加新评论</p>
          <CommentInput
            contractId="contract-123"
            placeholder="输入评论内容..."
            onCommentAdded={() => {
              setLastComment('添加了新评论');
            }}
          />
          {lastComment && (
            <div style={{ marginTop: '12px', color: '#52c41a' }}>✓ {lastComment}</div>
          )}
        </Card>

        <Divider />

        {/* 示例 2: 回复评审意见 */}
        <Card title="示例 2: 回复评审意见">
          <div
            style={{
              padding: '12px',
              background: '#f5f5f5',
              borderRadius: '4px',
              marginBottom: '12px',
            }}
          >
            <strong>法务评审意见:</strong>
            <p>合同条款需要补充违约责任相关内容</p>
          </div>
          <CommentInput
            contractId="contract-123"
            reviewId="review-456"
            placeholder="回复评审意见..."
            onCommentAdded={() => {
              setLastComment('回复了评审意见');
            }}
          />
        </Card>

        <Divider />

        {/* 示例 3: 嵌套回复 */}
        <Card title="示例 3: 嵌套回复">
          <div
            style={{
              padding: '12px',
              background: '#f5f5f5',
              borderRadius: '4px',
              marginBottom: '12px',
            }}
          >
            <strong>张三的评论:</strong>
            <p>这个问题需要和客户确认一下</p>
          </div>
          <CommentInput
            contractId="contract-123"
            parentCommentId="comment-789"
            placeholder="回复评论..."
            onCommentAdded={() => {
              setLastComment('回复了评论');
            }}
          />
        </Card>

        <Divider />

        {/* 示例 4: 自定义占位符 */}
        <Card title="示例 4: 自定义占位符">
          <CommentInput
            contractId="contract-123"
            placeholder="请输入您的意见和建议..."
            onCommentAdded={() => {
              setLastComment('提交了意见和建议');
            }}
          />
        </Card>

        <Divider />

        {/* 示例 5: 带回调函数 */}
        <Card title="示例 5: 带回调函数">
          <p>评论发送成功后会触发回调函数</p>
          <CommentInput
            contractId="contract-123"
            onCommentAdded={() => {
              setLastComment('评论已添加,触发了回调函数');
              console.log('评论添加成功!');
            }}
          />
        </Card>
      </Space>

      <Divider />

      <Card title="使用说明">
        <Space direction="vertical">
          <div>
            <strong>发送方式:</strong>
            <ul>
              <li>点击"发送"按钮</li>
              <li>按 Enter 键</li>
            </ul>
          </div>
          <div>
            <strong>输入验证:</strong>
            <ul>
              <li>不允许发送空内容</li>
              <li>最多输入 2000 字符</li>
            </ul>
          </div>
          <div>
            <strong>状态反馈:</strong>
            <ul>
              <li>发送时显示加载状态</li>
              <li>成功后显示成功提示</li>
              <li>失败后显示错误提示</li>
            </ul>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default CommentInputExample;
