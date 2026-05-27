# 技术设计文档 - 合同预审看板系统

## Overview

### 系统概述

合同预审看板系统是一个基于Web的协作平台,用于管理企业内部合同的预审流程。系统支持多角色(销售、法务、财务、业务、运营、人事)协同工作,提供合同创建、评审、讨论和审批功能,并集成AI辅助能力帮助用户快速理解合同状态和关键问题。

### 核心功能

1. **合同列表管理** - 支持筛选(全部/进行中/已完成/待我处理/抄送我)、搜索、状态展示
2. **合同详情展示** - 显示合同基本信息、评审人状态、附件版本管理
3. **评审时间线** - 按时间倒序展示评审意见、评论、回复,支持点赞和嵌套回复
4. **AI智能总结** - 自动生成审批进度摘要和关键问题提取
5. **AI合同顾问** - 提供法务意见查询、风险项识别、待办任务查询
6. **合同创建** - 表单化创建合同,选择评审人/抄送人,上传附件
7. **快速审批** - 一键同意待处理评审项

### 技术栈选择

**前端:**
- React 18 + TypeScript - 类型安全的组件化开发
- Zustand - 轻量级状态管理(替代Redux,更适合中小型应用)
- Ant Design 5 - 企业级UI组件库
- React Query - 服务端状态管理和缓存
- Socket.io-client - WebSocket实时通信
- Axios - HTTP客户端
- Day.js - 日期时间处理

**后端:**
- Python 3.11 + FastAPI - 现代化异步Web框架
- SQLAlchemy 2.0 - 强大的ORM
- Socket.IO (python-socketio) - WebSocket服务
- 钉钉开放平台SDK - 钉钉授权登录
- python-multipart - 文件上传处理
- Celery + Redis - 任务队列(处理AI总结等异步任务)

**数据库:**
- PostgreSQL 15 - 主数据库,支持JSONB字段存储灵活数据
- Redis 7 - 缓存层和会话存储

**文件存储:**
- MinIO - 开源对象存储(兼容S3 API)

**AI服务:**
- DeepSeek API - 主要AI服务提供商
- 自部署大模型 - 支持通过OpenAI兼容API接入(如vLLM、Ollama)
- 配置化模型切换 - 支持在配置文件中切换不同的AI服务

**部署:**
- Docker + Docker Compose - 容器化部署
- Nginx - 反向代理和静态资源服务


## Architecture

### 系统架构

系统采用经典的三层架构:

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (React)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │合同列表  │  │合同详情  │  │时间线    │  │AI顾问    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│         │              │              │              │        │
│         └──────────────┴──────────────┴──────────────┘        │
│                          │                                     │
│                    WebSocket + HTTP                            │
└─────────────────────────┼─────────────────────────────────────┘
                          │
┌─────────────────────────┼─────────────────────────────────────┐
│                    应用层 (FastAPI)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │合同服务  │  │评审服务  │  │文件服务  │  │AI服务    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│         │              │              │              │        │
│         └──────────────┴──────────────┴──────────────┘        │
│                          │                                     │
└─────────────────────────┼─────────────────────────────────────┘
                          │
┌─────────────────────────┼─────────────────────────────────────┐
│                    数据层                                      │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐           │
│  │ PostgreSQL   │  │  Redis   │  │   MinIO      │           │
│  │ (主数据库)   │  │  (缓存)  │  │ (文件存储)   │           │
│  └──────────────┘  └──────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 模块划分

**前端模块:**
1. **ContractList** - 合同列表组件(筛选、搜索、卡片展示)
2. **ContractDetail** - 合同详情组件(基本信息、评审人状态、附件管理)
3. **Timeline** - 时间线组件(评审意见、评论、回复)
4. **AIAdvisor** - AI顾问聊天组件
5. **ContractForm** - 合同创建表单
6. **QuickApproval** - 快速审批组件

**后端服务:**
1. **ContractService** - 合同CRUD、状态管理
2. **ReviewService** - 评审意见、评论、回复管理
3. **FileService** - 附件上传、版本管理、下载
4. **AIService** - 智能总结生成、顾问问答(支持DeepSeek和自部署模型)
5. **NotificationService** - 实时通知推送
6. **DingTalkAuthService** - 钉钉授权登录和用户信息同步


### 通信机制

**HTTP REST API:**
- 用于CRUD操作(创建合同、上传附件、提交评审等)
- 使用钉钉授权Token进行身份认证
- 响应格式: `{ success: boolean, data?: any, error?: string }`

**WebSocket (Socket.io):**
- 用于实时更新(新评论、点赞、状态变更)
- 事件类型:
  - `contract:updated` - 合同信息更新
  - `review:added` - 新增评审意见
  - `comment:added` - 新增评论
  - `reply:added` - 新增回复
  - `like:updated` - 点赞更新
  - `pending:changed` - 待办数量变化

### 性能优化策略

1. **前端优化:**
   - 虚拟滚动(react-window) - 处理大量合同列表
   - 懒加载 - 附件预览按需加载
   - 防抖/节流 - 搜索输入、滚动事件
   - React.memo - 避免不必要的组件重渲染
   - Code Splitting - 路由级别代码分割

2. **后端优化:**
   - Redis缓存 - 合同列表、用户信息、待办数量
   - 数据库索引 - contract_id, user_id, status, created_at
   - 分页查询 - 限制单次返回数据量
   - 连接池 - 数据库连接复用

3. **文件处理:**
   - 缩略图生成 - PDF首页预览
   - CDN加速 - 静态资源和附件下载
   - 断点续传 - 大文件上传


## Components and Interfaces

### 前端组件设计

#### 1. ContractList 组件

**职责:** 展示合同列表,支持筛选和搜索

**Props:**
```typescript
interface ContractListProps {
  onContractSelect: (contractId: string) => void;
  selectedContractId?: string;
}
```

**State:**
```typescript
interface ContractListState {
  contracts: Contract[];
  filter: 'all' | '进行中' | '已完成' | '待我处理' | '抄送我';
  searchKeyword: string;
  pendingCount: number;
}
```

**子组件:**
- `FilterBar` - 筛选按钮组
- `SearchBox` - 搜索输入框
- `ContractCard` - 单个合同卡片
- `QuickApprovalButton` - 快速同意按钮

#### 2. ContractDetail 组件

**职责:** 展示合同详细信息和附件

**Props:**
```typescript
interface ContractDetailProps {
  contractId: string;
}
```

**State:**
```typescript
interface ContractDetailState {
  contract: Contract | null;
  attachments: AttachmentGroup[];
  reviewers: ReviewerStatus[];
}
```

