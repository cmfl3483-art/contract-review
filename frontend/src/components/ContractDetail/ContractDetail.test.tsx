import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ContractDetail from './ContractDetail';
import * as stores from '../../stores';
import * as hooks from '../../hooks';

// Mock the stores and hooks
vi.mock('../../stores', () => ({
  useSelectedContractStore: vi.fn(),
}));

vi.mock('../../hooks', () => ({
  useContractDetail: vi.fn(),
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('ContractDetail', () => {
  it('应该显示空状态当没有选中合同时', () => {
    vi.mocked(stores.useSelectedContractStore).mockReturnValue({
      selectedContractId: null,
      setSelectedContractId: vi.fn(),
      clearSelection: vi.fn(),
    });

    render(<ContractDetail />, { wrapper });

    expect(screen.getByText('请选择一个合同查看详情')).toBeInTheDocument();
  });

  it('应该显示加载状态', () => {
    vi.mocked(stores.useSelectedContractStore).mockReturnValue({
      selectedContractId: 'contract-1',
      setSelectedContractId: vi.fn(),
      clearSelection: vi.fn(),
    });

    vi.mocked(hooks.useContractDetail).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      isError: false,
      isSuccess: false,
      refetch: vi.fn(),
    } as any);

    render(<ContractDetail />, { wrapper });

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('应该显示合同详情', () => {
    vi.mocked(stores.useSelectedContractStore).mockReturnValue({
      selectedContractId: 'contract-1',
      setSelectedContractId: vi.fn(),
      clearSelection: vi.fn(),
    });

    const mockData = {
      contract: {
        id: 'contract-1',
        name: '测试合同',
        description: '这是一个测试合同',
        status: 'progress' as const,
        initiatorId: 'user-1',
        ccUsers: [],
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-01T00:00:00Z',
      },
      reviewers: [
        {
          id: 'reviewer-1',
          name: '张三',
          role: '法务',
          status: 'approved' as const,
          avatar: undefined,
        },
        {
          id: 'reviewer-2',
          name: '李四',
          role: '财务',
          status: 'pending' as const,
          avatar: undefined,
        },
      ],
      attachments: [],
    };

    vi.mocked(hooks.useContractDetail).mockReturnValue({
      data: mockData,
      isLoading: false,
      error: null,
      isError: false,
      isSuccess: true,
      refetch: vi.fn(),
    } as any);

    render(<ContractDetail />, { wrapper });

    // 验证合同标题和描述
    expect(screen.getByText('测试合同')).toBeInTheDocument();
    expect(screen.getByText('这是一个测试合同')).toBeInTheDocument();

    // 验证评审人统计
    expect(screen.getByText(/评审人 \(1\/2\)/)).toBeInTheDocument();

    // 验证已审核评审人
    expect(screen.getByText('张三')).toBeInTheDocument();
    expect(screen.getByText('已通过')).toBeInTheDocument();

    // 验证待审核评审人
    expect(screen.getByText('李四')).toBeInTheDocument();
    expect(screen.getByText('待处理')).toBeInTheDocument();

    // 验证附件部分
    expect(screen.getByText('附件')).toBeInTheDocument();
    expect(screen.getByText('暂无附件')).toBeInTheDocument();
  });

  it('应该显示附件列表', () => {
    vi.mocked(stores.useSelectedContractStore).mockReturnValue({
      selectedContractId: 'contract-1',
      setSelectedContractId: vi.fn(),
      clearSelection: vi.fn(),
    });

    const mockData = {
      contract: {
        id: 'contract-1',
        name: '测试合同',
        status: 'progress' as const,
        initiatorId: 'user-1',
        ccUsers: [],
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-01T00:00:00Z',
      },
      reviewers: [],
      attachments: [
        {
          fileName: '合同文件.pdf',
          versionCount: 2,
          versions: [],
        },
        {
          fileName: '附件.docx',
          versionCount: 1,
          versions: [],
        },
      ],
    };

    vi.mocked(hooks.useContractDetail).mockReturnValue({
      data: mockData,
      isLoading: false,
      error: null,
      isError: false,
      isSuccess: true,
      refetch: vi.fn(),
    } as any);

    render(<ContractDetail />, { wrapper });

    // 验证附件显示
    expect(screen.getByText('合同文件.pdf')).toBeInTheDocument();
    expect(screen.getByText('2 个版本')).toBeInTheDocument();
    expect(screen.getByText('附件.docx')).toBeInTheDocument();
    expect(screen.getByText('1 个版本')).toBeInTheDocument();
  });

  it('应该显示错误状态', () => {
    vi.mocked(stores.useSelectedContractStore).mockReturnValue({
      selectedContractId: 'contract-1',
      setSelectedContractId: vi.fn(),
      clearSelection: vi.fn(),
    });

    vi.mocked(hooks.useContractDetail).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('加载失败'),
      isError: true,
      isSuccess: false,
      refetch: vi.fn(),
    } as any);

    render(<ContractDetail />, { wrapper });

    expect(screen.getByText('加载失败')).toBeInTheDocument();
  });
});
