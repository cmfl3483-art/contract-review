/**
 * ErrorBoundary 组件测试
 *
 * 注意: 这是一个基础测试文件模板
 * 实际测试需要配置测试环境 (Jest + React Testing Library)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ErrorBoundary from './ErrorBoundary';

// 创建一个会抛出错误的测试组件
function ThrowError() {
  throw new Error('测试错误');
}

// 创建一个正常的测试组件
function NormalComponent() {
  return <div>正常组件</div>;
}

describe('ErrorBoundary', () => {
  // 抑制控制台错误输出
  const originalError = console.error;
  beforeAll(() => {
    console.error = vi.fn();
  });

  afterAll(() => {
    console.error = originalError;
  });

  it('应该正常渲染子组件', () => {
    render(
      <ErrorBoundary>
        <NormalComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText('正常组件')).toBeInTheDocument();
  });

  it('应该捕获错误并显示降级 UI', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText('组件加载失败')).toBeInTheDocument();
    expect(screen.getByText('刷新页面')).toBeInTheDocument();
    expect(screen.getByText('重试')).toBeInTheDocument();
  });

  it('应该调用 onError 回调', () => {
    const onError = vi.fn();

    render(
      <ErrorBoundary onError={onError}>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(onError).toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String),
      })
    );
  });

  it('应该显示自定义降级 UI', () => {
    const fallback = <div>自定义错误提示</div>;

    render(
      <ErrorBoundary fallback={fallback}>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText('自定义错误提示')).toBeInTheDocument();
    expect(screen.queryByText('组件加载失败')).not.toBeInTheDocument();
  });
});
