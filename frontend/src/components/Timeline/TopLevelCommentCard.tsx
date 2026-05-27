import React, { useState } from 'react';
import { MessageOutlined } from '@ant-design/icons';
import type { Comment } from '../../types/index';
import { useAddComment } from '../../hooks';
import { formatRelativeTime } from '../../utils/time';
import ReplyList from './ReplyList';
import MentionInput from './MentionInput';
import './ReviewCard.css';

interface TopLevelCommentCardProps {
  comment: Comment;
  contractId: string;
}

const TopLevelCommentCard: React.FC<TopLevelCommentCardProps> = ({ comment, contractId }) => {
  const [showReplyInput, setShowReplyInput] = useState(false);

  const addCommentMutation = useAddComment();

  const handleReply = () => {
    setShowReplyInput(!showReplyInput);
  };

  const handleSendReply = (content: string, mentionedUserIds: string[]) => {
    addCommentMutation.mutate(
      {
        contractId,
        parentCommentId: comment.id,
        content,
        mentionedUserIds,
      },
      {
        onSuccess: () => {
          setShowReplyInput(false);
        },
      }
    );
  };

  const gradient = 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)';

  return (
    <div className="comment-card" id={`anchor-${comment.id}`}>
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
        <MentionInput
          contractId={contractId}
          placeholder={`回复 @${comment.author?.name || '未知用户'}...（输入 @ 提及）`}
          autoFocus
          disabled={addCommentMutation.isPending}
          onSubmit={handleSendReply}
          containerClassName="reply-input-container"
        />
      )}
      {comment.replies && comment.replies.length > 0 && (
        <ReplyList replies={comment.replies} contractId={contractId} />
      )}
    </div>
  );
};

export default TopLevelCommentCard;