**子组件:**
- `AttachmentList` - 附件列表(按文件名分组)
- `AttachmentVersion` - 单个附件版本
- `ReviewerStatusList` - 评审人状态列表
- `UploadButton` - 上传附件按钮

#### 3. Timeline 组件

**职责:** 展示评审时间线

**Props:**
```typescript
interface TimelineProps {
  contractId: string;
}
```

**State:**
```typescript
interface TimelineState {
  reviews: Review[];
  aiSummary: AISummary | null;
  expandedReplies: Set<string>;
}
```

**子组件:**
- `AISummaryCard` - AI智能总结卡片
- `ReviewCard` - 评审意见卡片
- `ReplyList` - 回复列表
- `CommentInput` - 评论输入框


#### 4. AIAdvisor 组件

**职责:** AI合同顾问聊天界面

**Props:**
```typescript
interface AIAdvisorProps {
  contractId: string;
  contractName: string;
}
```

**State:**
```typescript
interface AIAdvisorState {
  messages: Message[];
  inputValue: string;
  isLoading: boolean;
}
```

#### 5. ContractForm 组件

**职责:** 创建合同表单

**Props:**
```typescript
interface ContractFormProps {
  visible: boolean;
  onClose: () => void;
  onSubmit: (data: ContractFormData) => Promise<void>;
}
```

**State:**
```typescript
interface ContractFormState {
  name: string;
  description: string;
  reviewers: string[];
  ccUsers: string[];
  files: File[];
  errors: Record<string, string>;
}
```

### 后端API接口

#### 合同管理 API

**GET /api/contracts**
- 描述: 获取合同列表
- 查询参数:
  - `filter`: 'all' | '进行中' | '已完成' | '待我处理' | '抄送我'
  - `search`: 搜索关键词
  - `page`: 页码
  - `limit`: 每页数量
- 响应:
```typescript
{
  success: true,
  data: {
    contracts: Contract[],
    total: number,
    pendingCount: number
  }
}
```

**GET /api/contracts/:id**
- 描述: 获取合同详情
- 响应:
```typescript
{
  success: true,
  data: {
    contract: Contract,
    attachments: AttachmentGroup[],
    reviewers: ReviewerStatus[]
  }
}
```

**POST /api/contracts**
- 描述: 创建合同
- 请求体:
```typescript
{
  name: string,
  description?: string,
  reviewers: string[],
  ccUsers: string[]
}
```
- 响应:
```typescript
{
  success: true,
  data: { contractId: string }
}
```


#### 评审管理 API

**GET /api/contracts/:id/reviews**
- 描述: 获取合同的所有评审记录
- 响应:
```typescript
{
  success: true,
  data: {
    reviews: Review[],
    aiSummary: AISummary | null
  }
}
```

**POST /api/contracts/:id/reviews/:reviewId/approve**
- 描述: 同意评审项
- 请求体:
```typescript
{
  opinion: string
}
```
- 响应:
```typescript
{
  success: true,
  data: { review: Review }
}
```

**POST /api/contracts/:id/comments**
- 描述: 添加评论
- 请求体:
```typescript
{
  reviewId?: string,  // 可选,如果是回复评审意见
  parentCommentId?: string,  // 可选,如果是嵌套回复
  content: string
}
```
- 响应:
```typescript
{
  success: true,
  data: { comment: Comment }
}
```

**POST /api/reviews/:reviewId/like**
- 描述: 点赞评审意见
- 响应:
```typescript
{
  success: true,
  data: { likes: number }
}
```

**POST /api/comments/:commentId/like**
- 描述: 点赞评论
- 响应:
```typescript
{
  success: true,
  data: { likes: number }
}
```


#### 文件管理 API

**POST /api/contracts/:id/attachments**
- 描述: 上传附件
- 请求: multipart/form-data
  - `file`: 文件
  - `version`: 版本号(可选)
- 响应:
```typescript
{
  success: true,
  data: { attachment: Attachment }
}
```

**GET /api/attachments/:id/download**
- 描述: 下载附件
- 响应: 文件流

#### AI服务 API

**POST /api/ai/summary/:contractId**
- 描述: 生成AI智能总结(使用配置的AI模型)
- 响应:
```typescript
{
  success: true,
  data: { summary: AISummary }
}
```

**POST /api/ai/advisor**
- 描述: AI顾问问答(使用配置的AI模型)
- 请求体:
```typescript
{
  contractId: string,
  question: string
}
```
- 响应:
```typescript
{
  success: true,
  data: { answer: string }
}
```

**AI模型配置:**
系统支持以下AI服务:
1. **DeepSeek API** - 通过DeepSeek官方API
2. **自部署模型** - 通过OpenAI兼容API(如vLLM、Ollama、LocalAI)

配置示例:
```python
# config.py
AI_CONFIG = {
    "provider": "deepseek",  # 或 "custom"
    "api_base": "https://api.deepseek.com/v1",  # DeepSeek API地址
    "api_key": "your-api-key",
    "model": "deepseek-chat",
    # 自部署模型配置示例:
    # "provider": "custom",
    # "api_base": "http://localhost:8000/v1",
    # "model": "qwen2.5-7b-instruct"
}
```

#### 钉钉授权登录 API

**GET /api/auth/dingtalk/login**
- 描述: 获取钉钉授权登录URL
- 响应:
```typescript
{
  success: true,
  data: {
    authUrl: string  // 钉钉授权页面URL
  }
}
```

**GET /api/auth/dingtalk/callback**
- 描述: 钉钉授权回调处理
- 查询参数:
  - `code`: 钉钉授权码
  - `state`: 状态参数
- 响应:
```typescript
{
  success: true,
  data: {
    token: string,
    user: User
  }
}
```

**GET /api/auth/me**
- 描述: 获取当前用户信息
- 响应:
```typescript
{
  success: true,
  data: { user: User }
}
```


## Data Models

### 数据库Schema设计

#### User (用户表)

```typescript
interface User {
  id: string;              // UUID
  dingtalkUserId: string;  // 钉钉用户ID(唯一)
  dingtalkUnionId?: string; // 钉钉UnionID
  name: string;            // 显示名称
  role: string;            // 角色(销售/法务/财务/业务/运营/人事)
  email?: string;          // 邮箱
  mobile?: string;         // 手机号
  avatar?: string;         // 头像URL
  department?: string;     // 部门
  createdAt: Date;
  updatedAt: Date;
}
```

**索引:**
- PRIMARY KEY: `id`
- UNIQUE: `dingtalkUserId`
- INDEX: `role`

#### Contract (合同表)

```typescript
interface Contract {
  id: string;              // UUID
  name: string;            // 合同名称
  description?: string;    // 合同描述
  status: 'progress' | 'completed';  // 状态
  initiatorId: string;     // 发起人ID (FK -> User.id)
  ccUsers: string[];       // 抄送人ID数组
  createdAt: Date;
  updatedAt: Date;
}
```

