# 合同预审看板系统 - 前端

基于 React 18 + TypeScript + Ant Design 5 的合同预审看板系统前端应用。

## 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Ant Design 5** - UI 组件库
- **Zustand** - 状态管理
- **React Query** - 服务端状态管理
- **Axios** - HTTP 客户端
- **Socket.io-client** - WebSocket 实时通信
- **Day.js** - 日期时间处理
- **React Router** - 路由管理

## 项目结构

```
src/
├── components/       # 可复用组件
│   ├── ContractList/    # 合同列表组件
│   ├── ContractDetail/  # 合同详情组件
│   └── AIAdvisor/       # AI 顾问组件
├── layouts/          # 布局组件
│   ├── MainLayout.tsx   # 主布局
│   └── ThreeColumnLayout.tsx  # 三栏布局
├── pages/            # 页面组件
│   └── ContractBoard.tsx  # 合同看板页面
├── stores/           # Zustand 状态管理
├── services/         # API 服务
├── hooks/            # 自定义 Hooks
├── utils/            # 工具函数
├── types/            # TypeScript 类型定义
├── config/           # 配置文件
│   └── api.ts           # API 配置
├── App.tsx           # 应用入口
└── main.tsx          # 主入口文件
```

## 开发指南

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

应用将在 http://localhost:3000 启动

### 构建生产版本

```bash
npm run build
```

### 代码检查

```bash
# 运行 ESLint
npm run lint

# 自动修复 ESLint 问题
npm run lint:fix

# 检查代码格式
npm run format:check

# 格式化代码
npm run format
```

## 环境变量

复制 `.env.example` 到 `.env` 并配置以下变量:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

## 功能特性

### 已实现

- ✅ 项目初始化和基础配置
- ✅ 三栏布局结构
- ✅ 基础组件框架
- ✅ 路由配置
- ✅ API 配置
- ✅ 代码规范配置 (ESLint + Prettier)

### 待实现

- ⏳ 合同列表功能
- ⏳ 合同详情展示
- ⏳ 评审时间线
- ⏳ AI 智能总结
- ⏳ AI 合同顾问
- ⏳ 合同创建表单
- ⏳ 快速审批功能
- ⏳ 实时通信 (WebSocket)

## 代码规范

项目使用 ESLint 和 Prettier 进行代码规范检查和格式化:

- **ESLint**: 代码质量检查
- **Prettier**: 代码格式化
- **TypeScript**: 类型检查

提交代码前请确保:
1. 运行 `npm run lint` 无错误
2. 运行 `npm run format` 格式化代码
3. 运行 `npm run build` 构建成功

## 浏览器支持

- Chrome (最新版)
- Firefox (最新版)
- Safari (最新版)
- Edge (最新版)

## 许可证

MIT
