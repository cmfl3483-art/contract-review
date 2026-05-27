import React from 'react';
import { useMention } from '../../hooks/useMention';
import MentionPicker from './MentionPicker';

interface MentionInputProps {
  contractId: string;
  placeholder?: string;
  disabled?: boolean;
  autoFocus?: boolean;
  /** 提交回调，参数为 (content, mentionedUserIds) */
  onSubmit: (content: string, mentionedUserIds: string[]) => void;
  /** 提交按钮文案，默认"发送" */
  submitText?: string;
  /** 容器类名（继承现有 reply-input-container / reply-input-sub 等样式） */
  containerClassName?: string;
}

/**
 * 通用的 @ 提及输入框组件
 * 封装 input + useMention + MentionPicker，所有需要 @ 提及的输入框都用它
 */
const MentionInput: React.FC<MentionInputProps> = ({
  contractId,
  placeholder = '输入内容...',
  disabled = false,
  autoFocus = false,
  onSubmit,
  submitText = '发送',
  containerClassName = 'reply-input-container',
}) => {
  const {
    inputValue,
    mentionQuery,
    isMentionOpen,
    mentionedUserIds,
    showMaxMentionWarning,
    handleInputChange,
    handleUserSelect,
    handleMentionClose,
    reset,
  } = useMention();

  const handleSend = () => {
    const content = inputValue.trim();
    if (!content) return;
    onSubmit(content, mentionedUserIds);
    reset();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleMentionClose();
      return;
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={containerClassName} style={{ position: 'relative' }}>
      <input
        type="text"
        placeholder={placeholder}
        value={inputValue}
        onChange={(e) => handleInputChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        autoFocus={autoFocus}
      />
      <button
        onClick={handleSend}
        disabled={!inputValue.trim() || disabled}
      >
        {submitText}
      </button>
      {showMaxMentionWarning && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            color: '#ff4d4f',
            fontSize: 12,
            marginTop: 4,
          }}
        >
          最多可提及 10 人
        </div>
      )}
      {isMentionOpen && (
        <MentionPicker
          query={mentionQuery}
          contractId={contractId}
          onSelect={handleUserSelect}
          onClose={handleMentionClose}
        />
      )}
    </div>
  );
};

export default MentionInput;