**索引:**
- PRIMARY KEY: `id`
- INDEX: `initiatorId`
- INDEX: `status`
- INDEX: `createdAt DESC`

#### Review (评审记录表)

```typescript
interface Review {
  id: string;              // UUID
  contractId: string;      // 合同ID (FK -> Contract.id)
  reviewerId: string;      // 评审人ID (FK -> User.id)
  role: string;            // 评审人角色
  step: string;            // 评审步骤(如"法务初审")
  opinion?: string;        // 评审意见
  status: 'pending' | 'reviewing' | 'approved';  // 状态
  likes: number;           // 点赞数
  likedBy: string[];       // 点赞用户ID数组
  createdAt: Date;
  updatedAt: Date;
}
```

**索引:**
- PRIMARY KEY: `id`
- INDEX: `contractId`
- INDEX: `reviewerId`
- INDEX: `status`
- INDEX: `createdAt DESC`


#### Comment (评论表)

```typescript
interface Comment {
  id: string;              // UUID
  contractId: string;      // 合同ID (FK -> Contract.id)
  reviewId?: string;       // 评审ID (FK -> Review.id, 可选)
  parentCommentId?: string; // 父评论ID (FK -> Comment.id, 用于嵌套回复)
  authorId: string;        // 作者ID (FK -> User.id)
  content: string;         // 评论内容
  likes: number;           // 点赞数
  likedBy: string[];       // 点赞用户ID数组
  createdAt: Date;
  updatedAt: Date;
}
```

**索引:**
- PRIMARY KEY: `id`
- INDEX: `contractId`
- INDEX: `reviewId`
- INDEX: `parentCommentId`
- INDEX: `createdAt DESC`

#### Attachment (附件表)

```typescript
interface Attachment {
  id: string;              // UUID
  contractId: string;      // 合同ID (FK -> Contract.id)
  fileName: string;        // 文件名
  version: string;         // 版本号
  fileSize: number;        // 文件大小(字节)
  mimeType: string;        // MIME类型
  storageKey: string;      // 存储键(MinIO对象键)
  uploaderId: string;      // 上传人ID (FK -> User.id)
  createdAt: Date;
}
```

**索引:**
- PRIMARY KEY: `id`
- INDEX: `contractId`
- INDEX: `fileName, createdAt DESC` (复合索引,用于按文件名分组和排序)

#### AISummary (AI总结表)

```typescript
interface AISummary {
  id: string;              // UUID
  contractId: string;      // 合同ID (FK -> Contract.id)
  approvalStatus: 'completed' | 'in_progress';  // 审批状态
  completedCount: number;  // 已完成人数
  totalCount: number;      // 总人数
  reviewCount: number;     // 评审意见总数
  keyIssues: KeyIssue[];   // 关键问题数组(JSONB)
  createdAt: Date;
  updatedAt: Date;
}

interface KeyIssue {
  issue: string;           // 问题描述
  solution?: string;       // 解决方案
}
```

**索引:**
- PRIMARY KEY: `id`
- UNIQUE: `contractId`
- INDEX: `updatedAt DESC`


### 数据关系图

```
User (用户)
  │
  ├─── initiates ────> Contract (合同)
  │                       │
  │                       ├─── has ────> Review (评审记录)
  │                       │                 │
  │                       │                 └─── has ────> Comment (评论)
  │                       │                                    │
  │                       │                                    └─── replies to ──> Comment
  │                       │
  │                       ├─── has ────> Attachment (附件)
  │                       │
  │                       └─── has ────> AISummary (AI总结)
  │
  ├─── reviews ──────> Review
  │
  ├─── comments ─────> Comment
  │
  └─── uploads ──────> Attachment
```

### Redis缓存设计

**缓存键命名规范:**
- `contract:list:{userId}:{filter}` - 用户的合同列表缓存
- `contract:detail:{contractId}` - 合同详情缓存
- `contract:pending:{userId}` - 用户待办数量缓存
- `reviews:{contractId}` - 合同评审记录缓存
- `ai:summary:{contractId}` - AI总结缓存
- `user:session:{token}` - 用户会话缓存

**缓存过期策略:**
- 合同列表: 5分钟
- 合同详情: 10分钟
- 待办数量: 1分钟
- 评审记录: 5分钟
- AI总结: 30分钟
- 用户会话: 24小时

**缓存失效策略:**
- 写操作(创建/更新/删除)时主动清除相关缓存
- 使用Redis的EXPIRE自动过期
- WebSocket推送时清除客户端缓存

### MinIO存储设计

**Bucket结构:**
- `contract-attachments` - 存储所有合同附件

**对象键命名:**
- `{contractId}/{fileName}/{version}/{uuid}.{ext}`
- 例如: `123e4567-e89b-12d3-a456-426614174000/采购清单.pdf/v1.0/abc123.pdf`

**访问控制:**
- 私有访问,通过后端API生成预签名URL
- 预签名URL有效期: 1小时


## Error Handling

### 错误分类

#### 1. 客户端错误 (4xx)

**400 Bad Request - 请求参数错误**
- 场景: 缺少必填字段、字段格式错误、文件类型不支持
- 处理: 返回详细的错误信息,前端显示表单验证提示
- 示例:
```typescript
{
  success: false,
  error: "合同名称不能为空",
  code: "VALIDATION_ERROR",
  field: "name"
}
```

**401 Unauthorized - 未授权**
- 场景: Token过期、Token无效、未登录
- 处理: 清除本地Token,重定向到钉钉授权登录页
- 示例:
```typescript
{
  success: false,
  error: "登录已过期,请重新登录",
  code: "TOKEN_EXPIRED"
}
```

**403 Forbidden - 权限不足**
- 场景: 非评审人尝试审批、非发起人尝试删除合同
- 处理: 显示权限不足提示,禁用相关操作按钮
- 示例:
```typescript
{
  success: false,
  error: "您没有权限执行此操作",
  code: "PERMISSION_DENIED"
}
```

**404 Not Found - 资源不存在**
- 场景: 合同ID不存在、附件已删除
- 处理: 显示友好的404页面或提示
- 示例:
```typescript
{
  success: false,
  error: "合同不存在或已被删除",
  code: "RESOURCE_NOT_FOUND"
}
```

**413 Payload Too Large - 文件过大**
- 场景: 上传文件超过20MB限制
- 处理: 上传前前端校验,后端拒绝并返回错误
- 示例:
```typescript
{
  success: false,
  error: "文件大小不能超过20MB",
  code: "FILE_TOO_LARGE"
}
```


#### 2. 服务端错误 (5xx)

