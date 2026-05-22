import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ReplyList from './ReplyList';
import type { Comment } from '../../types';

// Mock the time utility
vi.mock('../../utils/time', () => ({
  formatRelativeTime: () => '5分钟前',
}));

// Mock the avatar utility
vi.mock('../../utils/avatar', () => ({
  getAvatarColor: () => '#1890ff',
  getInitials: (name: string) => name.charAt(0),
}));

describe('ReplyList', () => {
  const mockReplies: Comment[] = [
    {
      id: '1',
      contractId: 'contract-1',
      reviewId: 'review-1',
      authorId: 'user-1',
      author: {
        id: 'user-1',
        name: '张三',
        dingtalkUserId: 'dt-1',
        role: '法务',
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      },
      content: '这是第一条回复',
      likes: 2,
      likedBy: ['user-2', 'user-3'],
      createdAt: '2025-03-15T10:00:00Z',
      updatedAt: '2025-03-15T10:00:00Z',
    },
    {
      id: '2',
      contractId: 'contract-1',
      reviewId: 'review-1',
      authorId: 'user-2',
      author: {
        id: 'user-2',
        name: '李四',
        dingtalkUserId: 'dt-2',
        role: '财务',
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      },
      content: '这是第二条回复',
      likes: 1,
      likedBy: ['user-1'],
      createdAt: '2025-03-15T10:05:00Z',
      updatedAt: '2025-03-15T10:05:00Z',
    },
    {
      id: '3',
      contractId: 'contract-1',
      reviewId: 'review-1',
      authorId: 'user-3',
      author: {
        id: 'user-3',
        name: '王五',
        dingtalkUserId: 'dt-3',
        role: '业务',
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      },
      content: '这是第三条回复',
      likes: 0,
      likedBy: [],
      createdAt: '2025-03-15T10:10:00Z',
      updatedAt: '2025-03-15T10:10:00Z',
    },
  ];

  it('应该渲染回复列表', () => {
    render(<ReplyList replies={mockReplies} />);

    // Should show first 2 replies by default (collapsed)
    expect(screen.getByText('这是第一条回复')).toBeInTheDocument();
    expect(screen.getByText('这是第二条回复')).toBeInTheDocument();
    expect(screen.queryByText('这是第三条回复')).not.toBeInTheDocument();
  });

  it('应该显示作者名称和时间', () => {
    render(<ReplyList replies={mockReplies} />);

    expect(screen.getByText('张三')).toBeInTheDocument();
    expect(screen.getByText('李四')).toBeInTheDocument();
    expect(screen.getAllByText('5分钟前')).toHaveLength(2);
  });

  it('应该显示点赞数量', () => {
    render(<ReplyList replies={mockReplies} />);

    expect(screen.getByText('2')).toBeInTheDocument(); // First reply has 2 likes
    expect(screen.getByText('1')).toBeInTheDocument(); // Second reply has 1 like
  });

  it('当回复超过2条时应该显示展开按钮', () => {
    render(<ReplyList replies={mockReplies} />);

    const toggleButton = screen.getByText('共3条回复');
    expect(toggleButton).toBeInTheDocument();
  });

  it('点击展开按钮应该显示所有回复', () => {
    render(<ReplyList replies={mockReplies} />);

    const toggleButton = screen.getByText('共3条回复');
    fireEvent.click(toggleButton);

    // All replies should be visible
    expect(screen.getByText('这是第一条回复')).toBeInTheDocument();
    expect(screen.getByText('这是第二条回复')).toBeInTheDocument();
    expect(screen.getByText('这是第三条回复')).toBeInTheDocument();

    // Button text should change to "收起"
    expect(screen.getByText('收起')).toBeInTheDocument();
  });

  it('点击收起按钮应该折叠回复', () => {
    render(<ReplyList replies={mockReplies} />);

    // Expand first
    const toggleButton = screen.getByText('共3条回复');
    fireEvent.click(toggleButton);

    // Then collapse
    const collapseButton = screen.getByText('收起');
    fireEvent.click(collapseButton);

    // Should show only first 2 replies
    expect(screen.getByText('这是第一条回复')).toBeInTheDocument();
    expect(screen.getByText('这是第二条回复')).toBeInTheDocument();
    expect(screen.queryByText('这是第三条回复')).not.toBeInTheDocument();
  });

  it('当回复少于等于2条时不应该显示展开按钮', () => {
    const twoReplies = mockReplies.slice(0, 2);
    render(<ReplyList replies={twoReplies} />);

    expect(screen.queryByText(/共.*条回复/)).not.toBeInTheDocument();
    expect(screen.queryByText('收起')).not.toBeInTheDocument();
  });

  it('应该调用onLike回调', () => {
    const onLike = vi.fn();
    render(<ReplyList replies={mockReplies} onLike={onLike} />);

    // Click like button on first reply
    const likeButtons = screen.getAllByRole('button', { name: /like/i });
    fireEvent.click(likeButtons[0]);

    expect(onLike).toHaveBeenCalledWith('1');
  });

  it('当用户已点赞时应该显示已点赞状态', () => {
    render(<ReplyList replies={mockReplies} currentUserId="user-2" />);

    // First reply is liked by user-2
    const likeButtons = screen.getAllByRole('button');
    const firstLikeButton = likeButtons.find((btn) => btn.className.includes('reply-like-button'));

    expect(firstLikeButton).toHaveClass('liked');
  });

  it('当没有回复时不应该渲染任何内容', () => {
    const { container } = render(<ReplyList replies={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('当回复为undefined时不应该渲染任何内容', () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { container } = render(<ReplyList replies={undefined as any} />);
    expect(container.firstChild).toBeNull();
  });
});
