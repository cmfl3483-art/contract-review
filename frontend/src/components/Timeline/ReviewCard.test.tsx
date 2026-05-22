import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ReviewCard from './ReviewCard';
import type { Review } from '../../types';

describe('ReviewCard', () => {
  const mockReview: Review = {
    id: 'review-1',
    contractId: 'contract-1',
    reviewerId: 'user-1',
    reviewer: {
      id: 'user-1',
      dingtalkUserId: 'dingtalk-1',
      name: '张三',
      role: '法务',
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    role: '法务',
    step: '法务初审',
    opinion: '合同条款清晰，建议在第三条增加违约责任说明。',
    status: 'approved',
    likes: 5,
    likedBy: ['user-2', 'user-3'],
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  };

  it('应该渲染评审卡片', () => {
    render(<ReviewCard review={mockReview} />);

    expect(screen.getByTestId('review-card')).toBeInTheDocument();
  });

  it('应该显示评审人姓名和角色', () => {
    render(<ReviewCard review={mockReview} />);

    expect(screen.getByText('张三')).toBeInTheDocument();
    expect(screen.getByText('法务')).toBeInTheDocument();
  });

  it('应该显示评审意见内容', () => {
    render(<ReviewCard review={mockReview} />);

    expect(screen.getByText('合同条款清晰，建议在第三条增加违约责任说明。')).toBeInTheDocument();
  });

  it('应该显示相对时间', () => {
    render(<ReviewCard review={mockReview} />);

    expect(screen.getByText('2小时前')).toBeInTheDocument();
  });

  it('应该显示已通过状态', () => {
    render(<ReviewCard review={mockReview} />);

    expect(screen.getByText('✅')).toBeInTheDocument();
  });

  it('应该显示评审中状态', () => {
    const reviewingReview = {
      ...mockReview,
      status: 'reviewing' as const,
    };

    render(<ReviewCard review={reviewingReview} />);

    expect(screen.getByText('评审中')).toBeInTheDocument();
  });

  it('应该显示待处理状态', () => {
    const pendingReview = {
      ...mockReview,
      status: 'pending' as const,
    };

    render(<ReviewCard review={pendingReview} />);

    expect(screen.getByText('待处理')).toBeInTheDocument();
  });

  it('应该显示点赞数量', () => {
    render(<ReviewCard review={mockReview} />);

    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('当点赞数为0时应该显示"点赞"文本', () => {
    const reviewWithNoLikes = {
      ...mockReview,
      likes: 0,
      likedBy: [],
    };

    render(<ReviewCard review={reviewWithNoLikes} />);

    expect(screen.getByText('点赞')).toBeInTheDocument();
  });

  it('当用户已点赞时应该显示填充的点赞图标', () => {
    render(<ReviewCard review={mockReview} currentUserId="user-2" />);

    const likeButton = screen.getByTestId('review-like-button');
    expect(likeButton).toHaveClass('review-card-like-btn-active');
  });

  it('当用户未点赞时应该显示空心的点赞图标', () => {
    render(<ReviewCard review={mockReview} currentUserId="user-999" />);

    const likeButton = screen.getByTestId('review-like-button');
    expect(likeButton).not.toHaveClass('review-card-like-btn-active');
  });

  it('点击点赞按钮应该调用 onLike 回调', () => {
    const onLike = vi.fn();
    render(<ReviewCard review={mockReview} currentUserId="user-999" onLike={onLike} />);

    const likeButton = screen.getByTestId('review-like-button');
    fireEvent.click(likeButton);

    expect(onLike).toHaveBeenCalledWith('review-1');
    expect(onLike).toHaveBeenCalledTimes(1);
  });

  it('当没有提供 onLike 回调时点击点赞按钮不应该报错', () => {
    render(<ReviewCard review={mockReview} />);

    const likeButton = screen.getByTestId('review-like-button');
    expect(() => fireEvent.click(likeButton)).not.toThrow();
  });

  it('当评审意见为空时应该显示"参与了讨论"', () => {
    const reviewWithoutOpinion = {
      ...mockReview,
      opinion: undefined,
    };

    render(<ReviewCard review={reviewWithoutOpinion} />);

    expect(screen.getByText('参与了讨论')).toBeInTheDocument();
  });

  it('应该显示评审人头像', () => {
    render(<ReviewCard review={mockReview} />);

    const avatar = screen.getByText('张').closest('.ant-avatar');
    expect(avatar).toBeInTheDocument();
  });

  it('当评审人有头像时应该显示头像图片', () => {
    const reviewWithAvatar = {
      ...mockReview,
      reviewer: {
        ...mockReview.reviewer!,
        avatar: 'https://example.com/avatar.jpg',
      },
    };

    render(<ReviewCard review={reviewWithAvatar} />);

    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://example.com/avatar.jpg');
  });

  it('当评审人信息缺失时应该显示默认文本', () => {
    const reviewWithoutReviewer = {
      ...mockReview,
      reviewer: undefined,
    };

    render(<ReviewCard review={reviewWithoutReviewer} />);

    expect(screen.getByText('未知用户')).toBeInTheDocument();
  });

  it('应该显示评审人姓名的工具提示', () => {
    render(<ReviewCard review={mockReview} />);

    const avatar = screen.getByText('张').closest('.ant-avatar');
    const tooltip = avatar?.closest('[title]');
    expect(tooltip).toHaveAttribute('title', '张三');
  });

  it('应该正确处理多行评审意见', () => {
    const reviewWithMultilineOpinion = {
      ...mockReview,
      opinion: '第一行意见\n第二行意见\n第三行意见',
    };

    render(<ReviewCard review={reviewWithMultilineOpinion} />);

    expect(screen.getByText('第一行意见\n第二行意见\n第三行意见')).toBeInTheDocument();
  });

  it('应该正确处理长文本评审意见', () => {
    const longOpinion = '这是一个非常长的评审意见。'.repeat(50);
    const reviewWithLongOpinion = {
      ...mockReview,
      opinion: longOpinion,
    };

    render(<ReviewCard review={reviewWithLongOpinion} />);

    expect(screen.getByText(longOpinion)).toBeInTheDocument();
  });

  it('应该在悬停时改变卡片样式', () => {
    const { container } = render(<ReviewCard review={mockReview} />);

    const card = container.querySelector('.review-card');
    expect(card).toHaveClass('review-card');
  });
});
