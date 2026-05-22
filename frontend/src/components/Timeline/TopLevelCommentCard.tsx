import React, { useState } from 'react';
import { MessageOutlined } from '@ant-design/icons';
import type { Comment } from '../../types/index';
import { useAddComment } from '../../hooks';
import { formatRelativeTime } from '../../utils/time';
import ReplyList from './ReplyList';
import './ReviewCard.css';

interface TopLevelCommentCardProps {
  comment: Comment;
  contractId: string;
}

const TopLevelCommentCard: React.FC<TopLevelCommentCardProps> = ({ comment, contractId }) => {
  const [showReplyInput, setShowReplyInput] = useState(false);
  const [replyContent, setReplyContent] = useState('');

  const addCommentMutation = useAddComment();

  const handleReply = () => {
    setShowReplyInput(!showReplyInput);
    setReplyContent('');
  };

  const handleSendReply = () => {
    if (!replyContent.trim()) return;
    addCommentMutation.mutate(
      {
        contractId,
        parentCommentId: comment.id,
        content: replyContent.trim(),
      },
      {
        onSuccess: () => {
          setShowReplyInput(false);
          setReplyContent('');
        },
      }
    );
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendReply();
    }
  };

  const gradient = 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)';

  return (
    <div className="comment-card">
      <div className="comment-header">
        <div className="comment-avatar" style={{ background: gradient }}>
          {comment.author?.name?.charAt(0) || '?'}
          <div className="avatar-tooltip">{comment.author?.name || '未知用户'}</div>
        </div>
        <div className="comment-content">
          <span className="comment-author">{comment.author?.name || '未知用户'}</span>
          <span className="comment-colon">：</span>
          <span className="comment-text">{comment.content}</span>
        </div>
        <span className="comment-time">{formatRelativeTime(comment.createdAt)}</span>
      </div>
      <div className="action-buttons">
        <button className="action-btn" onClick={handleReply}>
          <MessageOutlined />
          <span className="action-text">回复</span>
        </button>
      </div>
      {showReplyInput && (
        <div className="reply-input-container">
          <input
            type="text"
            placeholder={`回复 @${comment.author?.name || '未知用户'}...`}
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            onKeyPress={handleKeyPress}
            autoFocus
          />
          <button
            onClick={handleSendReply}
            disabled={!replyContent.trim() || addCommentMutation.isPending}
          >
            发送
          </button>
        </div>
      )}
      {comment.replies && comment.replies.length > 0 && (
        <ReplyList replies={comment.replies} contractId={contractId} />
      )}
    </div>
  );
};

export default TopLevelCommentCard;
