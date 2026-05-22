# ContractList 组件文档

## 概述

ContractList 是合同预审看板系统的核心组件之一,负责展示合同列表并提供筛选、搜索和选择功能。

## 功能特性

### 1. 合同列表展示
- 显示所有合同的卡片列表
- 每个卡片显示合同名称、发起人、日期和状态
- 支持滚动查看大量合同

### 2. 筛选功能
- **全部**: 显示所有合同
- **进行中**: 仅显示状态为"进行中"的合同
- **已完成**: 仅显示状态为"已完成"的合同
- **待我处理**: 仅显示当前用户有待处理评审项的合同
- **抄送我**: 仅显示抄送给当前用户的合同

### 3. 搜索功能
- 实时搜索合同名称或发起人
- 防抖优化(300ms),减少不必要的 API 调用
- 支持清除搜索关键词

### 4. 待办提醒
- 在"待我处理"按钮上显示待办数量徽章
- 自动刷新待办数量(每 30 秒)

### 5. 合同选择
- 点击合同卡片选中该合同
- 选中的合同显示高亮效果(左侧蓝色边框)
- 触发 `onContractSelect` 回调

### 6. 快速审批
- 对于有待处理评审项的合同,显示"同意"按钮
- 点击按钮可快速审批(功能待实现)

### 7. 状态管理
- **加载状态**: 显示 Spin 加载动画
- **错误状态**: 显示错误消息
- **空状态**: 显示"暂无合同"提示

## 组件结构

```
ContractList
├── Header
│   └── 发起合同预审按钮
├── Filters
│   ├── SearchBox (搜索框)
│   └── FilterBar (筛选按钮组)
└── Items
    ├── ContractCard (合同卡片 1)
    ├── ContractCard (合同卡片 2)
    └── ...
```

## Props

```typescript
interface ContractListProps {
  onContractSelect?: (contractId: string) => void;
}
```

### onContractSelect (可选)
- **类型**: `(contractId: string) => void`
- **描述**: 当用户选择合同时触发的回调函数
- **参数**: `contractId` - 被选中的合同 ID

## 使用示例

### 基础使用

```tsx
import ContractList from './components/ContractList/ContractList';

function App() {
  return (
    <div className="app">
      <ContractList />
    </div>
  );
}
```

### 带回调的使用

```tsx
import ContractList from './components/ContractList/ContractList';
import ContractDetail from './components/ContractDetail/ContractDetail';
import { useState } from 'react';

function App() {
  const [selectedContractId, setSelectedContractId] = useState<string | null>(null);

  const handleContractSelect = (contractId: string) => {
    setSelectedContractId(contractId);
  };

  return (
    <div className="app">
      <div className="sidebar">
        <ContractList onContractSelect={handleContractSelect} />
      </div>
      <div className="main">
        {selectedContractId && (
          <ContractDetail contractId={selectedContractId} />
        )}
      </div>
    </div>
  );
}
```

## 状态管理

### Zustand Stores

组件使用以下 Zustand stores:

1. **useContractListStore**
   - `contracts`: 合同列表数据
   - `filter`: 当前筛选条件
   - `searchKeyword`: 搜索关键词
   - `pendingCount`: 待办数量

2. **useSelectedContractStore**
   - `selectedContractId`: 当前选中的合同 ID

### React Query Hooks

组件使用以下 React Query hooks:

1. **useContractList(filter, searchKeyword)**
   - 获取合同列表数据
   - 自动缓存和重新获取
   - 缓存时间: 5 分钟

2. **usePendingCount()**
   - 获取待办数量
   - 自动刷新: 每 30 秒
   - 缓存时间: 1 分钟

## 样式类名

### 主要类名

- `.contract-list` - 组件根容器
- `.contract-list-header` - 头部区域
- `.contract-list-filters` - 筛选区域
- `.contract-list-items` - 合同列表区域
- `.contract-list-loading` - 加载状态容器
- `.contract-list-error` - 错误状态容器
- `.contract-list-empty` - 空状态容器

### 自定义样式

```css
/* 自定义滚动条样式 */
.contract-list-items::-webkit-scrollbar {
  width: 6px;
}

.contract-list-items::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

/* 自定义加载动画 */
.contract-list-loading {
  min-height: 300px;
}
```

## 性能优化

### 1. 数据缓存
- 使用 React Query 缓存合同列表数据
- 避免重复的 API 调用

### 2. 防抖搜索
- 搜索输入使用 300ms 防抖
- 减少不必要的 API 请求

### 3. 条件渲染
- 仅在需要时渲染子组件
- 使用 React.memo 优化子组件(如需要)

### 4. 虚拟滚动(待实现)
- 对于大量合同(>1000),建议使用 react-window
- 提高滚动性能

## 可访问性

### 键盘导航
- 所有按钮和输入框支持键盘操作
- Tab 键切换焦点
- Enter 键触发操作

### 屏幕阅读器
- 使用语义化 HTML 标签
- 提供 aria-label 属性(如需要)
- 状态变化有明确的文本提示

## 错误处理

### 网络错误
- 显示友好的错误消息
- 提供重试机制(通过 React Query)

### 数据验证
- 处理空数据情况
- 处理无效数据格式

### 用户反馈
- 加载状态: Spin 组件
- 错误状态: Empty 组件 + 错误消息
- 空状态: Empty 组件 + "暂无合同"

## 测试

### 单元测试

测试文件: `ContractList.test.tsx`

测试用例:
- ✅ 应该显示加载状态
- ✅ 应该显示错误状态
- ✅ 应该显示空状态
- ✅ 应该显示合同列表
- ✅ 应该显示待处理徽章
- ✅ 应该支持筛选切换
- ✅ 应该支持搜索
- ✅ 应该支持合同选择
- ✅ 应该显示同意按钮
- ✅ 应该显示发起合同预审按钮

### 集成测试

建议测试场景:
- 筛选 + 搜索组合
- 选择合同 + 加载详情
- 快速审批流程

## 常见问题

### Q: 如何自定义筛选条件?
A: 修改 `FilterBar` 组件的 `filters` 数组,添加新的筛选选项。

### Q: 如何修改缓存时间?
A: 在 `useContractList` hook 中修改 `staleTime` 参数。

### Q: 如何添加虚拟滚动?
A: 安装 `react-window`,使用 `FixedSizeList` 或 `VariableSizeList` 组件包裹合同卡片列表。

### Q: 如何自定义合同卡片样式?
A: 修改 `ContractCard.css` 文件,或通过 props 传递自定义类名。

## 相关组件

- **ContractCard** - 合同卡片组件
- **FilterBar** - 筛选按钮组组件
- **SearchBox** - 搜索框组件
- **ContractDetail** - 合同详情组件(配合使用)

## 更新日志

### v1.0.0 (2025-01-18)
- ✅ 初始实现
- ✅ 集成所有子组件
- ✅ 连接状态管理和数据获取
- ✅ 实现筛选、搜索、选择功能
- ✅ 添加加载、错误、空状态处理
- ✅ 创建单元测试

## 许可证

MIT
