import React, { memo } from 'react';
import { Avatar } from 'antd';
import { UserOutlined, RobotOutlined, LoadingOutlined } from '@ant-design/icons';
import type { Message as MessageType } from '../../types';
import { formatRelativeTime } from '../../utils/time';
import MessageContent from './MessageContent';
import CollapsibleMessage from './CollapsibleMessage';
import './Message.css';

interface MessageProps {
  message: MessageType;
  currentUserName?: string;
  /** 当前合同 ID，用于 [ref:...] 跳转时切换合同 */
  contractId?: string;
  /** review.id → 作者姓名映射，用于 [ref:review-...] 渲染 */
  reviewMap?: Map<string, { authorName: string }>;
  /** comment.id → 作者姓名映射，用于 [ref:comment-...] 渲染 */
  commentMap?: Map<string, { authorName: string }>;
  /** AI 消息流式输出中：跳过折叠测量，避免抖动 */
  isStreaming?: boolean;
}

const Message: React.FC<MessageProps> = memo(
  ({
    message,
    currentUserName,
    contractId,
    reviewMap,
    commentMap,
    isStreaming = false,
  }) => {
    const isUser = message.role === 'user';
    const isThinking = !isUser && isStreaming && !message.content;

    const body = (
      <div className="message-bubble">
        {isThinking ? (
          <p className="message-text message-thinking">
            <LoadingOutlined style={{ marginRight: 6 }} />
            思考中...
          </p>
        ) : (
          <p className="message-text">
            <MessageContent
              text={message.content}
              contractId={contractId}
              reviewMap={reviewMap}
              commentMap={commentMap}
            />
          </p>
        )}
      </div>
    );

    return (
      <div
        className={`message ${isUser ? 'message-user' : 'message-assistant'}`}
        data-testid="message"
        data-role={message.role}
      >
        <div className="message-avatar">
          {isUser ? (
            <Avatar
              size={32}
              style={{ backgroundColor: '#1890ff' }}
              icon={<UserOutlined />}
            >
              {currentUserName?.charAt(0) || 'U'}
            </Avatar>
          ) : (
            <Avatar
              size={32}
              style={{ backgroundColor: '#52c41a' }}
              icon={<RobotOutlined />}
            />
          )}
        </div>

        <div className="message-content-wrapper">
          {isUser ? (
            body
          ) : (
            <CollapsibleMessage
              isStreaming={isStreaming}
              contentKey={message.content}
            >
              {body}
            </CollapsibleMessage>
          )}
          <div className="message-timestamp">
            {formatRelativeTime(message.timestamp)}
          </div>
        </div>
      </div>
    );
  }
);

Message.displayName = 'Message';

export default Message;
