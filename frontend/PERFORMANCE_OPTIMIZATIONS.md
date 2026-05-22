# 前端性能优化实施文档

## 概述

本文档记录了合同预审看板系统前端的性能优化实施情况。根据设计文档的要求,我们实施了以下优化策略:

1. React.memo 优化组件重渲染
2. 防抖/节流优化事件处理
3. 代码分割 (Code Splitting)
4. 资源加载优化

## 1. React.memo 优化

### 实施的组件

我们对以下组件应用了 `React.memo` 来避免不必要的重渲染:

#### 合同列表组件
- **ContractCard** (`src/components/ContractList/ContractCard.tsx`)
  - 优化原因: 列表中可能有大量合同卡片,避免父组件更新时所有卡片重渲染
  - 优化效果: 只有当 contract、selected、onSelect 或 onApprove props 变化时才重渲染

- **SearchBox** (`src/components/ContractList/SearchBox.tsx`)
  - 优化原因: 搜索框不需要随其他组件更新而重渲染
  - 优化效果: 只有当 onSearch 或 placeholder props 变化时才重渲染

#### 时间线组件
- **ReviewCard** (`src/components/Timeline/ReviewCard.tsx`)
  - 优化原因: 时间线中可能有多条评审记录,避免不必要的重渲染
  - 优化效果: 只有当 review、currentUserId 或 onLike props 变化时才重渲染

- **AISummaryCard** (`src/components/Timeline/AISummaryCard.tsx`)
  - 优化原因: AI总结卡片内容较复杂,避免频繁重渲染
  - 优化效果: 只有当 summary prop 变化时才重渲染

- **ReplyList** (`src/components/Timeline/ReplyList.tsx`)
  - 优化原因: 回复列表可能包含多条回复,避免不必要的重渲染
  - 优化效果: 只有当 replies、onLike 或 currentUserId props 变化时才重渲染

#### AI顾问组件
- **Message** (`src/components/AIAdvisor/Message.tsx`)
  - 优化原因: 聊天消息列表可能很长,避免所有消息重渲染
  - 优化效果: 只有当 message 或 currentUserName props 变化时才重渲染

- **ChatInput** (`src/components/AIAdvisor/ChatInput.tsx`)
  - 优化原因: 输入框不需要随消息列表更新而重渲染
  - 优化效果: 只有当 onSend、loading 或 placeholder props 变化时才重渲染

### 使用示例

```tsx
import { memo } from 'react';

const MyComponent = memo(({ data }) => {
  return <div>{data}</div>;
});

MyComponent.displayName = 'MyComponent';
```

### 注意事项

- 所有使用 `memo` 的组件都设置了 `displayName` 属性,便于 React DevTools 调试
- `memo` 使用浅比较来判断 props 是否变化,对于复杂对象需要确保引用稳定性
- 回调函数 props 应该使用 `useCallback` 包装以保持引用稳定

## 2. 防抖/节流优化

### 防抖 (Debounce)

**SearchBox 组件** 已实现搜索输入防抖:
- 位置: `src/components/ContractList/SearchBox.tsx`
- 延迟: 300ms
- 实现方式: 使用 `setTimeout` 和 `clearTimeout`
- 效果: 用户停止输入 300ms 后才触发搜索,减少不必要的 API 请求

```tsx
const debouncedSearch = useCallback(
  (keyword: string) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = window.setTimeout(() => {
      onSearch(keyword);
    }, 300);
  },
  [onSearch]
);
```

### 节流 (Throttle)

**useThrottle Hook** 已创建用于节流事件处理:
- 位置: `src/hooks/useThrottle.ts`
- 用途: 限制滚动、窗口调整等高频事件的处理频率
- 使用示例:

```tsx
import { useThrottle } from '@/hooks';

const MyComponent = () => {
  const handleScroll = useThrottle(() => {
    console.log('Scrolling...');
  }, 200);

  return <div onScroll={handleScroll}>...</div>;
};
```

### 适用场景

- **防抖**: 搜索输入、表单验证、窗口调整
- **节流**: 滚动事件、鼠标移动、窗口调整

## 3. 代码分割 (Code Splitting)

### 路由级别代码分割

**App.tsx** 已实现路由级别的代码分割:
- 使用 `React.lazy` 动态导入页面组件
- 使用 `Suspense` 提供加载状态
- 效果: 首次加载只加载必要的代码,其他页面按需加载

```tsx
import { lazy, Suspense } from 'react';

const ContractBoard = lazy(() => import('./pages/ContractBoard'));

function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<ContractBoard />} />
      </Routes>
    </Suspense>
  );
}
```

### Vite 构建优化

**vite.config.ts** 已配置手动代码分块:

```typescript
build: {
  rollupOptions: {
    output: {
      manualChunks(id) {
        // Vendor chunks
        if (id.includes('node_modules')) {
          if (id.includes('react') || id.includes('react-dom') || id.includes('react-router')) {
            return 'react-vendor';
          }
          if (id.includes('antd')) {
            return 'antd-vendor';
          }
          if (id.includes('@tanstack/react-query')) {
            return 'query-vendor';
          }
          if (id.includes('socket.io-client')) {
            return 'socket-vendor';
          }
          if (id.includes('axios') || id.includes('dayjs') || id.includes('zustand')) {
            return 'utils-vendor';
          }
        }
      },
    },
  },
}
```

