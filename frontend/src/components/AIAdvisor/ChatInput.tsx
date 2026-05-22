import React, { useState, memo } from 'react';
import type { KeyboardEvent } from 'react';
import { Input, Button, Space } from 'antd';
import { SendOutlined } from '@ant-design/icons';

interface ChatInputProps {
  onSend: (message: string) => void;
  loading?: boolean;
  placeholder?: string;
}

const ChatInput: React.FC<ChatInputProps> = memo(({
  onSend,
  loading = false,
  placeholder = '输入您的问题...',
}) => {
  const [inputValue, setInputValue] = useState('');

  const handleSend = () => {
    const trimmedValue = inputValue.trim();
    if (trimmedValue && !loading) {
      onSend(trimmedValue);
      setInputValue('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Space.Compact style={{ width: '100%' }}>
      <Input
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={placeholder}
        disabled={loading}
      />
      <Button
        type="primary"
        icon={<SendOutlined />}
        onClick={handleSend}
        disabled={loading || !inputValue.trim()}
        loading={loading}
      >
        发送
      </Button>
    </Space.Compact>
  );
});

ChatInput.displayName = 'ChatInput';

export default ChatInput;
