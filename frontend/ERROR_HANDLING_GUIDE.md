# 前端错误处理指南

## 概述

本文档描述了合同预审看板系统前端的完整错误处理策略,包括 HTTP 错误、WebSocket 错误、React 组件错误以及错误恢复机制。

## 错误处理层次

### 1. HTTP 错误处理 (Axios 拦截器)

**位置:** `src/utils/axios.ts`

#### 功能特性

- ✅ 自动重试机制 (最多 3 次)
- ✅ 指数退避策略
- ✅ 详细的错误日志
- ✅ 用户友好的错误提示
- ✅ 自动 Token 刷新和重定向

#### 错误分类

| 状态码 | 错误类型 | 处理策略 | 用户提示 |
|--------|---------|---------|---------|
| 401 | 未授权 | 清除 Token,跳转登录 | "登录已过期,即将跳转到登录页面" |
| 403 | 权限不足 | 显示错误通知 | "您没有权限执行此操作,请联系管理员" |
| 404 | 资源不存在 | 显示简短消息 | "请求的资源不存在" |
| 413 | 文件过大 | 显示详细通知 | "上传的文件超过大小限制(20MB)" |
| 429 | 请求过于频繁 | 显示警告通知 | "您的操作过于频繁,请稍后再试" |
| 500 | 服务器错误 | 自动重试,失败后显示通知 | "服务器遇到了问题,请稍后重试" |
| 502 | 网关错误 | 显示错误通知 | "服务正在维护或暂时不可用" |
| 503 | 服务不可用 | 显示警告通知 | "系统正在维护,请稍后再试" |
| 网络错误 | 无响应 | 自动重试,显示进度 | "网络连接失败,正在重试 (X/3)..." |

#### 重试逻辑

```typescript
// 可重试的错误类型
- 网络错误 (无响应)
- 5xx 服务器错误

// 重试配置
- 最大重试次数: 3
- 基础延迟: 1 秒
- 延迟策略: 指数退避 (1s, 2s, 4s)
```

#### 使用示例

```typescript
import axios from '@/utils/axios';

// 自动处理错误
try {
  const response = await axios.get('/api/contracts');
  // 处理成功响应
} catch (error) {
  // 错误已被拦截器处理,这里可以做额外处理
  console.error('Request failed:', error);
}
```

### 2. WebSocket 错误处理

**位置:** `src/config/socket.ts`

#### 功能特性

- ✅ 自动重连机制 (最多 5 次)
- ✅ 连接状态通知
- ✅ 重连进度提示
- ✅ 连接失败降级处理

#### 事件处理

| 事件 | 处理策略 | 用户提示 |
|------|---------|---------|
| connect | 显示成功消息 (仅重连时) | "实时通信已恢复" |
| connect_error | 显示警告通知 | "实时通信连接失败,部分功能可能受影响" |
| disconnect | 根据原因显示不同提示 | "实时通信已断开,正在尝试重新连接..." |
| reconnect_attempt | 更新重连进度通知 | "正在尝试重新连接 (X/5)..." |
| reconnect | 显示成功通知 | "重新连接成功,实时通信已恢复" |
| reconnect_failed | 显示错误通知,提供刷新按钮 | "无法连接到实时通信服务,请刷新页面重试" |

#### 重连配置

```typescript
reconnection: true,           // 启用自动重连
reconnectionAttempts: 5,      // 最多重连 5 次
reconnectionDelay: 1000,      // 重连延迟 1 秒
reconnectionDelayMax: 5000,   // 最大重连延迟 5 秒
timeout: 20000,               // 连接超时 20 秒
```

#### 使用示例

```typescript
import { useSocketIntegration } from '@/hooks/useSocket';

function MyComponent() {
  const { isConnected } = useSocketIntegration(contractId);
  
  return (
    <div>
      {!isConnected && <Alert message="实时通信未连接" type="warning" />}
      {/* 组件内容 */}
    </div>
  );
}
```

### 3. React 组件错误处理 (ErrorBoundary)

**位置:** `src/components/ErrorBoundary/ErrorBoundary.tsx`

#### 功能特性

- ✅ 捕获组件渲染错误
- ✅ 错误频率检测
- ✅ 自动恢复尝试
- ✅ 详细的错误日志
- ✅ 开发环境显示错误堆栈

#### 错误频率检测

