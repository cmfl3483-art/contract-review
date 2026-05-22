import React, { memo } from 'react';
import { Avatar } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import type { Message as MessageType } from '../../types';
import { formatRelativeTime } from '../../utils/time';
import './Message.css';

interface MessageProps {
  message: MessageType;
  currentUserName?: string;
}

const Message: React.FC<MessageProps> = memo(({ message, currentUserName }) => {
  const isUser = message.role === 'user';

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
        <div className="message-bubble">
          <p className="message-text">{message.content}</p>
        </div>
        <div className="message-timestamp">
          {formatRelativeTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
});

Message.displayName = 'Message';

export default Message;