**500 Internal Server Error - 服务器内部错误**
- 场景: 数据库连接失败、未捕获的异常
- 处理: 记录详细日志,返回通用错误信息,触发告警
- 示例:
```typescript
{
  success: false,
  error: "服务器内部错误,请稍后重试",
  code: "INTERNAL_ERROR",
  requestId: "req_123456"  // 用于追踪
}
```

**502 Bad Gateway - 上游服务错误**
- 场景: MinIO不可用、AI服务(DeepSeek/自部署模型)超时
- 处理: 降级处理(如AI功能暂时不可用),显示友好提示
- 示例:
```typescript
{
  success: false,
  error: "AI服务暂时不可用,请稍后重试",
  code: "AI_SERVICE_UNAVAILABLE"
}
```

**503 Service Unavailable - 服务不可用**
- 场景: 系统维护、数据库连接池耗尽
- 处理: 返回维护页面或限流提示
- 示例:
```typescript
{
  success: false,
  error: "系统正在维护,预计10分钟后恢复",
  code: "SERVICE_MAINTENANCE"
}
```

### 错误处理策略

#### 前端错误处理

**全局错误拦截器:**
```typescript
// Axios响应拦截器
axios.interceptors.response.use(
  response => response,
  error => {
    const { response } = error;
    
    if (!response) {
      // 网络错误
      message.error('网络连接失败,请检查网络');
      return Promise.reject(error);
    }
    
    switch (response.status) {
      case 401:
        // 清除Token,跳转钉钉授权登录
        localStorage.removeItem('token');
        window.location.href = '/api/auth/dingtalk/login';
        break;
      case 403:
        message.error('权限不足');
        break;
      case 404:
        message.error('资源不存在');
        break;
      case 413:
        message.error('文件过大');
        break;
      case 500:
        message.error('服务器错误,请稍后重试');
        break;
      default:
        message.error(response.data?.error || '操作失败');
    }
    
    return Promise.reject(error);
  }
);
```


**组件级错误边界:**
```typescript
// ErrorBoundary组件
class ErrorBoundary extends React.Component {
  state = { hasError: false };
  
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }
  
  componentDidCatch(error, errorInfo) {
    // 上报错误到监控系统
    console.error('Component Error:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return <div>组件加载失败,请刷新页面</div>;
    }
    return this.props.children;
  }
}
```

**WebSocket错误处理:**
```typescript
socket.on('connect_error', (error) => {
  console.error('WebSocket连接失败:', error);
  message.warning('实时通信连接失败,部分功能可能受影响');
});

socket.on('disconnect', (reason) => {
  if (reason === 'io server disconnect') {
    // 服务端主动断开,尝试重连
    socket.connect();
  }
});
```

#### 后端错误处理

**全局错误处理中间件:**
```typescript
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  // 记录错误日志
  logger.error({
    message: err.message,
    stack: err.stack,
    requestId: req.id,
    url: req.url,
    method: req.method,
    userId: req.user?.id
  });
  
  // 区分错误类型
  if (err instanceof ValidationError) {
    return res.status(400).json({
      success: false,
      error: err.message,
      code: 'VALIDATION_ERROR',
      field: err.field
    });
  }
  
  if (err instanceof UnauthorizedError) {
    return res.status(401).json({
      success: false,
      error: '未授权',
      code: 'UNAUTHORIZED'
    });
  }
  
  // 默认500错误
  res.status(500).json({
    success: false,
    error: '服务器内部错误',
    code: 'INTERNAL_ERROR',
    requestId: req.id
  });
});
```


**数据库错误处理:**
```typescript
try {
  const contract = await prisma.contract.create({ data });
} catch (error) {
  if (error.code === 'P2002') {
    // 唯一约束冲突
    throw new ValidationError('合同名称已存在');
  }
  if (error.code === 'P2025') {
    // 记录不存在
    throw new NotFoundError('合同不存在');
  }
  // 其他数据库错误
  throw new DatabaseError('数据库操作失败');
}
```

**外部服务错误处理:**
```python
# AI服务调用
async def generate_ai_summary(contract_id: str):
    try:
        # 使用配置的AI服务(DeepSeek或自部署模型)
        response = await ai_client.chat.completions.create(
            model=AI_CONFIG["model"],
            messages=[...],
            timeout=30.0  # 30秒超时
        )
        return response.choices[0].message.content
    except asyncio.TimeoutError:
        logger.warning(f"AI服务超时: contract_id={contract_id}")
        return None  # 降级处理,返回None
    except Exception as e:
        if hasattr(e, 'status_code') and e.status_code == 429:
            logger.warning(f"AI服务限流: contract_id={contract_id}")
            # 加入重试队列
            await retry_queue.enqueue(contract_id, delay=60)
            return None
        raise e
```

### 数据一致性保证

**事务处理:**
```python
# 创建合同时使用事务
async def create_contract(data: ContractData, db: AsyncSession):
    async with db.begin():
        # 1. 创建合同
        contract = Contract(
            name=data.name,
            description=data.description,
            status="progress",
            initiator_id=data.initiator_id,
            cc_users=data.cc_users
        )
        db.add(contract)
        await db.flush()  # 获取contract.id
        
        # 2. 创建评审记录
        reviews = [
            Review(
                contract_id=contract.id,
                reviewer_id=reviewer_id,
                status="pending"
            )
            for reviewer_id in data.reviewers
        ]
        db.add_all(reviews)
        
        # 3. 清除缓存
        await redis.delete(f"contract:list:*")
        
        await db.commit()
        return contract
```

**乐观锁:**
```python
# 使用版本号防止并发更新冲突
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound

async def update_contract(
    contract_id: str, 
    data: dict, 
    expected_version: int,
    db: AsyncSession
):
    result = await db.execute(
        update(Contract)
        .where(
            Contract.id == contract_id,
            Contract.version == expected_version
        )
        .values(**data, version=expected_version + 1)
    )
    
    if result.rowcount == 0:
        raise ConflictError("合同已被其他用户修改,请刷新后重试")
    
    await db.commit()
```


## Testing Strategy

### 测试方法论

本系统是一个Web应用,主要包含UI交互、CRUD操作、文件处理和外部服务集成。**Property-Based Testing不适用于此类系统**,因为:

1. **UI渲染和交互** - 适合使用快照测试和视觉回归测试
2. **简单CRUD操作** - 适合使用示例测试和集成测试
3. **文件上传/下载** - 副作用操作,适合使用Mock测试
4. **WebSocket通信** - 依赖外部服务,适合使用集成测试
5. **AI服务** - 外部API调用,适合使用Mock测试

因此,我们采用**传统的测试金字塔策略**:
- **单元测试** - 测试独立的函数和组件
- **集成测试** - 测试API端点和数据库交互
- **端到端测试** - 测试完整的用户流程

