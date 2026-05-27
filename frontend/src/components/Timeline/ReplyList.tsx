import React, { useState, useEffect, useMemo } from 'react';
import { MessageOutlined } from '@ant-design/icons';
import type { Comment } from '../../types/index';
import { useAddComment } from '../../hooks';
import { formatRelativeTime } from '../../utils/time';
import { useFocusedAnchorStore } from '../../stores/useFocusedAnchorStore';
import MentionInput from './MentionInput';
import './ReplyList.css';

interface ReplyListProps {
  replies: Comment[];
  contractId: string;
  reviewId?: string;
}

// 扁平化项: 携带"被回复对象"作者名, 用于显示 @某某
interface FlatReply {
  comment: Comment;
  replyToName?: string;
}

/** 深度优先扁平化整棵回复树, 第一层 replyToName 为 undefined */
function flattenReplies(items: Comment[], replyToName?: string): FlatReply[] {
  const result: FlatReply[] = [];
  for (const c of items) {
    result.push({ comment: c, replyToName });
    if (c.replies && c.replies.length > 0) {
      result.push(...flattenReplies(c.replies, c.author?.name));
    }
  }
  return result;
}

const ReplyList: React.FC<ReplyListProps> = ({ replies, contractId, reviewId }) => {
  const flatList = flattenReplies(replies);
  const focusedAnchorId = useFocusedAnchorStore((s) => s.anchorId);

  // 如果聚焦的 anchor 在被折叠区域里（索引 >= 2），需要展开
  const focusedInCollapsed = useMemo(() => {
    if (!focusedAnchorId) return false;
    const idx = flatList.findIndex((f) => f.comment.id === focusedAnchorId);
    return idx >= 2;
  }, [focusedAnchorId, flatList]);

  const [collapsed, setCollapsed] = useState(flatList.length > 2);
  const [replyingTo, setReplyingTo] = useState<string | null>(null);

  // 当聚焦的 anchor 在折叠区域时，自动展开
  useEffect(() => {
    if (focusedInCollapsed) {
      setCollapsed(false);
    }
  }, [focusedInCollapsed]);

  const addCommentMutation = useAddComment();

  const handleReply = (commentId: string) => {
    setReplyingTo(commentId);
  };

  const handleSendReply = (parentCommentId: string) => (content: string, mentionedUserIds: string[]) => {
    addCommentMutation.mutate(
      {
        contractId,
        reviewId,
        parentCommentId,
        content,
        mentionedUserIds,
      },
      {
        onSuccess: () => {
          setReplyingTo(null);
        },
      }
    );
  };

  const displayed = collapsed ? flatList.slice(0, 2) : flatList;
  const hasMore = flatList.length > 2;

  const getAvatarGradient = (index: number) => {
    const gradients = [
      'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
      'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
      'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
    ];
    return gradients[index % gradients.length];
  };

  return (
    <div className="replies-container">
      {displayed.map(({ comment: reply, replyToName }, index) => (
        <div key={reply.id} className="reply-card" id={`anchor-${reply.id}`}>
          <div className="reply-row">
            <div
              className="reply-avatar"
              style={{ background: getAvatarGradient(index) }}
              title={reply.author?.name || '未知用户'}
            >
              {reply.author?.name?.charAt(0) || '?'}
            </div>
            <div className="reply-body">
              <span className="reply-author">{reply.author?.name || '未知用户'}</span>
              {replyToName && (
                <span className="reply-target"> 回复 @{replyToName}</span>
              )}
              <span className="reply-colon">：</span>
              <span className="reply-text">{reply.content}</span>
            </div>
            <span className="reply-time">{formatRelativeTime(reply.createdAt)}</span>
          </div>
          <div className="reply-actions">
            <button className="reply-action-btn" onClick={() => handleReply(reply.id)}>
              <MessageOutlined />
              <span>回复</span>
            </button>
          </div>
          {replyingTo === reply.id && (
            <MentionInput
              contractId={contractId}
              placeholder={`回复 @${reply.author?.name || '未知用户'}...（输入 @ 提及）`}
              autoFocus
              disabled={addCommentMutation.isPending}
              onSubmit={handleSendReply(reply.id)}
              containerClassName="reply-input-sub"
            />
          )}
        </div>
      ))}
      {hasMore && (
        <button className="toggle-replies-btn" onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? `展开全部 ${flatList.length} 条回复` : '收起回复'}
        </button>
      )}
    </div>
  );
};

export default ReplyList;
