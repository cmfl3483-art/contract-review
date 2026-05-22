import React, { useState } from 'react';
import { message } from 'antd';
import { useAddComment } from '../../hooks';
import './CommentInput.css';

interface CommentInputProps {
  contractId: string;
}

const CommentInput: React.FC<CommentInputProps> = ({ contractId }) => {
  const [content, setContent] = useState('');
  const addCommentMutation = useAddComment();

  const handleSend = async () => {
    if (!content.trim()) {
      message.warning('请输入评论内容');
      return;
    }

    try {
      await addCommentMutation.mutateAsync({
        contractId,
        content: content.trim(),
      });
      
      setContent('');
      message.success('评论发送成功');
    } catch (error) {
      console.error('Failed to send comment:', error);
      message.error(error instanceof Error ? error.message : '评论发送失败');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="comment-input-area">
      <input
        type="text"
        placeholder="添加评论..."
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyPress={handleKeyPress}
        disabled={addCommentMutation.isPending}
      />
      <button 
        onClick={handleSend} 
        disabled={!content.trim() || addCommentMutation.isPending}
      >
        {addCommentMutation.isPending ? '发送中...' : '发送'}
      </button>
    </div>
  );
};

export default CommentInput;