### 测试覆盖目标

- **单元测试覆盖率**: ≥ 80%
- **集成测试覆盖率**: ≥ 70%
- **端到端测试**: 覆盖核心用户流程

### 前端测试

#### 1. 单元测试 (Jest + React Testing Library)

**组件测试:**
```typescript
// ContractCard.test.tsx
describe('ContractCard', () => {
  it('应该显示合同名称和状态', () => {
    const contract = {
      id: '1',
      name: '测试合同',
      status: '进行中',
      initiator: '张三',
      date: '2025-03-01'
    };
    
    render(<ContractCard contract={contract} />);
    
    expect(screen.getByText('测试合同')).toBeInTheDocument();
    expect(screen.getByText('进行中')).toBeInTheDocument();
  });
  
  it('当有待处理项时应该显示同意按钮', () => {
    const contract = { /* ... */ };
    const hasPending = true;
    
    render(<ContractCard contract={contract} hasPending={hasPending} />);
    
    expect(screen.getByText('同意')).toBeInTheDocument();
  });
  
  it('点击卡片应该触发选择事件', () => {
    const onSelect = jest.fn();
    const contract = { /* ... */ };
    
    render(<ContractCard contract={contract} onSelect={onSelect} />);
    
    fireEvent.click(screen.getByText('测试合同'));
    expect(onSelect).toHaveBeenCalledWith('1');
  });
});
```


**工具函数测试:**
```typescript
// utils/time.test.ts
describe('formatRelativeTime', () => {
  it('1小时内应该显示相对时间', () => {
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
    
    expect(formatRelativeTime(fiveMinutesAgo)).toBe('5分钟前');
  });
  
  it('超过30天应该显示具体日期', () => {
    const date = new Date('2024-01-01');
    
    expect(formatRelativeTime(date)).toBe('2024-01-01');
  });
});

// utils/filter.test.ts
describe('filterContracts', () => {
  const contracts = [
    { id: '1', name: '合同A', status: '进行中', initiator: '张三' },
    { id: '2', name: '合同B', status: '已完成', initiator: '李四' }
  ];
  
  it('应该按状态筛选合同', () => {
    const result = filterContracts(contracts, '进行中', '');
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('1');
  });
  
  it('应该按关键词搜索合同', () => {
    const result = filterContracts(contracts, 'all', '李四');
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('2');
  });
});
```

**Hooks测试:**
```typescript
// hooks/useContractList.test.ts
describe('useContractList', () => {
  it('应该加载合同列表', async () => {
    const { result } = renderHook(() => useContractList());
    
    await waitFor(() => {
      expect(result.current.contracts).toHaveLength(4);
    });
  });
  
  it('应该支持筛选', async () => {
    const { result } = renderHook(() => useContractList());
    
    act(() => {
      result.current.setFilter('进行中');
    });
    
    await waitFor(() => {
      expect(result.current.filteredContracts.every(c => c.status === '进行中')).toBe(true);
    });
  });
});
```

#### 2. 快照测试 (Jest Snapshots)

**组件快照:**
```typescript
// ContractCard.snapshot.test.tsx
describe('ContractCard Snapshots', () => {
  it('应该匹配进行中状态的快照', () => {
    const contract = {
      id: '1',
      name: '测试合同',
      status: '进行中',
      initiator: '张三',
      date: '2025-03-01'
    };
    
    const { container } = render(<ContractCard contract={contract} />);
    expect(container).toMatchSnapshot();
  });
  
  it('应该匹配已完成状态的快照', () => {
    const contract = {
      id: '2',
      name: '测试合同',
      status: '已完成',
      initiator: '李四',
      date: '2025-02-28'
    };
    
    const { container } = render(<ContractCard contract={contract} />);
    expect(container).toMatchSnapshot();
  });
});
```

#### 3. 集成测试 (React Testing Library)

**用户流程测试:**
```typescript
// ContractList.integration.test.tsx
describe('ContractList Integration', () => {
  it('应该支持完整的筛选和搜索流程', async () => {
    render(<ContractList />);
    
    // 等待数据加载
    await waitFor(() => {
      expect(screen.getAllByTestId('contract-card')).toHaveLength(4);
    });
    
    // 点击"进行中"筛选
    fireEvent.click(screen.getByText('进行中'));
    expect(screen.getAllByTestId('contract-card')).toHaveLength(2);
    
    // 输入搜索关键词
    const searchInput = screen.getByPlaceholderText('搜索合同名称或发起人');
    fireEvent.change(searchInput, { target: { value: '张三' } });
    
    await waitFor(() => {
      expect(screen.getAllByTestId('contract-card')).toHaveLength(1);
    });
  });
  
  it('应该支持快速审批流程', async () => {
    const mockApprove = jest.fn();
    render(<ContractList onApprove={mockApprove} />);
    
    // 点击同意按钮
    const approveButton = screen.getByText('同意');
    fireEvent.click(approveButton);
    
    // 确认对话框
    await waitFor(() => {
      expect(screen.getByText('确认同意')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('确定'));
    
    expect(mockApprove).toHaveBeenCalled();
  });
});
```

### 后端测试

#### 1. 单元测试 (Pytest)

**服务层测试:**
```python
# tests/services/test_contract_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.contract_service import ContractService

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def contract_service(mock_db):
    return ContractService(mock_db)

class TestContractService:
    @pytest.mark.asyncio
    async def test_create_contract_success(self, contract_service, mock_db):
        """应该创建合同并返回合同ID"""
        contract_data = {
            "name": "测试合同",
            "description": "测试描述",
            "reviewers": ["user1", "user2"],
            "cc_users": ["user3"]
        }
        
        mock_contract = MagicMock(
            id="contract-123",
            name="测试合同",
            status="progress"
        )
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        
        result = await contract_service.create_contract(
            contract_data, 
            "current-user"
        )
        
        assert result.id == "contract-123"
        mock_db.add.assert_called_once()
```

