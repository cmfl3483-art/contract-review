import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ContractList from './ContractList';
import * as contractHooks from '../../hooks/useContracts';
import type { ContractListResponse } from '../../types';

// Mock the hooks
vi.mock('../../hooks/useContracts');

// Mock data
const mockContracts: ContractListResponse = {
  contracts: [
    {
      id: '1',
      name: '测试合同A',
      description: '测试描述A',
      status: 'progress',
      initiatorId: 'user1',
      initiator: {
        id: 'user1',
        dingtalkUserId: 'dt1',
        name: '张三',
        role: '销售',
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-01T00:00:00Z',
      },
      ccUsers: [],
      hasPendingReview: true,
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    {
      id: '2',
      name: '测试合同B',
      description: '测试描述B',
      status: 'completed',
      initiatorId: 'user2',
      initiator: {
        id: 'user2',
        dingtalkUserId: 'dt2',
        name: '李四',
        role: '法务',
        createdAt: '2025-01-02T00:00:00Z',
        updatedAt: '2025-01-02T00:00:00Z',
      },
      ccUsers: [],
      hasPendingReview: false,
      createdAt: '2025-01-02T00:00:00Z',
      updatedAt: '2025-01-02T00:00:00Z',
    },
  ],
  total: 2,
  pendingCount: 1,
};

describe('ContractList', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    // Reset all mocks
    vi.clearAllMocks();
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);
  };

  it('应该显示加载状态', () => {
    // Mock loading state
    vi.mocked(contractHooks.useContractList).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
    } as any);

    vi.mocked(contractHooks.usePendingCount).mockReturnValue({
      data: 0,
    } as any);

    renderWithProviders(<ContractList />);

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('应该显示错误状态', () => {
    // Mock error state
    vi.mocked(contractHooks.useContractList).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('加载失败'),
    } as any);

    vi.mocked(contractHooks.usePendingCount).mockReturnValue({
      data: 0,
    } as any);

    renderWithProviders(<ContractList />);

    expect(screen.getByText('加载失败')).toBeInTheDocument();
  });

  it('应该显示空状态', async () => {
    // Mock empty data
    vi.mocked(contractHooks.useContractList).mockReturnValue({
      data: { contracts: [], total: 0, pendingCount: 0 },
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.mocked(contractHooks.usePendingCount).mockReturnValue({
      data: 0,
    } as any);

    renderWithProviders(<ContractList />);

    await waitFor(() => {
      expect(screen.getByText('暂无合同')).toBeInTheDocument();
    });
  });

  it('应该显示合同列表', async () => {
    // Mock successful data
    vi.mocked(contractHooks.useContractList).mockReturnValue({
      data: mockContracts,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.mocked(contractHooks.usePendingCount).mockReturnValue({
      data: 1,
    } as any);

    renderWithProviders(<ContractList />);

    await waitFor(() => {
      expect(screen.getByText('测试合同A')).toBeInTheDocument();
      expect(screen.getByText('测试合同B')).toBeInTheDocument();
      expect(screen.getByText('张三')).toBeInTheDocument();
      expect(screen.getByText('李四')).toBeInTheDocument();
    });
  });

  it('应该显示待处理徽章', async () => {
    // Mock successful data with pending count
    vi.mocked(contractHooks.useContractList).mockReturnValue({
      data: mockContracts,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.mocked(contractHooks.usePendingCount).mockReturnValue({
      data: 1,
    } as any);

    renderWithProviders(<ContractList />);

    await waitFor(() => {
      // The badge should show the pending count
      const badge = screen.getByText('1');
      expect(badge).toBeInTheDocument();
    });
  });

  it('应该支持筛选切换', async () => {
    // Mock successful data
    vi.mocked(contractHooks.useContractList).mockReturnValue({
      data: mockContracts,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.mocked(contractHooks.usePendingCount).mockReturnValue({
      data: 1,
    } as any);

    renderWithProviders(<ContractList />);

    await waitFor(() => {
      expect(screen.getByText('测试合同A')).toBeInTheDocument();
    });

    // Click on "进行中" filter
    const progressButton = screen.getByText('进行中');
    fireEvent.click(progressButton);

    // The filter should be active (button should have primary type)
    expect(progressButton.closest('button')).toHaveClass('ant-btn-primary');
  });

  it('应该支持搜索', async () => {
    // Mock successful data
    vi.mocked(contractHooks.useContractList).mockReturnValue({
      data: mockContracts,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.mocked(contractHooks.usePendingCount).mockReturnValue({
      data: 1,
    } as any);

    renderWithProviders(<ContractList />);

    await waitFor(() => {
      expect(screen.getByText('测试合同A')).toBeInTheDocument();
    });

    // Type in search box
    const searchInput = screen.getByPlaceholderText('搜索合同名称或发起人');
    fireEvent.change(searchInput, { target: { value: '张三' } });

    // The search input should have the value
    expect(searchInput).toHaveValue('张三');
  });

  it('应该支持合同选择', async () => {
    const onContractSelect = vi.fn();

    // Mock successful data
    vi.mocked(contractHooks.useContractList).mockReturnValue({
      data: mockContracts,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.mocked(contractHooks.usePendingCount).mockReturnValue({
      data: 1,
    } as any);

    renderWithProviders(<ContractList onContractSelect={onContractSelect} />);

    await waitFor(() => {
      expect(screen.getByText('测试合同A')).toBeInTheDocument();
    });

    // Click on a contract card
    const contractCard = screen.getByText('测试合同A').closest('.contract-card');
    if (contractCard) {
      fireEvent.click(contractCard);
    }

    // The callback should be called
    expect(onContractSelect).toHaveBeenCalledWith('1');
  });

  it('应该显示同意按钮（当有待处理项时）', async () => {
    // Mock successful data
    vi.mocked(contractHooks.useContractList).mockReturnValue({
      data: mockContracts,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.mocked(contractHooks.usePendingCount).mockReturnValue({
      data: 1,
    } as any);

    renderWithProviders(<ContractList />);

    await waitFor(() => {
      expect(screen.getByText('测试合同A')).toBeInTheDocument();
    });

    // The first contract has pending review, so it should show approve button
    const approveButtons = screen.getAllByText('同意');
    expect(approveButtons).toHaveLength(1);
  });

  it('应该显示发起合同预审按钮', async () => {
    // Mock successful data
    vi.mocked(contractHooks.useContractList).mockReturnValue({
      data: mockContracts,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.mocked(contractHooks.usePendingCount).mockReturnValue({
      data: 1,
    } as any);

    renderWithProviders(<ContractList />);

    await waitFor(() => {
      expect(screen.getByText('发起合同预审')).toBeInTheDocument();
    });
  });
});
