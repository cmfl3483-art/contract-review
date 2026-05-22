/**
 * SearchBox 组件测试
 *
 * 测试搜索框的防抖功能、清除功能和输入交互
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import SearchBox from './SearchBox';

describe('SearchBox', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('应该渲染搜索输入框', () => {
    const mockOnSearch = vi.fn();
    render(<SearchBox onSearch={mockOnSearch} />);

    const input = screen.getByPlaceholderText('搜索合同名称或发起人');
    expect(input).toBeInTheDocument();
  });

  it('应该使用自定义占位符文本', () => {
    const mockOnSearch = vi.fn();
    render(<SearchBox onSearch={mockOnSearch} placeholder="自定义搜索" />);

    const input = screen.getByPlaceholderText('自定义搜索');
    expect(input).toBeInTheDocument();
  });

  it('应该在输入时更新值', () => {
    const mockOnSearch = vi.fn();
    render(<SearchBox onSearch={mockOnSearch} />);

    const input = screen.getByPlaceholderText('搜索合同名称或发起人') as HTMLInputElement;
    fireEvent.change(input, { target: { value: '测试合同' } });

    expect(input.value).toBe('测试合同');
  });

  it('应该在输入后300ms触发搜索（防抖）', async () => {
    const mockOnSearch = vi.fn();
    render(<SearchBox onSearch={mockOnSearch} />);

    const input = screen.getByPlaceholderText('搜索合同名称或发起人');

    // 输入文本
    fireEvent.change(input, { target: { value: '测试' } });

    // 立即检查，不应该调用
    expect(mockOnSearch).not.toHaveBeenCalled();

    // 快进300ms
    vi.advanceTimersByTime(300);

    // 现在应该调用了
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('测试');
      expect(mockOnSearch).toHaveBeenCalledTimes(1);
    });
  });

  it('应该在快速输入时只触发一次搜索（防抖）', async () => {
    const mockOnSearch = vi.fn();
    render(<SearchBox onSearch={mockOnSearch} />);

    const input = screen.getByPlaceholderText('搜索合同名称或发起人');

    // 快速输入多次
    fireEvent.change(input, { target: { value: '测' } });
    vi.advanceTimersByTime(100);

    fireEvent.change(input, { target: { value: '测试' } });
    vi.advanceTimersByTime(100);

    fireEvent.change(input, { target: { value: '测试合同' } });
    vi.advanceTimersByTime(100);

    // 此时还没有调用
    expect(mockOnSearch).not.toHaveBeenCalled();

    // 再等待100ms，总共300ms
    vi.advanceTimersByTime(100);

    // 应该只调用一次，使用最后的值
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('测试合同');
      expect(mockOnSearch).toHaveBeenCalledTimes(1);
    });
  });

  it('应该在点击清除按钮时清空输入并立即触发搜索', async () => {
    const mockOnSearch = vi.fn();
    render(<SearchBox onSearch={mockOnSearch} />);

    const input = screen.getByPlaceholderText('搜索合同名称或发起人') as HTMLInputElement;

    // 输入文本
    fireEvent.change(input, { target: { value: '测试合同' } });
    vi.advanceTimersByTime(300);

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('测试合同');
    });

    mockOnSearch.mockClear();

    // 点击清除按钮
    const clearButton = input.parentElement?.querySelector('.ant-input-clear-icon');
    if (clearButton) {
      fireEvent.click(clearButton);
    }

    // 应该立即清空并触发搜索
    expect(input.value).toBe('');
    expect(mockOnSearch).toHaveBeenCalledWith('');
    expect(mockOnSearch).toHaveBeenCalledTimes(1);
  });

  it('应该显示搜索图标', () => {
    const mockOnSearch = vi.fn();
    render(<SearchBox onSearch={mockOnSearch} />);

    const searchIcon = document.querySelector('.anticon-search');
    expect(searchIcon).toBeInTheDocument();
  });

  it('应该在有值时显示清除按钮', () => {
    const mockOnSearch = vi.fn();
    render(<SearchBox onSearch={mockOnSearch} />);

    const input = screen.getByPlaceholderText('搜索合同名称或发起人');

    // 输入文本
    fireEvent.change(input, { target: { value: '测试' } });

    // 清除按钮应该可见
    const clearButton = input.parentElement?.querySelector('.ant-input-clear-icon');
    expect(clearButton).toBeInTheDocument();
  });
});
