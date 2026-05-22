# API 快速参考指南

## 访问 API 文档

系统提供三种方式访问 API 文档:

### 1. 交互式文档 (Swagger UI)
**URL**: http://localhost:8000/api/docs

**特点:**
- 可视化界面
- 可直接测试 API
- 自动生成请求示例
- 支持认证测试

### 2. 文档浏览 (ReDoc)
**URL**: http://localhost:8000/api/redoc

**特点:**
- 清晰的文档布局
- 更好的阅读体验
- 支持搜索
- 响应式设计

### 3. OpenAPI Schema
**URL**: http://localhost:8000/api/openapi.json

**特点:**
- JSON 格式的 API 规范
- 可导入到 Postman、Insomnia 等工具
- 可用于代码生成

### 4. 详细文档
**文件**: `backend/API_DOCUMENTATION.md`

**特点:**
- 完整的 API 说明
- 使用示例和最佳实践
- 错误处理指南
- 性能优化建议
- 常见问题解答


---

## 快速开始

### 1. 启动服务

```bash
# 启动所有服务 (PostgreSQL, Redis, MinIO, Backend)
cd backend
docker-compose up -d

# 或使用项目根目录的脚本
./docker-start.sh
```

### 2. 访问文档

打开浏览器访问: http://localhost:8000/api/docs

### 3. 测试 API

在 Swagger UI 中:
1. 点击右上角 "Authorize" 按钮
2. 输入 Bearer Token: `Bearer YOUR_TOKEN`
3. 点击任意 API 端点
4. 点击 "Try it out" 按钮
5. 填写参数并点击 "Execute"

---

## API 端点概览

### 认证 API (`/api/auth`)
- `GET /api/auth/dingtalk/login` - 获取钉钉授权 URL
- `GET /api/auth/dingtalk/callback` - 钉钉授权回调
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/logout` - 用户登出

### 合同管理 API (`/api/contracts`)
- `POST /api/contracts` - 创建合同
- `GET /api/contracts` - 获取合同列表
- `GET /api/contracts/{id}` - 获取合同详情
- `POST /api/contracts/{id}/comments` - 添加评论

### 评审管理 API (`/api`)
- `GET /api/contracts/{id}/reviews` - 获取评审记录
- `POST /api/contracts/{id}/reviews/{review_id}/approve` - 同意评审
- `POST /api/reviews/{id}/like` - 点赞评审意见
- `POST /api/comments/{id}/like` - 点赞评论

### 文件管理 API (`/api`)
- `POST /api/contracts/{id}/attachments` - 上传附件
- `GET /api/attachments/{id}/download` - 下载附件
- `GET /api/attachments/{id}/stream` - 文件流下载
- `GET /api/attachments/{id}` - 获取附件信息

### AI 功能 API (`/api/ai`)
- `POST /api/ai/summary/{contract_id}` - 生成 AI 智能总结
- `GET /api/ai/summary/{contract_id}` - 获取已生成的总结
- `POST /api/ai/advisor` - AI 顾问问答
- `GET /api/ai/summary/task/{task_id}` - 获取任务状态


---

## 常用请求示例

### 获取合同列表

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/contracts?filter=待我处理&page=1&limit=20"
```

### 创建合同

```bash
curl -X POST http://localhost:8000/api/contracts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "采购合同-2025-001",
    "description": "与供应商A的年度采购合同",
    "reviewers": [
      {"user_id": "user-1", "role": "法务", "step": "法务初审"}
    ],
    "cc_users": ["user-3"]
  }'
```

### 上传附件

```bash
curl -X POST http://localhost:8000/api/contracts/CONTRACT_ID/attachments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/contract.pdf"
```

### 同意评审

```bash
curl -X POST http://localhost:8000/api/contracts/CONTRACT_ID/reviews/REVIEW_ID/approve \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"opinion": "同意并通过"}'
```

### AI 顾问问答

```bash
curl -X POST http://localhost:8000/api/ai/advisor \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_id": "CONTRACT_ID",
    "question": "法务有什么意见?"
  }'
```

---

## 响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    // 响应数据
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "错误描述",
  "code": "ERROR_CODE"
}
```

或 FastAPI 默认格式:

```json
{
  "detail": "错误描述"
}
```

---

## 认证说明

所有 API 端点(除了登录相关)都需要认证。

**请求头格式:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**获取 Token:**
1. 访问 `/api/auth/dingtalk/login` 获取钉钉授权 URL
2. 用户完成钉钉授权
3. 系统回调 `/api/auth/dingtalk/callback` 并返回 Token

**Token 有效期:** 24 小时

---

## WebSocket 连接

**连接地址:** `ws://localhost:8000/socket.io`

**认证方式:**
```javascript
const socket = io('http://localhost:8000', {
  path: '/socket.io',
  auth: { token: 'YOUR_JWT_TOKEN' }
});
```

**事件列表:**
- `contract:updated` - 合同更新
- `review:added` - 新增评审
- `comment:added` - 新增评论
- `reply:added` - 新增回复
- `like:updated` - 点赞更新
- `pending:changed` - 待办变化

---

## 更多信息

详细文档请参考: `backend/API_DOCUMENTATION.md`

包含:
- 完整的 API 说明
- 数据模型定义
- 错误码说明
- 使用示例
- 性能优化建议
- 安全建议
- 常见问题解答
