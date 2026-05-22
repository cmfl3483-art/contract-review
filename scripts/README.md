# 部署脚本说明

本目录包含合同预审看板系统的部署和管理脚本。

## 📋 脚本列表

### 1. build.sh - 构建脚本
构建前端和后端的 Docker 镜像。

**用法:**
```bash
./scripts/build.sh
```

**功能:**
- 安装前端依赖并构建生产版本
- 检查后端依赖文件
- 构建后端 Docker 镜像
- 构建前端 Docker 镜像

**前置条件:**
- Docker 已安装
- Docker Compose V2 已安装
- Node.js 和 npm 已安装 (用于前端构建)

---

### 2. start.sh - 启动脚本
启动所有服务容器。

**用法:**
```bash
./scripts/start.sh
```

**功能:**
- 启动所有 Docker Compose 服务
- 等待服务启动
- 检查各服务健康状态
- 显示服务访问地址

**启动的服务:**
- PostgreSQL (端口 5432)
- Redis (端口 6379)
- MinIO (端口 9000, 9001)
- 后端 API (端口 8000)
- 前端应用 (端口 80)
- Nginx 反向代理 (端口 80)

---

### 3. stop.sh - 停止脚本
停止所有服务容器。

**用法:**
```bash
./scripts/stop.sh
```

**功能:**
- 显示当前运行的服务
- 询问是否删除数据卷
- 停止所有服务

**选项:**
- 保留数据卷: 数据库、Redis、MinIO 的数据会保留
- 删除数据卷: 所有数据会被清除 (谨慎使用)

---

### 4. restart.sh - 重启脚本
重启服务容器。

**用法:**
```bash
# 重启所有服务
./scripts/restart.sh

# 重启特定服务
./scripts/restart.sh backend
./scripts/restart.sh frontend
./scripts/restart.sh postgres
```

**功能:**
- 重启所有服务或指定服务
- 不会丢失数据

---

### 5. logs.sh - 日志查看脚本
查看服务日志。

**用法:**
```bash
# 查看所有服务日志
./scripts/logs.sh

# 查看特定服务日志
./scripts/logs.sh backend
./scripts/logs.sh frontend
./scripts/logs.sh postgres
./scripts/logs.sh redis
./scripts/logs.sh minio
./scripts/logs.sh nginx

# 查看最后 N 行日志
./scripts/logs.sh backend -n 100

# 实时跟踪日志
./scripts/logs.sh backend --follow
```

**可用服务名称:**
- `backend` - 后端 API 服务
- `frontend` - 前端 Web 服务
- `postgres` - PostgreSQL 数据库
- `redis` - Redis 缓存
- `minio` - MinIO 对象存储
- `nginx` - Nginx 反向代理

---

### 6. status.sh - 状态检查脚本
检查系统运行状态。

**用法:**
```bash
./scripts/status.sh
```

**功能:**
- 显示所有容器状态
- 检查各服务健康状态
- 显示资源使用情况 (CPU、内存、网络)
- 显示数据卷使用情况
- 显示服务访问地址

---

## 🚀 快速开始

### 首次部署

1. **构建镜像**
   ```bash
   ./scripts/build.sh
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置必要的环境变量
   ```

3. **启动服务**
   ```bash
   ./scripts/start.sh
   ```

4. **检查状态**
   ```bash
   ./scripts/status.sh
   ```

5. **访问应用**
   - 前端: http://localhost
   - API 文档: http://localhost:8000/api/docs

### 日常运维

**查看日志**
```bash
# 查看所有日志
./scripts/logs.sh

# 查看后端日志
./scripts/logs.sh backend

# 实时跟踪前端日志
./scripts/logs.sh frontend -f
```

**重启服务**
```bash
# 重启所有服务
./scripts/restart.sh

# 重启后端服务
./scripts/restart.sh backend
```

**停止服务**
```bash
./scripts/stop.sh
```

**检查状态**
```bash
./scripts/status.sh
```

---

## 🔧 故障排查

### 服务无法启动

1. 检查 Docker 是否运行
   ```bash
   docker ps
   ```

2. 查看服务日志
   ```bash
   ./scripts/logs.sh
   ```

3. 检查端口占用
   ```bash
   # macOS/Linux
   lsof -i :80
   lsof -i :8000
   lsof -i :5432
   ```

### 数据库连接失败

1. 检查 PostgreSQL 状态
   ```bash
   docker compose exec postgres pg_isready -U postgres
   ```

2. 查看数据库日志
   ```bash
   ./scripts/logs.sh postgres
   ```

### 前端无法访问

1. 检查 Nginx 状态
   ```bash
   ./scripts/logs.sh nginx
   ```

2. 检查前端构建
   ```bash
   ls -la frontend/dist
   ```

### 后端 API 错误

1. 查看后端日志
   ```bash
   ./scripts/logs.sh backend
   ```

2. 检查环境变量配置
   ```bash
   cat .env
   ```

---

## 📝 注意事项

1. **数据备份**: 在执行 `./scripts/stop.sh` 并选择删除数据卷前，请确保已备份重要数据

2. **端口冲突**: 确保以下端口未被占用:
   - 80 (前端/Nginx)
   - 8000 (后端 API)
   - 5432 (PostgreSQL)
   - 6379 (Redis)
   - 9000, 9001 (MinIO)

3. **资源要求**: 
   - 最小内存: 4GB
   - 推荐内存: 8GB
   - 磁盘空间: 至少 10GB

4. **环境变量**: 生产环境请务必修改 `.env` 文件中的敏感信息:
   - 数据库密码
   - Redis 密码
   - MinIO 密钥
   - JWT 密钥
   - AI API 密钥

---

## 🔐 安全建议

1. **修改默认密码**: 不要在生产环境使用默认密码
2. **使用 HTTPS**: 配置 SSL 证书
3. **限制访问**: 使用防火墙限制端口访问
4. **定期备份**: 定期备份数据库和文件存储
5. **监控日志**: 定期检查日志，及时发现异常

---

## 📚 更多信息

- [项目 README](../README.md)
- [部署文档](../docs/DEPLOYMENT.md)
- [API 文档](http://localhost:8000/api/docs)
- [故障排查指南](../docs/TROUBLESHOOTING.md)
