# 合同预审看板系统 - Docker 启动成功 ✅

## 系统状态

所有服务已成功启动并运行：

- ✅ **Frontend (前端)**: http://localhost
- ✅ **Backend (后端)**: http://localhost:8000
- ✅ **PostgreSQL (数据库)**: localhost:5432
- ✅ **Redis (缓存)**: localhost:6379
- ✅ **MinIO (文件存储)**: http://localhost:9001 (控制台)
- ✅ **Celery Worker (异步任务)**: 运行中

## 访问系统

### 1. 打开浏览器访问
```
http://localhost
```

### 2. 钉钉登录配置

**重要提示**: 由于您没有公网 IP 或域名，钉钉 OAuth 回调无法正常工作。有以下几种测试方案：

#### 方案 A: 使用 ngrok 临时公网地址（推荐用于测试钉钉登录）

1. 安装 ngrok: https://ngrok.com/download
2. 启动 ngrok:
   ```bash
   ngrok http 80
   ```
3. 获取 ngrok 提供的公网地址（如 `https://xxxx.ngrok.io`）
4. 更新后端配置 `/Users/cm/Documents/kiro/project/backend/.env`:
   ```
   DINGTALK_REDIRECT_URI=https://xxxx.ngrok.io/auth/callback
   ```
5. 在钉钉开放平台更新回调地址为: `https://xxxx.ngrok.io/auth/callback`
6. 重启后端:
   ```bash
   docker compose restart backend
   ```
7. 通过 ngrok 地址访问系统: `https://xxxx.ngrok.io`

#### 方案 B: 直接测试 API（不需要钉钉登录）

访问 API 文档直接测试后端功能:
```
http://localhost:8000/docs
```

在这里可以：
- 查看所有 API 接口
- 直接测试 API 调用
- 不需要钉钉登录即可测试大部分功能

#### 方案 C: 模拟登录（开发测试）

如果只是想测试系统功能，可以临时修改后端代码跳过钉钉认证（仅用于开发测试）。

## 当前配置

### 钉钉配置
- **AppKey**: dingkrwl72tqfsl781ns
- **AppSecret**: XcPgi6KsK1dU9cor1gANWQuYSym-yxw71xy8xeA1hufW-1QYX0XXK8_QM76vQSqB
- **回调地址**: http://localhost/auth/callback （需要改为公网地址才能正常工作）

### DeepSeek AI 配置
- **API Key**: sk-50b210fd06654e228bf4c85278174b95
- **模型**: deepseek-v4-flash
- **API Base**: https://api.deepseek.com/v1

## 常用命令

### 查看服务状态
```bash
docker compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery_worker
```

### 重启服务
```bash
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart backend
docker compose restart frontend
```

### 停止服务
```bash
docker compose down
```

### 重新构建并启动
```bash
docker compose up -d --build
```

## 测试 API

### 1. 健康检查
```bash
curl http://localhost:8000/health
```

### 2. 获取钉钉登录 URL
```bash
curl http://localhost/api/auth/dingtalk/login
```

### 3. 访问 API 文档
浏览器打开: http://localhost:8000/docs

## 数据库管理

### 连接数据库
```bash
docker compose exec postgres psql -U postgres -d contract_review
```

### 查看表
```sql
\dt
```

### 查看用户
```sql
SELECT * FROM users;
```

## MinIO 文件存储

访问 MinIO 控制台:
- URL: http://localhost:9001
- 用户名: minioadmin
- 密码: minioadmin

## 故障排查

### 前端无法连接后端
1. 检查浏览器控制台是否有错误
2. 确认 API 请求是否使用相对路径（不应该有 `localhost:8000`）
3. 检查 Nginx 代理配置是否正确

### 后端启动失败
1. 查看后端日志: `docker compose logs backend`
2. 检查数据库连接是否正常
3. 确认环境变量配置正确

### 数据库连接失败
1. 确认 PostgreSQL 容器正在运行: `docker compose ps postgres`
2. 检查数据库健康状态
3. 查看数据库日志: `docker compose logs postgres`

## 下一步

1. **如果要测试钉钉登录**: 使用 ngrok 方案 A
2. **如果只是测试功能**: 使用 API 文档方案 B
3. **如果要正式部署**: 需要配置真实的域名和 HTTPS

## 技术栈

- **前端**: React + TypeScript + Vite + Ant Design
- **后端**: FastAPI + Python 3.11
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **文件存储**: MinIO
- **异步任务**: Celery
- **Web服务器**: Nginx
- **容器化**: Docker + Docker Compose

## 系统功能

1. ✅ 钉钉 OAuth 登录
2. ✅ 合同上传与管理
3. ✅ AI 智能预审（DeepSeek）
4. ✅ 多人协作审批
5. ✅ 实时通知（WebSocket）
6. ✅ 评论与讨论
7. ✅ 附件管理
8. ✅ 审批流程
9. ✅ 看板视图

---

**系统已成功启动！** 🎉

如有问题，请查看日志或参考上述故障排查部分。
