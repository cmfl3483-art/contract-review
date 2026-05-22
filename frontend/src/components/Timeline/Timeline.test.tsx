import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Timeline from './Timeline';
import * as useReviewsHook from '../../hooks/useReviews';
import * as authStore from '../../store/authStore';
import type { ReviewsResponse, User } from '../../types';

// Mock the hooks
vi.mock('../../hooks/useReviews');
vi.mock('../../store/authStore');

describe('Timeline', () => {
  let queryClient: QueryClient;

  const mockUser: User = {
    id: 'user-1',
    dingtalkUserId: 'dingtalk-1',
    name: '测试用户',
    role: '销售',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
  };

  const mockReviewsData: ReviewsResponse = {
    reviews: [
      {
        id: 'review-1',
        contractId: 'contract-1',
        reviewerId: 'user-2',
        reviewer: {
          id: 'user-2',
          dingtalkUserId: 'dingtalk-2',
          name: '张三',
          role: '法务',
          createdAt: '2025-01-01T00:00:00Z',
          updatedAt: '2025-01-01T00:00:00Z',
        },
        role: '法务',
        step: '法务初审',
        opinion: '合同条款需要修改',
        status: 'approved',
        likes: 5,
        likedBy: ['user-1'],
        createdAt: '2025-01-02T10:00:00Z',
        updatedAt: '2025-01-02T10:00:00Z',
      },
      {
        id: 'review-2',
        contractId: 'contract-1',
        reviewerId: 'user-3',
        reviewer: {
          id: 'user-3',
          dingtalkUserId: 'dingtalk-3',
          name: '李四',
          role: '财务',
          createdAt: '2025-01-01T00:00:00Z',
          updatedAt: '2025-01-01T00:00:00Z',
        },
        role: '财务',
        step: '财务审核',
        opinion: '预算合理',
        status: 'approved',
        likes: 3,
        likedBy: [],
        createdAt: '2025-01-01T09:00:00Z',
        updatedAt: '2025-01-01T09:00:00Z',
      },
    ],
    aiSummary: {
      id: 'summary-1',
      contractId: 'contract-1',
      approvalStatus: 'in_progress',
      completedCount: 2,
      totalCount: 3,
      reviewCount: 2,
      keyIssues: [
        {
          issue: '合同条款需要修改',
          solution: '已联系法务部门',
        },
      ],
      createdAt: '2025-01-02T10:00:00Z',
      updatedAt: '2025-01-02T10:00:00Z',
    },
  };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    // Mock useAuthStore
    vi.mocked(authStore.useAuthStore).mockReturnValue(mockUser);

    // Mock useLikeReview and useLikeComment
    vi.mocked(useReviewsHook.useLikeReview).mockReturnValue({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
    } as any);

    vi.mocked(useReviewsHook.useLikeComment).mockReturnValue({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
    } as any);
  });

  const renderTimeline = (contractId: string) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <Timeline contractId={contractId} />
      </QueryClientProvider>
    );
  };

  it('应该显示加载状态', () => {
    vi.mocked(useReviewsHook.useReviews).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as any);

    renderTimeline('contract-1');

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('应该显示错误状态', () => {
    vi.mocked(useReviewsHook.useReviews).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('加载失败'),
    } as any);

    renderTimeline('contract-1');

    expect(screen.getByText('加载失败,请稍后重试')).toBeInTheDocument();
  });

  it('应该显示空状态', () => {
    vi.mocked(useReviewsHook.useReviews).mockReturnValue({
      data: { reviews: [], aiSummary: null },
      isLoading: false,
      error: null,
    } as any);

    renderTimeline('contract-1');

    expect(screen.getByText('暂无评审记录')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('添加第一条评论...')).toBeInTheDocument();
  });

  it('应该显示AI智能总结', async () => {
    vi.mocked(useReviewsHook.useReviews).mockReturnValue({
      data: mockReviewsData,
      isLoading: false,
      error: null,
    } as any);

    renderTimeline('contract-1');

    await waitFor(() => {
      expect(screen.getByText('AI 智能总结')).toBeInTheDocument();
      expect(screen.getByText('审批进行中')).toBeInTheDocument();
      expect(screen.getByText('2/3 人')).toBeInTheDocument();
    });
  });

  it('应该按时间倒序显示评审记录', async () => {
    vi.mocked(useReviewsHook.useReviews).mockReturnValue({
      data: mockReviewsData,
      isLoading: false,
      error: null,
    } as any);

    renderTimeline('contract-1');

    await waitFor(() => {
      const reviewCards = screen.getAllByTestId('review-card');
      expect(reviewCards).toHaveLength(2);

      // 第一个应该是最新的评审(张三)
      expect(reviewCards[0]).toHaveTextContent('张三');
      // 第二个应该是较早的评审(李四)
      expect(reviewCards[1]).toHaveTextContent('李四');
    });
  });

  it('应该过滤空评审记录', async () => {
    const dataWithEmptyReviews: ReviewsResponse = {
      reviews: [
        ...mockReviewsData.reviews,
        {
          id: 'review-3',
          contractId: 'contract-1',
          reviewerId: 'user-4',
          reviewer: {
            id: 'user-4',
            dingtalkUserId: 'dingtalk-4',
            name: '王五',
            role: '业务',
            createdAt: '2025-01-01T00:00:00Z',
            updatedAt: '2025-01-01T00:00:00Z',
          },
          role: '业务',
          step: '业务审核',
          opinion: '待评审',
          status: 'pending',
          likes: 0,
          likedBy: [],
          createdAt: '2025-01-03T10:00:00Z',
          updatedAt: '2025-01-03T10:00:00Z',
        },
      ],
      aiSummary: null,
    };

    vi.mocked(useReviewsHook.useReviews).mockReturnValue({
      data: dataWithEmptyReviews,
      isLoading: false,
      error: null,
    } as any);

    renderTimeline('contract-1');

    await waitFor(() => {
      const reviewCards = screen.getAllByTestId('review-card');
      // 应该只显示2个有效评审,过滤掉"待评审"的记录
      expect(reviewCards).toHaveLength(2);
    });
  });

  it('应该显示评论输入框', async () => {
    vi.mocked(useReviewsHook.useReviews).mockReturnValue({
      data: mockReviewsData,
      isLoading: false,
      error: null,
    } as any);

    renderTimeline('contract-1');

    await waitFor(() => {
      expect(screen.getByPlaceholderText('添加评论...')).toBeInTheDocument();
    });
  });

  it('应该渲染Timeline容器', async () => {
    vi.mocked(useReviewsHook.useReviews).mockReturnValue({
      data: mockReviewsData,
      isLoading: false,
      error: null,
    } as any);

    renderTimeline('contract-1');

    await waitFor(() => {
      expect(screen.getByTestId('timeline')).toBeInTheDocument();
    });
  });
});
