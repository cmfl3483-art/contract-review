import React, { useState } from 'react';
import { MessageOutlined } from '@ant-design/icons';
import type { Review } from '../../types/index';
import { useAddComment } from '../../hooks';
import { formatRelativeTime } from '../../utils/time';
import ReplyList from './ReplyList';
import MentionInput from './MentionInput';
import './ReviewCard.css';

interface ReviewCardProps {
  review: Review;
  contractId: string;
}

const ReviewCard: React.FC<ReviewCardProps> = ({ review, contractId }) => {
  const [showReplyInput, setShowReplyInput] = useState(false);

  const addCommentMutation = useAddComment();

  const handleReply = () => {
    setShowReplyInput(!showReplyInput);
  };

  const handleSendReply = (content: string, mentionedUserIds: string[]) => {
    addCommentMutation.mutate(
      {
        contractId,
        reviewId: review.id,
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

  const getAvatarGradient = () => {
    const gradients = [
      'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
      'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    ];
    const idx = review.reviewer?.name ? review.reviewer.name.charCodeAt(0) % gradients.length : 0;
    return gradients[idx];
  };

  // 过滤空评审记录
  if (!review.opinion || review.opinion === '待评审' || review.opinion.trim() === '') {
    return null;
  }

  return (
    <div className="comment-card" id={`anchor-${review.id}`}>
      <div className="comment-header">
        <div className="comment-avatar" style={{ background: getAvatarGradient() }}>
          {review.reviewer?.name?.charAt(0) || '?'}
          <div className="avatar-tooltip">{review.reviewer?.name || '未知用户'}</div>
        </div>
        <div className="comment-content">
          <span className="comment-author">{review.reviewer?.name || '未知用户'}</span>
          <span className="comment-colon">：</span>
          <span className="comment-text">{review.opinion}</span>
        </div>
        <span className="comment-time">{formatRelativeTime(review.createdAt)}</span>
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
          placeholder={`回复 @${review.reviewer?.name || '未知用户'}...（输入 @ 提及）`}
          autoFocus
          disabled={addCommentMutation.isPending}
          onSubmit={handleSendReply}
          containerClassName="reply-input-container"
        />
      )}
      {review.replies && review.replies.length > 0 && (
        <ReplyList replies={review.replies} contractId={contractId} reviewId={review.id} />
      )}
    </div>
  );
};

export default ReviewCard;
