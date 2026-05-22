import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import UploadButton from './UploadButton';
import * as useAttachmentsHook from '../../hooks/useAttachments';

// Mock Ant Design message
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    message: {
      error: vi.fn(),
      success: vi.fn(),
    },
  };
});

describe('UploadButton', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  const renderComponent = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <UploadButton contractId="test-contract-id" {...props} />
      </QueryClientProvider>
    );
  };

  it('应该渲染上传按钮', () => {
    renderComponent();
    expect(screen.getByText('上传附件')).toBeInTheDocument();
  });

  it('当 disabled 为 true 时应该禁用按钮', () => {
    renderComponent({ disabled: true });
    const button = screen.getByRole('button', { name: /上传附件/i });
    expect(button).toBeDisabled();
  });

  it('点击按钮应该触发文件选择', () => {
    renderComponent();
    const button = screen.getByRole('button', { name: /上传附件/i });

    // 获取隐藏的 file input
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const clickSpy = vi.spyOn(fileInput, 'click');

    fireEvent.click(button);
    expect(clickSpy).toHaveBeenCalled();
  });

  it('应该验证文件类型', async () => {
    const { message } = await import('antd');
    renderComponent();

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    // 创建一个不支持的文件类型
    const invalidFile = new File(['content'], 'test.txt', { type: 'text/plain' });

    Object.defineProperty(fileInput, 'files', {
      value: [invalidFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith(expect.stringContaining('不支持的文件类型'));
    });
  });

  it('应该验证文件大小', async () => {
    const { message } = await import('antd');
    renderComponent();

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    // 创建一个超过 20MB 的文件
    const largeFile = new File(['x'.repeat(21 * 1024 * 1024)], 'large.pdf', {
      type: 'application/pdf',
    });

    Object.defineProperty(fileInput, 'files', {
      value: [largeFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith(expect.stringContaining('文件大小不能超过 20MB'));
    });
  });

  it('应该成功上传有效文件', async () => {
    const { message } = await import('antd');

    // Mock useUploadAttachment hook
    const mockMutateAsync = vi.fn().mockResolvedValue({ id: 'attachment-id' });
    vi.spyOn(useAttachmentsHook, 'useUploadAttachment').mockReturnValue({
      mutateAsync: mockMutateAsync,
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      isSuccess: false,
      isIdle: true,
      data: undefined,
      error: null,
      reset: vi.fn(),
      status: 'idle',
      variables: undefined,
      context: undefined,
      failureCount: 0,
      failureReason: null,
      submittedAt: 0,
    } as any);

    renderComponent();

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    // 创建一个有效的 PDF 文件
    const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    Object.defineProperty(fileInput, 'files', {
      value: [validFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        contractId: 'test-contract-id',
        file: validFile,
      });
    });

    await waitFor(() => {
      expect(message.success).toHaveBeenCalledWith(expect.stringContaining('上传成功'));
    });
  });

  it('上传失败时应该显示错误消息', async () => {
    const { message } = await import('antd');

    // Mock useUploadAttachment hook with error
    const mockMutateAsync = vi.fn().mockRejectedValue(new Error('上传失败'));
    vi.spyOn(useAttachmentsHook, 'useUploadAttachment').mockReturnValue({
      mutateAsync: mockMutateAsync,
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      isSuccess: false,
      isIdle: true,
      data: undefined,
      error: null,
      reset: vi.fn(),
      status: 'idle',
      variables: undefined,
      context: undefined,
      failureCount: 0,
      failureReason: null,
      submittedAt: 0,
    } as any);

    renderComponent();

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    Object.defineProperty(fileInput, 'files', {
      value: [validFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith(expect.stringContaining('上传失败'));
    });
  });
});
