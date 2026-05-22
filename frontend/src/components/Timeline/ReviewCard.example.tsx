import React, { useState } from 'react';
import ReviewCard from './ReviewCard';
import type { Review } from '../../types';

/**
 * ReviewCard Component Examples
 *
 * This file demonstrates various use cases of the ReviewCard component
 */

// Mock data
const mockReviews: Review[] = [
  {
    id: 'review-1',
    contractId: 'contract-1',
    reviewerId: 'user-1',
    reviewer: {
      id: 'user-1',
      dingtalkUserId: 'dingtalk-1',
      name: '张三',
      role: '法务',
      avatar: undefined,
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    role: '法务',
    step: '法务初审',
    opinion: '合同条款清晰，建议在第三条增加违约责任说明。',
    status: 'approved',
    likes: 5,
    likedBy: ['user-2', 'user-3'],
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'review-2',
    contractId: 'contract-1',
    reviewerId: 'user-2',
    reviewer: {
      id: 'user-2',
      dingtalkUserId: 'dingtalk-2',
      name: '李四',
      role: '财务',
      avatar: undefined,
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    role: '财务',
    step: '财务审核',
    opinion: '预算合理，付款条款需要明确具体时间节点。',
    status: 'reviewing',
    likes: 3,
    likedBy: ['user-1'],
    createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'review-3',
    contractId: 'contract-1',
    reviewerId: 'user-3',
    reviewer: {
      id: 'user-3',
      dingtalkUserId: 'dingtalk-3',
      name: '王五',
      role: '业务',
      avatar: undefined,
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    role: '业务',
    step: '业务审核',
    opinion: undefined, // No opinion, will show "参与了讨论"
    status: 'pending',
    likes: 0,
    likedBy: [],
    createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'review-4',
    contractId: 'contract-1',
    reviewerId: 'user-4',
    reviewer: {
      id: 'user-4',
      dingtalkUserId: 'dingtalk-4',
      name: '赵六',
      role: '运营',
      avatar: 'https://i.pravatar.cc/150?img=1',
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    role: '运营',
    step: '运营审核',
    opinion:
      '从运营角度看，合同执行周期较长，建议增加阶段性验收条款。\n同时需要明确双方的沟通机制和响应时间。\n整体方案可行，同意通过。',
    status: 'approved',
    likes: 8,
    likedBy: ['user-1', 'user-2', 'user-3'],
    createdAt: new Date(Date.now() - 35 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 35 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

/**
 * Example 1: Basic ReviewCard
 */
export function BasicReviewCard() {
  return (
    <div style={{ maxWidth: 600, margin: '20px auto' }}>
      <h2>基础评审卡片</h2>
      <ReviewCard review={mockReviews[0]} />
    </div>
  );
}

/**
 * Example 2: ReviewCard with Like Functionality
 */
export function ReviewCardWithLike() {
  const [reviews, setReviews] = useState(mockReviews);
  const currentUserId = 'user-current';

  const handleLike = (reviewId: string) => {
    setReviews((prevReviews) =>
      prevReviews.map((review) => {
        if (review.id === reviewId) {
          const isLiked = review.likedBy.includes(currentUserId);
          return {
            ...review,
            likes: isLiked ? review.likes - 1 : review.likes + 1,
            likedBy: isLiked
              ? review.likedBy.filter((id) => id !== currentUserId)
              : [...review.likedBy, currentUserId],
          };
        }
        return review;
      })
    );
  };

  return (
    <div style={{ maxWidth: 600, margin: '20px auto' }}>
      <h2>带点赞功能的评审卡片</h2>
      {reviews.map((review) => (
        <ReviewCard
          key={review.id}
          review={review}
          currentUserId={currentUserId}
          onLike={handleLike}
        />
      ))}
    </div>
  );
}

/**
 * Example 3: Different Review Statuses
 */
export function ReviewStatusExamples() {
  return (
    <div style={{ maxWidth: 600, margin: '20px auto' }}>
      <h2>不同状态的评审卡片</h2>

      <h3>已通过 (Approved)</h3>
      <ReviewCard review={mockReviews[0]} />

      <h3>评审中 (Reviewing)</h3>
      <ReviewCard review={mockReviews[1]} />

      <h3>待处理 (Pending)</h3>
      <ReviewCard review={mockReviews[2]} />
    </div>
  );
}

/**
 * Example 4: Review Without Opinion
 */
export function ReviewWithoutOpinion() {
  return (
    <div style={{ maxWidth: 600, margin: '20px auto' }}>
      <h2>无意见的评审卡片（显示"参与了讨论"）</h2>
      <ReviewCard review={mockReviews[2]} />
    </div>
  );
}

/**
 * Example 5: Review with Multi-line Opinion
 */
export function ReviewWithMultilineOpinion() {
  return (
    <div style={{ maxWidth: 600, margin: '20px auto' }}>
      <h2>多行意见的评审卡片</h2>
      <ReviewCard review={mockReviews[3]} />
    </div>
  );
}

/**
 * Example 6: Review with Avatar
 */
export function ReviewWithAvatar() {
  return (
    <div style={{ maxWidth: 600, margin: '20px auto' }}>
      <h2>带头像的评审卡片</h2>
      <ReviewCard review={mockReviews[3]} />
    </div>
  );
}

/**
 * Example 7: Timeline with Multiple Reviews
 */
export function TimelineExample() {
  const [reviews, setReviews] = useState(mockReviews);
  const currentUserId = 'user-current';

  const handleLike = (reviewId: string) => {
    setReviews((prevReviews) =>
      prevReviews.map((review) => {
        if (review.id === reviewId) {
          const isLiked = review.likedBy.includes(currentUserId);
          return {
            ...review,
            likes: isLiked ? review.likes - 1 : review.likes + 1,
            likedBy: isLiked
              ? review.likedBy.filter((id) => id !== currentUserId)
              : [...review.likedBy, currentUserId],
          };
        }
        return review;
      })
    );
  };

  return (
    <div style={{ maxWidth: 600, margin: '20px auto' }}>
      <h2>完整时间线示例</h2>
      <div style={{ background: '#f5f5f5', padding: 16, borderRadius: 8 }}>
        {reviews.map((review) => (
          <ReviewCard
            key={review.id}
            review={review}
            currentUserId={currentUserId}
            onLike={handleLike}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Default export: All examples
 */
export default function ReviewCardExamples() {
  return (
    <div>
      <BasicReviewCard />
      <ReviewCardWithLike />
      <ReviewStatusExamples />
      <ReviewWithoutOpinion />
      <ReviewWithMultilineOpinion />
      <ReviewWithAvatar />
      <TimelineExample />
    </div>
  );
}
