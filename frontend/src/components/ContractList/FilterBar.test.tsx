import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import FilterBar, { FilterType } from './FilterBar';

describe('FilterBar', () => {
  it('应该渲染所有筛选按钮', () => {
    const mockOnFilterChange = vi.fn();
    render(<FilterBar activeFilter="all" onFilterChange={mockOnFilterChange} pendingCount={0} />);

    expect(screen.getByText('全部')).toBeInTheDocument();
    expect(screen.getByText('进行中')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
    expect(screen.getByText('待我处理')).toBeInTheDocument();
    expect(screen.getByText('抄送我')).toBeInTheDocument();
  });

  it('应该高亮显示当前激活的筛选按钮', () => {
    const mockOnFilterChange = vi.fn();
    const { container } = render(
      <FilterBar activeFilter="进行中" onFilterChange={mockOnFilterChange} pendingCount={0} />
    );

    const activeButton = screen.getByText('进行中').closest('button');
    expect(activeButton).toHaveClass('ant-btn-primary');
  });

  it('点击筛选按钮应该触发 onFilterChange 回调', () => {
    const mockOnFilterChange = vi.fn();
    render(<FilterBar activeFilter="all" onFilterChange={mockOnFilterChange} pendingCount={0} />);

    const button = screen.getByText('进行中');
    fireEvent.click(button);

    expect(mockOnFilterChange).toHaveBeenCalledWith('进行中');
  });

  it('当 pendingCount > 0 时应该在"待我处理"按钮上显示徽章', () => {
    const mockOnFilterChange = vi.fn();
    const { container } = render(
      <FilterBar activeFilter="all" onFilterChange={mockOnFilterChange} pendingCount={5} />
    );

    // 检查徽章是否存在
    const badge = container.querySelector('.ant-badge-count');
    expect(badge).toBeInTheDocument();
    expect(badge?.textContent).toBe('5');
  });

  it('当 pendingCount = 0 时不应该显示徽章', () => {
    const mockOnFilterChange = vi.fn();
    const { container } = render(
      <FilterBar activeFilter="all" onFilterChange={mockOnFilterChange} pendingCount={0} />
    );

    // 检查徽章不存在
    const badge = container.querySelector('.ant-badge-count');
    expect(badge).not.toBeInTheDocument();
  });

  it('应该支持所有筛选类型', () => {
    const mockOnFilterChange = vi.fn();
    const filters: FilterType[] = ['all', '进行中', '已完成', '待我处理', '抄送我'];

    filters.forEach((filter) => {
      mockOnFilterChange.mockClear();
      render(<FilterBar activeFilter="all" onFilterChange={mockOnFilterChange} pendingCount={0} />);

      const button = screen.getByText(filter === 'all' ? '全部' : filter);
      fireEvent.click(button);

      expect(mockOnFilterChange).toHaveBeenCalledWith(filter);
    });
  });
});
