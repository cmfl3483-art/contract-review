# ErrorBoundary 组件

## 概述

`ErrorBoundary` 是一个 React 错误边界组件,用于捕获子组件树中的 JavaScript 错误,记录错误信息并显示降级 UI,防止整个应用崩溃。

## 功能特性

- ✅ 捕获子组件树中的渲染错误
- ✅ 显示用户友好的错误提示界面
- ✅ 提供刷新页面和重试功能
- ✅ 开发环境显示详细错误堆栈
- ✅ 支持自定义错误处理回调
- ✅ 支持自定义降级 UI
- ✅ 预留监控系统集成接口

## 使用方法

### 基础用法

将需要保护的组件包裹在 `ErrorBoundary` 中:

```tsx
import ErrorBoundary from '@/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <YourComponent />
    </ErrorBoundary>
  );
}
```

### 自定义错误处理

通过 `onError` 回调处理错误(例如上报到监控系统):

```tsx
import ErrorBoundary from '@/components/ErrorBoundary';

function App() {
  const handleError = (error: Error, errorInfo: ErrorInfo) => {
    // 上报到监控系统
    console.error('Error caught:', error);
    // Sentry.captureException(error, { extra: errorInfo });
  };

  return (
    <ErrorBoundary onError={handleError}>
      <YourComponent />
    </ErrorBoundary>
  );
}
```

### 自定义降级 UI

通过 `fallback` 属性自定义错误显示界面:

```tsx
import ErrorBoundary from '@/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary 
      fallback={
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <h2>出错了!</h2>
          <p>请刷新页面重试</p>
        </div>
      }
    >
      <YourComponent />
    </ErrorBoundary>
  );
}
```

### 嵌套使用

可以在不同层级使用多个 ErrorBoundary,实现更细粒度的错误隔离:

```tsx
import ErrorBoundary from '@/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <Header />
      <ErrorBoundary>
        <MainContent />
      </ErrorBoundary>
      <ErrorBoundary>
        <Sidebar />
      </ErrorBoundary>
      <Footer />
    </ErrorBoundary>
  );
}
```

## Props

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `children` | `ReactNode` | 是 | - | 需要保护的子组件 |
| `fallback` | `ReactNode` | 否 | - | 自定义降级 UI,不提供则使用默认 UI |
| `onError` | `(error: Error, errorInfo: ErrorInfo) => void` | 否 | - | 错误处理回调函数 |

## 默认降级 UI

默认降级 UI 包含:

- 错误状态图标
- 友好的错误提示文案
- "刷新页面" 按钮 - 重新加载整个页面
- "重试" 按钮 - 重置错误状态,尝试重新渲染
- 开发环境下的详细错误信息(可展开查看)

## 注意事项

### ErrorBoundary 无法捕获的错误

根据 React 官方文档,ErrorBoundary **无法**捕获以下类型的错误:

1. **事件处理器中的错误** - 使用 try-catch 处理
2. **异步代码中的错误** - 使用 try-catch 或 Promise.catch() 处理
3. **服务端渲染的错误**
4. **ErrorBoundary 自身抛出的错误**

示例:

```tsx
// ❌ ErrorBoundary 无法捕获
function MyComponent() {
  const handleClick = () => {
    throw new Error('事件处理器错误'); // 不会被捕获
  };

  return <button onClick={handleClick}>点击</button>;
}

// ✅ 正确处理方式
function MyComponent() {
  const handleClick = () => {
    try {
      throw new Error('事件处理器错误');
    } catch (error) {
      console.error('捕获到错误:', error);
    }
  };

  return <button onClick={handleClick}>点击</button>;
}
```

### 生产环境建议

在生产环境中,建议:

1. 集成错误监控服务(如 Sentry、LogRocket)
2. 不要向用户显示详细的错误堆栈信息
3. 提供明确的恢复操作指引
4. 记录足够的上下文信息用于问题排查

## 集成监控系统

### Sentry 集成示例

```tsx
import * as Sentry from '@sentry/react';
import ErrorBoundary from '@/components/ErrorBoundary';

function App() {
  const handleError = (error: Error, errorInfo: ErrorInfo) => {
    Sentry.captureException(error, {
      contexts: {
        react: {
          componentStack: errorInfo.componentStack,
        },
      },
    });
  };

  return (
    <ErrorBoundary onError={handleError}>
      <YourComponent />
    </ErrorBoundary>
  );
}
```

### 自定义监控服务集成

```tsx
import ErrorBoundary from '@/components/ErrorBoundary';
import { reportError } from '@/services/monitoring';

function App() {
  const handleError = (error: Error, errorInfo: ErrorInfo) => {
    reportError({
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    });
  };

  return (
    <ErrorBoundary onError={handleError}>
      <YourComponent />
    </ErrorBoundary>
  );
}
```

## 测试

### 测试错误捕获

创建一个会抛出错误的测试组件:

```tsx
function BuggyComponent() {
  throw new Error('测试错误');
  return <div>不会渲染</div>;
}

// 在开发环境中测试
function TestPage() {
  return (
    <ErrorBoundary>
      <BuggyComponent />
    </ErrorBoundary>
  );
}
```

### 单元测试示例

```tsx
import { render, screen } from '@testing-library/react';
import ErrorBoundary from './ErrorBoundary';

function ThrowError() {
  throw new Error('测试错误');
}

describe('ErrorBoundary', () => {
  it('应该捕获错误并显示降级 UI', () => {
    // 抑制控制台错误输出
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText('组件加载失败')).toBeInTheDocument();
    expect(screen.getByText('刷新页面')).toBeInTheDocument();

    spy.mockRestore();
  });

  it('应该调用 onError 回调', () => {
    const onError = jest.fn();
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary onError={onError}>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(onError).toHaveBeenCalled();
    spy.mockRestore();
  });
});
```

## 相关资源

- [React 官方文档 - Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
- [Ant Design - Result 组件](https://ant.design/components/result-cn)
- [Sentry React SDK](https://docs.sentry.io/platforms/javascript/guides/react/)

## 更新日志

### v1.0.0 (2025-01-XX)

- ✨ 初始版本
- ✅ 实现基础错误捕获功能
- ✅ 实现默认降级 UI
- ✅ 支持自定义错误处理和降级 UI
- ✅ 开发环境显示详细错误信息
