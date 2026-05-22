# Task 19.1 Complete: 配置 Axios 客户端

## 任务概述

成功配置了前端 Axios HTTP 客户端,实现了统一的请求/响应处理、自动认证、错误处理和类型安全。

## 实现内容

### 1. Axios 实例配置 (`src/utils/axios.ts`)

创建了配置完整的 Axios 实例:

**基础配置:**
- Base URL: 从环境变量 `VITE_API_BASE_URL` 读取
- 超时时间: 30 秒
- 默认 Content-Type: `application/json`

**请求拦截器:**
- 自动从 localStorage 读取 JWT token
- 自动添加 `Authorization: Bearer <token>` 请求头
- 支持所有需要认证的 API 请求

**响应拦截器:**
- 统一错误处理,根据 HTTP 状态码显示友好的错误提示
- 401 错误自动清除 token 并跳转到钉钉登录页面
- 使用 Ant Design 的 `message` 组件显示错误消息
- 支持的错误类型:
  - 401: 登录过期,自动跳转登录
  - 403: 权限不足
  - 404: 资源不存在
  - 413: 文件过大
  - 500: 服务器错误
  - 502: 服务不可用
  - 503: 系统维护
  - 网络错误: 网络连接失败

### 2. 类型安全的请求工具 (`src/utils/request.ts`)

提供了完整的类型安全 HTTP 请求函数:

**基础请求方法:**
- `get<T>(url, config)` - GET 请求
- `post<T>(url, data, config)` - POST 请求
- `put<T>(url, data, config)` - PUT 请求
- `patch<T>(url, data, config)` - PATCH 请求
- `del<T>(url, config)` - DELETE 请求

**文件操作方法:**
- `upload<T>(url, formData, onProgress)` - 文件上传,支持进度回调
- `download(url, filename)` - 文件下载,自动触发浏览器下载

**特性:**
- 所有函数使用 TypeScript 泛型,提供完整的类型推断
- 自动提取 API 响应的 `data` 字段,简化使用
- 使用 `unknown` 替代 `any`,提高类型安全性
- 支持 Axios 的所有配置选项

### 3. API 响应类型定义 (`src/types/api.ts`)

定义了标准的 API 响应格式:

```typescript
interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  code?: string;
  field?: string;
  requestId?: string;
}
```

支持分页响应:
```typescript
interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}
```

### 4. 工具导出 (`src/utils/index.ts`)

提供统一的导出点,方便其他模块导入:
```typescript
export { default as axios } from './axios';
export * from './request';
```

### 5. 文档和示例

**README.md:**
- 详细的使用文档
- 各种场景的代码示例
- 错误处理说明
- 类型安全指南

**测试示例文件 (`__test_axios__.ts`):**
- GET 请求示例
- POST 请求示例
- 文件上传示例
- 文件下载示例

## 技术要点

### 1. 自动认证
```typescript
// 请求拦截器自动添加 token
const token = localStorage.getItem('token');
if (token && config.headers) {
  config.headers.Authorization = `Bearer ${token}`;
}
```

### 2. 401 自动跳转
```typescript
case 401:
  message.error('登录已过期,请重新登录');
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = '/api/auth/dingtalk/login';
  break;
```

### 3. 类型安全
```typescript
// 使用泛型提供类型推断
const contracts = await get<Contract[]>(API_ENDPOINTS.CONTRACTS.LIST);
// contracts 的类型是 Contract[]
```

### 4. 文件上传进度
```typescript
await upload(url, formData, (progressEvent) => {
  const percent = Math.round(
    (progressEvent.loaded * 100) / (progressEvent.total || 1)
  );
  console.log(`Upload progress: ${percent}%`);
});
```

## 使用示例

### 获取合同列表
```typescript
import { get } from '@/utils/request';
import { API_ENDPOINTS } from '@/config/api';

const contracts = await get(API_ENDPOINTS.CONTRACTS.LIST);
```

### 创建合同
```typescript
import { post } from '@/utils/request';
import { API_ENDPOINTS } from '@/config/api';

const newContract = await post(API_ENDPOINTS.CONTRACTS.CREATE, {
  name: '新合同',
  description: '合同描述',
  reviewers: ['user1', 'user2'],
  ccUsers: ['user3']
});
```

### 上传附件
```typescript
import { upload } from '@/utils/request';
import { API_ENDPOINTS } from '@/config/api';

const formData = new FormData();
formData.append('file', file);

const result = await upload(
  API_ENDPOINTS.CONTRACTS.ATTACHMENTS(contractId),
  formData,
  (progressEvent) => {
    const percent = Math.round(
      (progressEvent.loaded * 100) / (progressEvent.total || 1)
    );
    setUploadProgress(percent);
  }
);
```

## 文件清单

创建的文件:
- ✅ `src/utils/axios.ts` - Axios 实例配置
- ✅ `src/utils/request.ts` - 类型安全的请求工具
- ✅ `src/utils/index.ts` - 工具导出
- ✅ `src/types/api.ts` - API 响应类型定义
- ✅ `src/utils/README.md` - 使用文档
- ✅ `src/utils/__test_axios__.ts` - 测试示例

## 验证结果

### TypeScript 编译
- ✅ 所有新文件通过 TypeScript 类型检查
- ✅ 使用 type-only imports 符合 verbatimModuleSyntax 要求
- ✅ 所有类型定义正确,无 `any` 类型

### ESLint 检查
- ✅ 所有新文件通过 ESLint 检查
- ✅ 代码格式符合 Prettier 规范
- ✅ 无未使用的变量或导入

### 功能验证
- ✅ Axios 实例正确配置
- ✅ 请求拦截器正确添加 Authorization header
- ✅ 响应拦截器正确处理各种错误状态
- ✅ 类型安全的请求函数正确导出
- ✅ 文件上传/下载功能完整实现

## 设计文档对应

本任务实现了设计文档中的以下内容:

**前端架构 (Design.md):**
- ✅ Axios HTTP 客户端配置
- ✅ 请求拦截器 (添加 Authorization header)
- ✅ 响应拦截器 (统一错误处理)
- ✅ 401 错误自动跳转钉钉登录

**错误处理策略 (Design.md - Error Handling):**
- ✅ 全局错误拦截器
- ✅ 401/403/404/413/500/502/503 错误处理
- ✅ 网络错误处理
- ✅ 友好的错误提示

**需求覆盖:**
- ✅ 需求 10.1-10.10: 用户界面交互和错误处理
- ✅ 需求 8.10: 钉钉授权登录集成

## 后续任务

Task 19.1 已完成,可以继续执行:
- Task 19.2: 配置 Zustand 状态管理
- Task 19.3: 配置 React Query
- Task 19.4: 配置 Socket.IO 客户端

## 注意事项

1. **Token 存储**: 当前使用 localStorage 存储 token,生产环境建议考虑更安全的存储方式
2. **错误消息**: 所有错误消息使用中文,符合项目需求
3. **类型安全**: 所有请求函数都使用泛型,确保类型安全
4. **环境变量**: API_BASE_URL 从 .env 文件读取,确保正确配置

## 总结

Task 19.1 成功完成,实现了完整的 Axios HTTP 客户端配置,包括:
- ✅ 自动认证机制
- ✅ 统一错误处理
- ✅ 类型安全的请求工具
- ✅ 文件上传/下载支持
- ✅ 完整的文档和示例

所有代码通过 TypeScript 和 ESLint 检查,符合项目代码规范。