```typescript
// 配置
最大错误频率: 3 次
错误窗口: 10 秒

// 行为
- 10 秒内错误少于 3 次: 允许重试
- 10 秒内错误达到 3 次: 禁用重试,建议刷新页面
```

#### 使用示例

```typescript
import ErrorBoundary from '@/components/ErrorBoundary';

// 基础用法
<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>

// 自定义错误处理
<ErrorBoundary
  onError={(error, errorInfo) => {
    // 上报到监控系统
    reportError(error, errorInfo);
  }}
  onReset={() => {
    // 重置应用状态
    resetAppState();
  }}
>
  <YourComponent />
</ErrorBoundary>

// 自定义降级 UI
<ErrorBoundary fallback={<CustomErrorUI />}>
  <YourComponent />
</ErrorBoundary>
```

## 错误恢复工具

**位置:** `src/utils/errorRecovery.ts`

### 1. 重试机制 (retryWithBackoff)

自动重试失败的异步操作,使用指数退避策略。

```typescript
import { retryWithBackoff } from '@/utils/errorRecovery';

// 重试 API 调用
const data = await retryWithBackoff(
  async () => {
    const response = await fetch('/api/data');
    return response.json();
  },
  3,    // 最多重试 3 次
  1000  // 基础延迟 1 秒
);
```

### 2. 超时控制 (withTimeout)

为异步操作添加超时限制。

```typescript
import { withTimeout } from '@/utils/errorRecovery';

// 5 秒超时
const data = await withTimeout(
  async () => {
    return await fetchData();
  },
  5000
);
```

### 3. 熔断器 (CircuitBreaker)

防止级联故障,在重复失败后停止请求。

```typescript
import { CircuitBreaker } from '@/utils/errorRecovery';

const breaker = new CircuitBreaker(
  5,      // 失败阈值: 5 次
  60000   // 重置超时: 1 分钟
);

// 使用熔断器保护
try {
  const result = await breaker.execute(async () => {
    return await riskyOperation();
  });
} catch (error) {
  if (error.message.includes('Circuit breaker is open')) {
    // 熔断器已打开,服务不可用
    showServiceUnavailableMessage();
  }
}
```

### 4. 错误通知防抖 (ErrorNotificationDebouncer)

防止相同错误的通知重复显示。

```typescript
import { errorDebouncer } from '@/utils/errorRecovery';

function handleError(error: Error) {
  const errorKey = error.message;
  
  // 只在 5 秒内首次出现时显示通知
  if (errorDebouncer.shouldNotify(errorKey)) {
    notification.error({
      message: '操作失败',
      description: error.message,
    });
  }
}
```

### 5. 安全的 localStorage 操作

防止 localStorage 操作失败导致应用崩溃。

```typescript
import { safeLocalStorage } from '@/utils/errorRecovery';

// 安全的读取
const token = safeLocalStorage.getItem('token', null);

// 安全的写入
const success = safeLocalStorage.setItem('token', 'abc123');
if (!success) {
  console.warn('Failed to save token');
}
```

### 6. 错误严重性分类

根据错误类型自动分类严重性。

```typescript
import { classifyErrorSeverity, ErrorSeverity } from '@/utils/errorRecovery';

const severity = classifyErrorSeverity(error);

switch (severity) {
  case ErrorSeverity.CRITICAL:
    // 立即通知用户,可能需要刷新页面
    break;
  case ErrorSeverity.HIGH:
    // 显示错误通知
    break;
  case ErrorSeverity.MEDIUM:
    // 显示警告消息
    break;
  case ErrorSeverity.LOW:
    // 记录日志,可选显示提示
    break;
}
```

## 最佳实践

### 1. 分层错误处理

```typescript
// ❌ 不好的做法 - 在每个组件中处理错误
function MyComponent() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    fetch('/api/data')
      .then(res => res.json())
      .then(setData)
      .catch(error => {
        // 每个组件都要写错误处理
        message.error('加载失败');
      });
  }, []);
}

// ✅ 好的做法 - 使用统一的错误处理
function MyComponent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['data'],
    queryFn: async () => {
      const response = await axios.get('/api/data');
      return response.data;
    },
  });
  
  // 错误已被 axios 拦截器处理
  if (error) {
    return <ErrorState />;
  }
}
```

### 2. 错误边界保护关键组件

