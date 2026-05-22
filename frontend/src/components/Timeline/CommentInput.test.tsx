import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CommentInput from './CommentInput';
import * as useReviewsHook from '../../hooks/useReviews';

// Mock the useAddComment hook
vi.mock('../../hooks/useReviews', () => ({
  useAddComment: vi.fn(),
}));

// Mock antd message
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    message: {
      success: vi.fn(),
      warning: vi.fn(),
      error: vi.fn(),
    },
  };
});

describe('CommentInput', () => {
  let queryClient: QueryClient;
  let mockMutateAsync: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    mockMutateAsync = vi.fn();
    vi.mocked(useReviewsHook.useAddComment).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      isSuccess: false,
      error: null,
      data: undefined,
      mutate: vi.fn(),
      reset: vi.fn(),
      status: 'idle',
      variables: undefined,
      context: undefined,
      failureCount: 0,
      failureReason: null,
      isIdle: true,
      isPaused: false,
      submittedAt: 0,
    });
  });

  const renderComponent = (props = {}) => {
    const defaultProps = {
      contractId: 'contract-123',
    };

    return render(
      <QueryClientProvider client={queryClient}>
        <CommentInput {...defaultProps} {...props} />
      </QueryClientProvider>
    );
  };

  it('应该渲染输入框和发送按钮', () => {
    renderComponent();

    expect(screen.getByPlaceholderText('输入评论内容...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /发送/i })).toBeInTheDocument();
  });

  it('应该使用自定义占位符文本', () => {
    renderComponent({ placeholder: '自定义占位符' });

    expect(screen.getByPlaceholderText('自定义占位符')).toBeInTheDocument();
  });

  it('应该在输入框为空时禁用发送按钮', () => {
    renderComponent();

    const sendButton = screen.getByRole('button', { name: /发送/i });
    expect(sendButton).toBeDisabled();
  });

  it('应该在输入内容后启用发送按钮', () => {
    renderComponent();

    const input = screen.getByPlaceholderText('输入评论内容...');
    fireEvent.change(input, { target: { value: '测试评论' } });

    const sendButton = screen.getByRole('button', { name: /发送/i });
    expect(sendButton).not.toBeDisabled();
  });

  it('应该在点击发送按钮时提交评论', async () => {
    mockMutateAsync.mockResolvedValue({ comment: { id: 'comment-1' } });
    renderComponent();

    const input = screen.getByPlaceholderText('输入评论内容...');
    fireEvent.change(input, { target: { value: '测试评论' } });

    const sendButton = screen.getByRole('button', { name: /发送/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        contractId: 'contract-123',
        reviewId: undefined,
        parentCommentId: undefined,
        content: '测试评论',
      });
    });
  });

  it('应该在按回车键时提交评论', async () => {
    mockMutateAsync.mockResolvedValue({ comment: { id: 'comment-1' } });
    renderComponent();

    const input = screen.getByPlaceholderText('输入评论内容...');
    fireEvent.change(input, { target: { value: '测试评论' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        contractId: 'contract-123',
        reviewId: undefined,
        parentCommentId: undefined,
        content: '测试评论',
      });
    });
  });

  it('应该在提交成功后清空输入框', async () => {
    mockMutateAsync.mockResolvedValue({ comment: { id: 'comment-1' } });
    renderComponent();

    const input = screen.getByPlaceholderText('输入评论内容...') as HTMLInputElement;
    fireEvent.change(input, { target: { value: '测试评论' } });

    const sendButton = screen.getByRole('button', { name: /发送/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });

  it('应该在提交成功后调用回调函数', async () => {
    mockMutateAsync.mockResolvedValue({ comment: { id: 'comment-1' } });
    const onCommentAdded = vi.fn();
    renderComponent({ onCommentAdded });

    const input = screen.getByPlaceholderText('输入评论内容...');
    fireEvent.change(input, { target: { value: '测试评论' } });

    const sendButton = screen.getByRole('button', { name: /发送/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(onCommentAdded).toHaveBeenCalled();
    });
  });

  it('应该支持回复评审意见', async () => {
    mockMutateAsync.mockResolvedValue({ comment: { id: 'comment-1' } });
    renderComponent({ reviewId: 'review-123' });

    const input = screen.getByPlaceholderText('输入评论内容...');
    fireEvent.change(input, { target: { value: '回复评审' } });

    const sendButton = screen.getByRole('button', { name: /发送/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        contractId: 'contract-123',
        reviewId: 'review-123',
        parentCommentId: undefined,
        content: '回复评审',
      });
    });
  });

  it('应该支持嵌套回复', async () => {
    mockMutateAsync.mockResolvedValue({ comment: { id: 'comment-1' } });
    renderComponent({ parentCommentId: 'comment-456' });

    const input = screen.getByPlaceholderText('输入评论内容...');
    fireEvent.change(input, { target: { value: '嵌套回复' } });

    const sendButton = screen.getByRole('button', { name: /发送/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        contractId: 'contract-123',
        reviewId: undefined,
        parentCommentId: 'comment-456',
        content: '嵌套回复',
      });
    });
  });

  it('应该在内容为空时显示警告', async () => {
    const { message } = await import('antd');
    renderComponent();

    const input = screen.getByPlaceholderText('输入评论内容...');
    fireEvent.change(input, { target: { value: '   ' } }); // 只有空格

    const sendButton = screen.getByRole('button', { name: /发送/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(message.warning).toHaveBeenCalledWith('评论内容不能为空');
    });
  });

  it('应该在加载时禁用输入框和按钮', () => {
    vi.mocked(useReviewsHook.useAddComment).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      isSuccess: false,
      error: null,
      data: undefined,
      mutate: vi.fn(),
      reset: vi.fn(),
      status: 'pending',
      variables: undefined,
      context: undefined,
      failureCount: 0,
      failureReason: null,
      isIdle: false,
      isPaused: false,
      submittedAt: Date.now(),
    });

    renderComponent();

    const input = screen.getByPlaceholderText('输入评论内容...');
    const sendButton = screen.getByRole('button', { name: /发送/i });

    expect(input).toBeDisabled();
    expect(sendButton).toHaveAttribute('aria-busy', 'true');
  });

  it('应该限制输入长度为2000字符', () => {
    renderComponent();

    const input = screen.getByPlaceholderText('输入评论内容...') as HTMLInputElement;
    expect(input).toHaveAttribute('maxLength', '2000');
  });
});