**工具函数测试:**
```typescript
// utils/validation.test.ts
describe('Validation Utils', () => {
  describe('validateContractData', () => {
    it('应该验证有效的合同数据', () => {
      const data = {
        name: '测试合同',
        reviewers: ['user1', 'user2']
      };
      
      expect(() => validateContractData(data)).not.toThrow();
    });
    
    it('应该拒绝空合同名称', () => {
      const data = {
        name: '',
        reviewers: ['user1']
      };
      
      expect(() => validateContractData(data)).toThrow('合同名称不能为空');
    });
    
    it('应该拒绝空评审人列表', () => {
      const data = {
        name: '测试合同',
        reviewers: []
      };
      
      expect(() => validateContractData(data)).toThrow('至少需要一个评审人');
    });
  });
  
  describe('validateFileUpload', () => {
    it('应该验证有效的文件类型', () => {
      const file = {
        mimetype: 'application/pdf',
        size: 1024 * 1024 * 10  // 10MB
      };
      
      expect(() => validateFileUpload(file)).not.toThrow();
    });
    
    it('应该拒绝不支持的文件类型', () => {
      const file = {
        mimetype: 'application/zip',
        size: 1024 * 1024
      };
      
      expect(() => validateFileUpload(file)).toThrow('不支持的文件类型');
    });
    
    it('应该拒绝超过大小限制的文件', () => {
      const file = {
        mimetype: 'application/pdf',
        size: 1024 * 1024 * 25  // 25MB
      };
      
      expect(() => validateFileUpload(file)).toThrow('文件大小不能超过20MB');
    });
  });
});
```

#### 2. API集成测试 (Supertest)

**API端点测试:**
```typescript
// routes/contracts.integration.test.ts
describe('Contract API Integration', () => {
  let app: Express;
  let authToken: string;
  
  beforeAll(async () => {
    app = createApp();
    // 登录获取token
    const response = await request(app)
      .post('/api/auth/login')
      .send({ username: 'testuser', password: 'password' });
    authToken = response.body.data.token;
  });
  
  describe('POST /api/contracts', () => {
    it('应该创建新合同', async () => {
      const contractData = {
        name: '测试合同',
        description: '测试描述',
        reviewers: ['user1', 'user2'],
        ccUsers: ['user3']
      };
      
      const response = await request(app)
        .post('/api/contracts')
        .set('Authorization', `Bearer ${authToken}`)
        .send(contractData)
        .expect(200);
      
      expect(response.body.success).toBe(true);
      expect(response.body.data.contractId).toBeDefined();
    });
    
    it('当缺少必填字段时应该返回400错误', async () => {
      const response = await request(app)
        .post('/api/contracts')
        .set('Authorization', `Bearer ${authToken}`)
        .send({ description: '只有描述' })
        .expect(400);
      
      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('合同名称');
    });
    
    it('当未授权时应该返回401错误', async () => {
      await request(app)
        .post('/api/contracts')
        .send({ name: '测试合同' })
        .expect(401);
    });
  });
  
  describe('GET /api/contracts', () => {
    it('应该返回合同列表', async () => {
      const response = await request(app)
        .get('/api/contracts')
        .set('Authorization', `Bearer ${authToken}`)
        .query({ filter: 'all' })
        .expect(200);
      
      expect(response.body.success).toBe(true);
      expect(Array.isArray(response.body.data.contracts)).toBe(true);
      expect(response.body.data.pendingCount).toBeDefined();
    });
    
    it('应该支持筛选参数', async () => {
      const response = await request(app)
        .get('/api/contracts')
        .set('Authorization', `Bearer ${authToken}`)
        .query({ filter: '进行中' })
        .expect(200);
      
      const contracts = response.body.data.contracts;
      expect(contracts.every(c => c.status === 'progress')).toBe(true);
    });
    
    it('应该支持搜索参数', async () => {
      const response = await request(app)
        .get('/api/contracts')
        .set('Authorization', `Bearer ${authToken}`)
        .query({ search: '测试' })
        .expect(200);
      
      const contracts = response.body.data.contracts;
      expect(contracts.every(c => 
        c.name.includes('测试') || c.initiator.includes('测试')
      )).toBe(true);
    });
  });
  
  describe('POST /api/contracts/:id/reviews/:reviewId/approve', () => {
    it('应该同意评审项', async () => {
      const response = await request(app)
        .post('/api/contracts/contract-123/reviews/review-456/approve')
        .set('Authorization', `Bearer ${authToken}`)
        .send({ opinion: '同意并通过' })
        .expect(200);
      
      expect(response.body.success).toBe(true);
      expect(response.body.data.review.status).toBe('approved');
    });
    
    it('当非评审人尝试审批时应该返回403错误', async () => {
      const response = await request(app)
        .post('/api/contracts/contract-123/reviews/review-789/approve')
        .set('Authorization', `Bearer ${authToken}`)
        .send({ opinion: '同意' })
        .expect(403);
      
      expect(response.body.error).toContain('权限');
    });
  });
});
```

#### 3. 数据库集成测试

**数据库操作测试:**
```typescript
// database/contracts.db.test.ts
describe('Contract Database Operations', () => {
  let prisma: PrismaClient;
  
  beforeAll(async () => {
    prisma = new PrismaClient();
    await prisma.$connect();
  });
  
  afterAll(async () => {
    await prisma.$disconnect();
  });
  
  beforeEach(async () => {
    // 清空测试数据
    await prisma.comment.deleteMany();
    await prisma.review.deleteMany();
    await prisma.attachment.deleteMany();
    await prisma.contract.deleteMany();
  });
  
  it('应该创建合同并自动创建评审记录', async () => {
    const contract = await prisma.contract.create({
      data: {
        name: '测试合同',
        status: 'progress',
        initiatorId: 'user1',
        ccUsers: ['user2']
      }
    });
    
    await prisma.review.createMany({
      data: [
        { contractId: contract.id, reviewerId: 'user3', status: 'pending' },
        { contractId: contract.id, reviewerId: 'user4', status: 'pending' }
      ]
    });
    
    const reviews = await prisma.review.findMany({
      where: { contractId: contract.id }
    });
    
    expect(reviews).toHaveLength(2);
  });
  
  it('应该支持事务回滚', async () => {
    await expect(
      prisma.$transaction(async (tx) => {
        await tx.contract.create({
          data: {
            name: '测试合同',
            status: 'progress',
            initiatorId: 'user1'
          }
        });
        
        // 故意抛出错误触发回滚
        throw new Error('测试回滚');
      })
    ).rejects.toThrow('测试回滚');
    
    // 验证数据未被保存
    const contracts = await prisma.contract.findMany();
    expect(contracts).toHaveLength(0);
  });
  
  it('应该正确处理级联删除', async () => {
    const contract = await prisma.contract.create({
      data: {
        name: '测试合同',
        status: 'progress',
        initiatorId: 'user1'
      }
    });
    
    await prisma.review.create({
      data: {
        contractId: contract.id,
        reviewerId: 'user2',
        status: 'pending'
      }
    });
    
    await prisma.contract.delete({
      where: { id: contract.id }
    });
    
    const reviews = await prisma.review.findMany({
      where: { contractId: contract.id }
    });
    
    expect(reviews).toHaveLength(0);
  });
});
```

#### 4. 外部服务Mock测试