```typescript
// ✅ 为关键功能添加错误边界
function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ErrorBoundary>
          <ContractList />
        </ErrorBoundary>
        
        <ErrorBoundary>
          <ContractDetail />
        </ErrorBoundary>
        
        <ErrorBoundary>
          <AIAdvisor />
        </ErrorBoundary>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
```

### 3. 提供用户友好的错误信息

```typescript
// ❌ 不好的做法 - 技术性错误信息
message.error('TypeError: Cannot read property "id" of undefined');

// ✅ 好的做法 - 用户友好的错误信息
notification.error({
  message: '加载合同失败',
  description: '无法加载合同详情,请刷新页面重试',
  duration: 4,
});
```

### 4. 记录错误日志

```typescript
// ✅ 在开发环境记录详细日志
if (import.meta.env.DEV) {
  console.group('[Error] API Request Failed');
  console.error('Error:', error);
  console.error('URL:', url);
  console.error('Method:', method);
  console.error('Response:', response);
  console.groupEnd();
}
```

### 5. 错误恢复策略

```typescript
// ✅ 提供多种恢复选项
<Result
  status="error"
  title="加载失败"
  subTitle="无法加载数据,请选择以下操作"
  extra={[
    <Button type="primary" onClick={handleRetry}>
      重试
    </Button>,
    <Button onClick={handleRefresh}>
      刷新页面
    </Button>,
    <Button onClick={handleGoBack}>
      返回上一页
    </Button>,
  ]}
/>
```

## 错误监控集成

### 预留的监控系统集成点

```typescript
// ErrorBoundary 组件
componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
  // TODO: 上报到监控系统
  // reportErrorToMonitoring(error, errorInfo, {
  //   errorCount: this.state.errorCount + 1,
  //   isHighFrequency,
  // });
}

// Axios 拦截器
const logError = (error: AxiosError, context: string): void => {
  // TODO: 上报到监控系统
  // reportErrorToMonitoring({
  //   type: 'http_error',
  //   context,
  //   error,
  //   url: error.config?.url,
  //   method: error.config?.method,
  //   status: error.response?.status,
  // });
};
```

### 推荐的监控工具

1. **Sentry** - 错误追踪和性能监控
2. **LogRocket** - 会话重放和错误追踪
3. **Datadog** - 全栈监控
4. **自定义监控服务** - 根据需求定制

## 测试错误处理

### 1. 测试 HTTP 错误

```typescript
// 模拟网络错误
jest.mock('@/utils/axios');
axios.get.mockRejectedValue(new Error('Network error'));

// 测试组件如何处理错误
test('handles network error', async () => {
  render(<MyComponent />);
  
  await waitFor(() => {
    expect(screen.getByText('网络连接失败')).toBeInTheDocument();
  });
});
```

### 2. 测试 ErrorBoundary

```typescript
test('catches component errors', () => {
  const ThrowError = () => {
    throw new Error('Test error');
  };
  
  render(
    <ErrorBoundary>
      <ThrowError />
    </ErrorBoundary>
  );
  
  expect(screen.getByText('组件加载失败')).toBeInTheDocument();
});
```

### 3. 测试错误恢复

```typescript
test('retries failed requests', async () => {
  let attempts = 0;
  const mockFn = jest.fn(async () => {
    attempts++;
    if (attempts < 3) {
      throw new Error('Temporary error');
    }
    return 'success';
  });
  
  const result = await retryWithBackoff(mockFn, 3, 100);
  
  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```

## 总结

本系统实现了完整的多层错误处理机制:

1. **HTTP 层**: Axios 拦截器自动处理网络错误,支持重试和详细的错误提示
2. **WebSocket 层**: 自动重连机制,连接状态通知
3. **组件层**: ErrorBoundary 捕获渲染错误,防止应用崩溃
4. **工具层**: 提供错误恢复工具,如重试、超时、熔断器等

所有错误处理都遵循以下原则:
- ✅ 用户友好的错误信息
- ✅ 自动恢复机制
- ✅ 详细的错误日志
- ✅ 优雅的降级处理
- ✅ 预留监控系统集成点

## 相关文档

- [Axios 配置文档](./src/utils/README.md)
- [ErrorBoundary 使用文档](./src/components/ErrorBoundary/README.md)
- [Socket.IO 配置文档](./src/config/SOCKET_README.md)
- [React Query 错误处理](./src/hooks/README.md)
