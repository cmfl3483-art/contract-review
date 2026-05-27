import React from 'react';
import { message } from 'antd';
import { useAddComment } from '../../hooks';
import { useMention } from '../../hooks/useMention';
import MentionPicker from './MentionPicker';
import './CommentInput.css';

interface CommentInputProps {
  contractId: string;
}

const CommentInput: React.FC<CommentInputProps> = ({ contractId }) => {
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

  const addCommentMutation = useAddComment();

  const handleSend = async () => {
    if (!inputValue.trim()) {
      message.warning('请输入评论内容');
      return;
    }

    try {
      await addCommentMutation.mutateAsync({
        contractId,
        content: inputValue.trim(),
        mentionedUserIds,
      });

      reset();
      message.success('评论发送成功');
    } catch (error) {
      console.error('Failed to send comment:', error);
      message.error(error instanceof Error ? error.message : '评论发送失败');
    }
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
    <div className="comment-input-area">
      <div style={{ position: 'relative', flex: 1, alignSelf: 'flex-end' }}>
        <input
          type="text"
          placeholder="添加评论... (输入 @ 提及用户)"
          value={inputValue}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={addCommentMutation.isPending}
        />
        {showMaxMentionWarning && (
          <div style={{ color: '#ff4d4f', fontSize: 12, marginTop: 4 }}>
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
      <button
        style={{ alignSelf: 'flex-end' }}
        onClick={handleSend}
        disabled={!inputValue.trim() || addCommentMutation.isPending}
      >
        {addCommentMutation.isPending ? '发送中...' : '发送'}
      </button>
    </div>
  );
};

export default CommentInput;