**AI服务Mock测试:**
```typescript
// services/AIService.test.ts
describe('AIService', () => {
  let aiService: AIService;
  let mockOpenAI: jest.Mocked<OpenAI>;
  
  beforeEach(() => {
    mockOpenAI = {
      chat: {
        completions: {
          create: jest.fn()
        }
      }
    } as any;
    
    aiService = new AIService(mockOpenAI);
  });
  
  describe('generateSummary', () => {
    it('应该生成AI总结', async () => {
      const mockResponse = {
        choices: [{
          message: {
            content: JSON.stringify({
              approvalStatus: 'in_progress',
              completedCount: 2,
              totalCount: 5,
              reviewCount: 8,
              keyIssues: [
                { issue: '需要补充财务数据', solution: '已提供' }
              ]
            })
          }
        }]
      };
      
      mockOpenAI.chat.completions.create.mockResolvedValue(mockResponse as any);
      
      const result = await aiService.generateSummary('contract-123');
      
      expect(result.approvalStatus).toBe('in_progress');
      expect(result.keyIssues).toHaveLength(1);
    });
    
    it('当API超时时应该返回null', async () => {
      mockOpenAI.chat.completions.create.mockRejectedValue(
        new Error('ETIMEDOUT')
      );
      
      const result = await aiService.generateSummary('contract-123');
      
      expect(result).toBeNull();
    });
  });
});
```

**文件存储Mock测试:**
```typescript
// services/FileService.test.ts
describe('FileService', () => {
  let fileService: FileService;
  let mockMinIO: jest.Mocked<MinIO.Client>;
  
  beforeEach(() => {
    mockMinIO = {
      putObject: jest.fn(),
      getObject: jest.fn(),
      presignedGetObject: jest.fn()
    } as any;
    
    fileService = new FileService(mockMinIO);
  });
  
  describe('uploadFile', () => {
    it('应该上传文件到MinIO', async () => {
      const file = {
        buffer: Buffer.from('test content'),
        originalname: '测试文件.pdf',
        mimetype: 'application/pdf',
        size: 1024
      };
      
      mockMinIO.putObject.mockResolvedValue({ etag: 'abc123' } as any);
      
      const result = await fileService.uploadFile('contract-123', file);
      
      expect(result.fileName).toBe('测试文件.pdf');
      expect(mockMinIO.putObject).toHaveBeenCalled();
    });
    
    it('当上传失败时应该抛出错误', async () => {
      const file = {
        buffer: Buffer.from('test'),
        originalname: 'test.pdf',
        mimetype: 'application/pdf',
        size: 1024
      };
      
      mockMinIO.putObject.mockRejectedValue(new Error('Upload failed'));
      
      await expect(
        fileService.uploadFile('contract-123', file)
      ).rejects.toThrow('文件上传失败');
    });
  });
});
```

### 端到端测试

#### 1. E2E测试 (Playwright)

**完整用户流程测试:**
```typescript
// e2e/contract-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('合同预审完整流程', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('http://localhost:3000/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:3000/');
  });
  
  test('应该完成创建合同到审批的完整流程', async ({ page }) => {
    // 1. 点击发起合同预审
    await page.click('text=发起合同预审');
    
    // 2. 填写合同信息
    await page.fill('input[name="name"]', 'E2E测试合同');
    await page.fill('textarea[name="description"]', '这是一个端到端测试合同');
    
    // 3. 选择评审人
    await page.click('text=选择评审人');
    await page.click('text=张三');
    await page.click('text=李四');
    
    // 4. 上传附件
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-files/sample.pdf');
    
    // 5. 提交合同
    await page.click('button:has-text("提交")');
    
    // 6. 验证合同出现在列表中
    await expect(page.locator('text=E2E测试合同')).toBeVisible();
    
    // 7. 点击合同查看详情
    await page.click('text=E2E测试合同');
    
    // 8. 验证合同详情显示正确
    await expect(page.locator('text=这是一个端到端测试合同')).toBeVisible();
    await expect(page.locator('text=sample.pdf')).toBeVisible();
    
    // 9. 添加评论
    await page.fill('textarea[placeholder="输入评论..."]', '这是一条测试评论');
    await page.press('textarea[placeholder="输入评论..."]', 'Enter');
    
    // 10. 验证评论显示
    await expect(page.locator('text=这是一条测试评论')).toBeVisible();
    
    // 11. 快速审批
    await page.click('button:has-text("同意")');
    await page.click('button:has-text("确定")');
    
    // 12. 验证审批状态更新
    await expect(page.locator('text=✅')).toBeVisible();
  });
  
  test('应该支持筛选和搜索功能', async ({ page }) => {
    // 1. 点击"进行中"筛选
    await page.click('text=进行中');
    
    // 2. 验证只显示进行中的合同
    const cards = page.locator('[data-testid="contract-card"]');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
    
    // 3. 输入搜索关键词
    await page.fill('input[placeholder*="搜索"]', '测试');
    
    // 4. 验证搜索结果
    await expect(page.locator('text=测试合同')).toBeVisible();
  });
  
  test('应该支持AI顾问问答', async ({ page }) => {
    // 1. 选择一个合同
    await page.click('[data-testid="contract-card"]').first();
    
    // 2. 在AI顾问输入框输入问题
    await page.fill('input[placeholder*="输入问题"]', '有哪些法务意见?');
    await page.press('input[placeholder*="输入问题"]', 'Enter');
    
    // 3. 验证AI回复
    await expect(page.locator('.ai-message')).toBeVisible();
  });
});
```

**WebSocket实时更新测试:**
```typescript
// e2e/realtime-updates.spec.ts
test.describe('实时更新功能', () => {
  test('应该实时显示新评论', async ({ browser }) => {
    // 创建两个浏览器上下文模拟两个用户
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // 用户1登录
    await page1.goto('http://localhost:3000/login');
    await page1.fill('input[name="username"]', 'user1');
    await page1.fill('input[name="password"]', 'password');
    await page1.click('button[type="submit"]');
    
    // 用户2登录
    await page2.goto('http://localhost:3000/login');
    await page2.fill('input[name="username"]', 'user2');
    await page2.fill('input[name="password"]', 'password');
    await page2.click('button[type="submit"]');
    
    // 两个用户都打开同一个合同
    await page1.click('[data-testid="contract-card"]').first();
    await page2.click('[data-testid="contract-card"]').first();
    
    // 用户1添加评论
    await page1.fill('textarea[placeholder="输入评论..."]', '实时测试评论');
    await page1.press('textarea[placeholder="输入评论..."]', 'Enter');
    
    // 验证用户2能实时看到评论
    await expect(page2.locator('text=实时测试评论')).toBeVisible({ timeout: 5000 });
    
    await context1.close();
    await context2.close();
  });
});
```

### 测试覆盖率要求

