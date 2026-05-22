# 🚀 快速启动指南

## ✅ 配置已完成

以下配置已经设置好：

### 钉钉配置
- AppKey: `dingkrwl72tqfsl781ns`
- AppSecret: `XcPgi6KsK1dU9cor1gANWQuYSym-yxw71xy8xeA1hufW-1QYX0XXK8_QM76vQSqB`
- 回调地址: `http://localhost:3000/auth/callback`

### AI 配置
- 提供商: DeepSeek
- 模型: `deepseek-v4-flash`
- API Key: 已配置

### JWT 密钥
- 已生成强随机密钥

---

## 📝 启动步骤

### 方式 1: 使用启动脚本（推荐，适合开发调试）

#### 步骤 1: 启动基础设施服务

```bash
cd /Users/cm/Documents/kiro/project
chmod +x start-services.sh
./start-services.sh
```

这会启动：
- PostgreSQL (端口 5432)
- Redis (端口 6379)
- MinIO (端口 9000, 9001)

#### 步骤 2: 启动后端服务

**新开一个终端窗口**，运行：

```bash
cd /Users/cm/Documents/kiro/project
chmod +x start-backend.sh
./start-backend.sh
```

后端会在 `http://localhost:8000` 启动

#### 步骤 3: 启动前端服务

**再新开一个终端窗口**，运行：

```bash
cd /Users/cm/Documents/kiro/project
chmod +x start-frontend.sh
./start-frontend.sh
```

前端会在 `http://localhost:5173` 启动

---

### 方式 2: 使用 Docker Compose（一键启动所有服务）

```bash
cd /Users/cm/Documents/kiro/project

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

**注意**: 使用 Docker Compose 方式，前端会在 `http://localhost` (端口 80) 启动

---

## 🌐 访问地址

启动成功后，可以访问：

### 开发模式（方式 1）
- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **MinIO 控制台**: http://localhost:9001
  - 用户名: `minioadmin`
  - 密码: `minioadmin`

### Docker 模式（方式 2）
- **前端应用**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **MinIO 控制台**: http://localhost:9001

---

## 🔍 验证服务

### 1. 检查后端健康状态

```bash
curl http://localhost:8000/health
```

应该返回：
```json
{
  "status": "healthy",
  "timestamp": "2025-01-XX..."
}
```

### 2. 查看 API 文档

浏览器访问: http://localhost:8000/docs

### 3. 检查数据库连接

```bash
docker exec -it contract_review_postgres psql -U postgres -d contract_review -c "\dt"
```

### 4. 检查 MinIO

浏览器访问: http://localhost:9001
- 用户名: `minioadmin`
- 密码: `minioadmin`

---

## 🛠️ 常用命令

### 查看服务状态

```bash
# Docker Compose 服务
docker-compose ps

# 查看所有容器
docker ps
```

### 查看日志

```bash
# 所有服务日志
docker-compose logs -f

# 特定服务日志
docker-compose logs -f postgres
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 停止服务

```bash
# 停止所有 Docker Compose 服务
docker-compose down

# 停止并删除数据卷（慎用！会删除数据）
docker-compose down -v
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

---

## 🐛 故障排查

### 问题 1: 端口被占用

**错误信息**: `port is already allocated`

**解决方案**:
```bash
# 查看端口占用
lsof -i :8000
lsof -i :5432
lsof -i :6379

# 停止占用端口的进程
kill -9 <PID>
```

### 问题 2: 数据库连接失败

**解决方案**:
```bash
# 检查 PostgreSQL 是否运行
docker ps | grep postgres

# 重启 PostgreSQL
docker-compose restart postgres

# 查看 PostgreSQL 日志
docker-compose logs postgres
```

### 问题 3: 前端无法连接后端

**解决方案**:
1. 确认后端已启动: `curl http://localhost:8000/health`
2. 检查前端 `.env` 文件中的 API 地址
3. 检查浏览器控制台的错误信息

### 问题 4: MinIO 无法访问

**解决方案**:
```bash
# 检查 MinIO 状态
docker-compose logs minio

# 重启 MinIO
docker-compose restart minio
```

---

## 📚 下一步

1. **创建测试账号**: 访问前端，使用钉钉登录
2. **上传测试合同**: 测试文件上传功能
3. **测试 AI 功能**: 尝试 AI 总结和顾问功能
4. **查看 API 文档**: http://localhost:8000/docs

---

## 🔐 关于钉钉回调地址

由于你没有公网 IP 和域名，钉钉 OAuth 回调可能无法正常工作。有以下解决方案：

### 方案 1: 使用内网穿透工具（推荐）

使用 ngrok 或 frp 等工具将本地服务暴露到公网：

```bash
# 使用 ngrok (需要先安装)
ngrok http 3000

# 会得到一个公网地址，如: https://xxxx.ngrok.io
# 将这个地址配置到钉钉开放平台的回调地址
```

### 方案 2: 跳过钉钉登录

如果只是测试其他功能，可以：
1. 直接使用 API 文档测试接口: http://localhost:8000/docs
2. 或者修改代码，添加一个测试用户绕过钉钉登录

### 方案 3: 部署到有公网 IP 的服务器

将应用部署到云服务器（阿里云、腾讯云等），然后配置真实的回调地址。

---

## 💡 提示

- 首次启动可能需要几分钟来下载 Docker 镜像
- 如果修改了 `.env` 文件，需要重启相应的服务
- 开发模式下，代码修改会自动重新加载（热更新）
- 生产部署请参考 `DEPLOYMENT_GUIDE.md`

---

## 📞 需要帮助？

如果遇到问题，可以：
1. 查看日志: `docker-compose logs -f`
2. 查看详细文档: `DEPLOYMENT_GUIDE.md`
3. 检查服务状态: `docker-compose ps`