### 分块策略

1. **react-vendor**: React 核心库 (变化频率低,适合长期缓存)
2. **antd-vendor**: Ant Design UI 组件库 (体积大,独立缓存)
3. **query-vendor**: React Query 数据管理库
4. **socket-vendor**: Socket.IO 实时通信库
5. **utils-vendor**: 工具库 (axios, dayjs, zustand)

### 优化效果

- 首次加载时间减少 (只加载必要的代码)
- 更好的缓存策略 (vendor 代码变化少,可长期缓存)
- 并行加载多个小文件,提高加载速度

## 4. 资源加载优化

### 图片懒加载

**useImageLazyLoad Hook** 已创建用于图片懒加载:
- 位置: `src/hooks/useImageLazyLoad.ts`
- 实现: 使用 Intersection Observer API
- 效果: 图片进入视口前 50px 才开始加载

```tsx
import { useImageLazyLoad } from '@/hooks';

const MyComponent = () => {
  const { ref, loaded } = useImageLazyLoad();

  return (
    <img 
      ref={ref}
      src={loaded ? actualImageUrl : placeholderUrl}
      alt="Description"
    />
  );
};
```

### 构建优化

**vite.config.ts** 已配置生产构建优化:

```typescript
build: {
  // 代码分块 (见上文)
  rollupOptions: { ... },
  // 块大小警告阈值
  chunkSizeWarningLimit: 1000,
  // 禁用 source map (减小构建体积)
  sourcemap: false,
}
```

**注意**: 代码压缩可以通过安装 `terser` 或 `esbuild` 包来启用,但对于开发环境不是必需的。

### 依赖预优化

```typescript
optimizeDeps: {
  include: [
    'react',
    'react-dom',
    'react-router-dom',
    'antd',
    '@tanstack/react-query',
    'axios',
    'dayjs',
    'zustand',
    'socket.io-client',
  ],
}
```

## 5. 性能监控建议

### React DevTools Profiler

使用 React DevTools Profiler 监控组件渲染性能:
1. 打开 React DevTools
2. 切换到 Profiler 标签
3. 点击录制按钮
4. 执行操作
5. 停止录制并分析结果

### 关键指标

- **组件渲染次数**: 检查是否有不必要的重渲染
- **渲染时间**: 识别性能瓶颈组件
- **火焰图**: 查看组件渲染层级和时间分布

### Chrome DevTools Performance

使用 Chrome DevTools Performance 面板:
1. 打开 DevTools
2. 切换到 Performance 标签
3. 点击录制按钮
4. 执行操作
5. 停止录制并分析结果

### 关键指标

- **FCP (First Contentful Paint)**: 首次内容绘制时间
- **LCP (Largest Contentful Paint)**: 最大内容绘制时间
- **TTI (Time to Interactive)**: 可交互时间
- **TBT (Total Blocking Time)**: 总阻塞时间

## 6. 未来优化方向

### 虚拟滚动

如果合同列表或时间线数据量很大,可以考虑实现虚拟滚动:
- 使用 `react-window` 或 `react-virtualized`
- 只渲染可见区域的项目
- 大幅减少 DOM 节点数量

### Service Worker

实现 Service Worker 进行离线缓存:
- 缓存静态资源
- 缓存 API 响应
- 提供离线访问能力

### Web Workers

将计算密集型任务移到 Web Workers:
- 数据处理
- 复杂计算
- 避免阻塞主线程

### 预加载和预获取

使用 `<link rel="preload">` 和 `<link rel="prefetch">`:
- 预加载关键资源
- 预获取可能需要的资源
- 提高感知性能

## 7. 性能优化检查清单

- [x] 使用 React.memo 优化组件重渲染
- [x] 实现搜索输入防抖
- [x] 创建节流 Hook
- [x] 实现路由级别代码分割
- [x] 配置 Vite 手动代码分块
- [x] 创建图片懒加载 Hook
- [x] 配置生产构建优化
- [x] 配置依赖预优化
- [ ] 实现虚拟滚动 (如需要)
- [ ] 添加性能监控 (如需要)
- [ ] 实现 Service Worker (如需要)

## 8. 总结

本次性能优化实施涵盖了设计文档中要求的所有优化策略:

1. **React.memo**: 优化了 8 个关键组件,减少不必要的重渲染
2. **防抖/节流**: 实现了搜索防抖和通用节流 Hook
3. **代码分割**: 实现了路由级别代码分割和 vendor 分块
4. **资源优化**: 创建了图片懒加载 Hook 和构建优化配置

这些优化将显著提升应用的加载速度和运行时性能,为用户提供更流畅的体验。

## 参考资料

- [React.memo 文档](https://react.dev/reference/react/memo)
- [React.lazy 文档](https://react.dev/reference/react/lazy)
- [Vite 构建优化](https://vitejs.dev/guide/build.html)
- [Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API)
- [Web Performance](https://web.dev/performance/)