**覆盖率目标:**
- **单元测试**: ≥ 80% (代码行覆盖率)
- **集成测试**: ≥ 70% (API端点覆盖率)
- **端到端测试**: 100% (核心用户流程覆盖)

**核心用户流程:**
1. 用户登录
2. 创建合同
3. 上传附件
4. 添加评论
5. 快速审批
6. 筛选和搜索
7. AI顾问问答

**测试执行策略:**
- 单元测试: 每次代码提交时自动运行
- 集成测试: 每次Pull Request时运行
- 端到端测试: 每日定时运行 + 部署前运行

**测试工具配置:**
```json
// package.json
{
  "scripts": {
    "test": "jest",
    "test:unit": "jest --testPathPattern=\\.test\\.(ts|tsx)$",
    "test:integration": "jest --testPathPattern=\\.integration\\.test\\.(ts|tsx)$",
    "test:e2e": "playwright test",
    "test:coverage": "jest --coverage",
    "test:watch": "jest --watch"
  },
  "jest": {
    "coverageThreshold": {
      "global": {
        "branches": 80,
        "functions": 80,
        "lines": 80,
        "statements": 80
      }
    }
  }
}
```

### 关于Correctness Properties

**为什么本设计文档不包含Correctness Properties章节:**

本系统是一个典型的Web应用,主要包含以下特征:

1. **UI渲染和交互** - React组件的渲染和用户交互行为
2. **简单CRUD操作** - 合同、评审、评论的创建、读取、更新、删除
3. **文件上传/下载** - 副作用操作,依赖外部存储服务(MinIO)
4. **WebSocket实时通信** - 依赖外部服务,用于推送实时更新
5. **AI服务集成** - 调用外部API(OpenAI)

根据Property-Based Testing (PBT)的适用性评估:

**PBT不适用的原因:**
- **UI渲染** - 适合使用快照测试和视觉回归测试,而非属性测试
- **CRUD操作** - 行为确定且简单,适合使用示例测试,不需要生成大量随机输入
- **外部服务** - 测试外部服务的配置和集成,而非测试我们代码的逻辑属性
- **副作用操作** - 文件上传、WebSocket通信等副作用操作不适合属性测试
- **确定性行为** - 大部分操作是确定性的,不需要通过100+次随机输入来发现边界情况

**采用的测试策略:**
- **单元测试** - 测试独立函数和组件的具体行为
- **快照测试** - 验证UI组件的渲染输出
- **集成测试** - 测试API端点和数据库交互
- **端到端测试** - 验证完整的用户流程
- **Mock测试** - 隔离外部依赖(AI服务、文件存储)

这些传统的测试方法更适合本系统的特点,能够提供充分的测试覆盖和质量保证。



## 技术栈变更说明

### 变更概述

根据项目需求,对原设计文档进行了以下技术栈调整:

### 1. 后端语言变更: Node.js → Python

**变更内容:**
- **原技术栈**: Node.js 20 + Express 4 + TypeScript + Prisma
- **新技术栈**: Python 3.11 + FastAPI + SQLAlchemy 2.0

**变更原因:**
- 团队技术栈偏好
- Python生态在AI/数据处理方面更成熟
- FastAPI提供优秀的异步性能和自动API文档

**影响范围:**
- 所有后端代码示例改为Python语法
- ORM从Prisma改为SQLAlchemy
- 测试框架从Jest改为Pytest
- 任务队列从Bull改为Celery

### 2. 用户认证变更: 传统登录 → 钉钉授权登录

**变更内容:**
- **原方案**: 用户名/密码登录 + JWT认证
- **新方案**: 钉钉OAuth授权登录

**变更原因:**
- 企业内部系统,统一使用钉钉账号体系
- 简化用户管理,无需维护密码
- 提升安全性和用户体验

**影响范围:**
- User数据模型:移除username/password字段,添加dingtalkUserId/dingtalkUnionId
- 认证API:从POST /api/auth/login改为GET /api/auth/dingtalk/login和callback
- 前端登录流程:从表单登录改为跳转钉钉授权页面
- 新增DingTalkAuthService服务

### 3. AI服务变更: OpenAI → DeepSeek + 自部署模型

**变更内容:**
- **原方案**: 仅支持OpenAI API (GPT-4)
- **新方案**: 支持DeepSeek API + 自部署大模型(通过OpenAI兼容API)

**变更原因:**
- 成本考虑:DeepSeek性价比更高
- 数据安全:支持私有化部署的大模型
- 灵活性:可根据场景切换不同模型

**影响范围:**
- AI服务配置:添加provider、api_base、model等配置项
- AIService实现:支持多种AI服务提供商
- 错误处理:适配不同AI服务的错误响应格式

### 技术栈对比表

| 组件 | 原技术栈 | 新技术栈 | 变更原因 |
|------|---------|---------|---------|
| 后端框架 | Node.js + Express | Python + FastAPI | 团队偏好,AI生态 |
| ORM | Prisma | SQLAlchemy 2.0 | 配合Python |
| 用户认证 | JWT | 钉钉OAuth | 企业账号体系 |
| AI服务 | OpenAI GPT-4 | DeepSeek + 自部署 | 成本,安全,灵活性 |
| 任务队列 | Bull | Celery | 配合Python |
| 后端测试 | Jest | Pytest | 配合Python |

### 不变的技术栈

以下技术栈保持不变:
- **前端**: React 18 + TypeScript + Ant Design 5
- **数据库**: PostgreSQL 15 + Redis 7
- **文件存储**: MinIO
- **WebSocket**: Socket.IO (前后端)
- **部署**: Docker + Docker Compose

### 迁移注意事项

1. **数据库Schema**: User表需要添加钉钉相关字段,移除password字段
2. **API接口**: 认证相关接口需要重新设计
3. **前端登录**: 需要实现钉钉授权登录流程
4. **AI配置**: 需要添加AI服务配置文件
5. **测试用例**: 后端测试需要从Jest迁移到Pytest

### 配置文件示例

**AI服务配置 (config/ai.py):**
```python
AI_CONFIG = {
    # DeepSeek配置
    "provider": "deepseek",
    "api_base": "https://api.deepseek.com/v1",
    "api_key": "your-deepseek-api-key",
    "model": "deepseek-chat",
    
    # 自部署模型配置示例(注释掉)
    # "provider": "custom",
    # "api_base": "http://localhost:8000/v1",
    # "api_key": "not-needed",
    # "model": "qwen2.5-7b-instruct"
}
```

**钉钉配置 (config/dingtalk.py):**
```python
DINGTALK_CONFIG = {
    "app_key": "your-app-key",
    "app_secret": "your-app-secret",
    "redirect_uri": "http://your-domain.com/api/auth/dingtalk/callback",
    "scope": "openid corpid"
}
```
