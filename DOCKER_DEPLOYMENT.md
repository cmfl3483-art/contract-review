# Docker 部署指南

本文档介绍如何使用 Docker 部署合同预审看板系统。

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [服务管理](#服务管理)
- [故障排查](#故障排查)
- [生产环境部署](#生产环境部署)

## 系统要求

### 硬件要求

- **CPU**: 2 核心或以上
- **内存**: 4GB 或以上
- **磁盘**: 20GB 可用空间

### 软件要求

- **Docker**: 20.10 或以上
- **Docker Compose**: 2.0 或以上
- **操作系统**: Linux, macOS, 或 Windows (with WSL2)

### 检查 Docker 安装

```bash
docker --version
docker-compose --version
```

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd project
```

### 2. 配置环境变量

复制环境变量模板并填写实际值:

```bash
cp .env.production.example .env.production
```

编辑 `.env.production` 文件,填写以下必需配置:

- **钉钉配置**: `DINGTALK_APP_KEY`, `DINGTALK_APP_SECRET`, `DINGTALK_CORP_ID`
- **AI 配置**: `AI_API_KEY` (如果使用 DeepSeek)
- **JWT 密钥**: `SECRET_KEY` (使用强随机字符串)

### 3. 构建镜像

```bash
./docker-build.sh
```

### 4. 启动服务

```bash
./docker-start.sh
```

启动脚本会自动:
- 启动所有服务容器
- 运行数据库迁移
- 初始化 MinIO bucket

### 5. 访问系统

- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **MinIO 控制台**: http://localhost:9001 (用户名: minioadmin, 密码: minioadmin)

## 配置说明

### 服务架构

系统包含以下服务:

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 80 | 前端 Web 应用 (Nginx) |
| backend | 8000 | 后端 API 服务 (FastAPI) |
| celery_worker | - | 异步任务处理 (Celery) |
| postgres | 5432 | PostgreSQL 数据库 |
| redis | 6379 | Redis 缓存 |
| minio | 9000, 9001 | MinIO 对象存储 |

### 环境变量

#### 钉钉配置

```bash
DINGTALK_APP_KEY=your-app-key          # 钉钉应用 Key
DINGTALK_APP_SECRET=your-app-secret    # 钉钉应用 Secret
DINGTALK_CORP_ID=your-corp-id          # 钉钉企业 ID
```

#### AI 配置

**选项 1: 使用 DeepSeek API**

```bash
AI_PROVIDER=deepseek
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=your-deepseek-api-key
AI_MODEL=deepseek-chat
```

**选项 2: 使用自部署模型**

```bash
AI_PROVIDER=custom
AI_API_BASE=http://your-model-server:8000/v1
AI_API_KEY=your-api-key-or-empty
AI_MODEL=qwen2.5-7b-instruct
```

#### 数据库配置

默认使用 Docker Compose 中的 PostgreSQL 服务。如需使用外部数据库:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

#### Redis 配置

默认使用 Docker Compose 中的 Redis 服务。如需使用外部 Redis:

```bash
REDIS_URL=redis://host:6379/0
```

#### MinIO 配置

默认使用 Docker Compose 中的 MinIO 服务。如需使用外部 MinIO 或 S3:

```bash
MINIO_ENDPOINT=your-minio-endpoint:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET=contract-attachments
MINIO_SECURE=true
```

#### JWT 配置

```bash
SECRET_KEY=your-very-secure-secret-key  # 使用强随机字符串
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440        # Token 有效期 (分钟)
```

### Docker Compose 配置

`docker-compose.yml` 文件定义了所有服务的配置。主要配置项:

- **网络**: 所有服务在 `contract_review_network` 网络中通信
- **数据卷**: 数据持久化到 Docker volumes
- **健康检查**: 所有服务都配置了健康检查
- **依赖关系**: 服务按依赖顺序启动

## 服务管理

### 启动服务

```bash
# 启动所有服务
./docker-start.sh

# 或使用 docker-compose
docker-compose up -d
```

### 停止服务

```bash
# 停止所有服务
./docker-stop.sh

# 或使用 docker-compose
docker-compose down
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart backend
```

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 查看所有服务日志
./docker-logs.sh

# 查看特定服务日志
./docker-logs.sh backend
./docker-logs.sh frontend
./docker-logs.sh celery

# 或使用 docker-compose
docker-compose logs -f backend
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh

# 进入数据库容器
docker-compose exec postgres psql -U postgres -d contract_review
```

### 运行数据库迁移

```bash
docker-compose exec backend alembic upgrade head
```

### 创建数据库迁移

```bash
docker-compose exec backend alembic revision --autogenerate -m "migration message"
```

## 故障排查

### 服务无法启动

1. **检查 Docker 是否运行**:
   ```bash
   docker info
   ```

2. **检查端口占用**:
   ```bash
   # macOS/Linux
   lsof -i :80
   lsof -i :8000
   
   # Windows
   netstat -ano | findstr :80
   ```

3. **查看服务日志**:
   ```bash
   docker-compose logs backend
   ```

### 数据库连接失败

1. **检查 PostgreSQL 服务状态**:
   ```bash
   docker-compose ps postgres
   ```

2. **检查数据库健康状态**:
   ```bash
   docker-compose exec postgres pg_isready -U postgres
   ```

3. **查看数据库日志**:
   ```bash
   docker-compose logs postgres
   ```

### Redis 连接失败

1. **检查 Redis 服务状态**:
   ```bash
   docker-compose ps redis
   ```

2. **测试 Redis 连接**:
   ```bash
   docker-compose exec redis redis-cli ping
   ```

### MinIO 连接失败

1. **检查 MinIO 服务状态**:
   ```bash
   docker-compose ps minio
   ```

2. **访问 MinIO 控制台**:
   打开 http://localhost:9001

3. **检查 bucket 是否存在**:
   ```bash
   docker-compose exec backend python -c "
   from app.core.minio_client import minio_client
   print(minio_client.bucket_exists('contract-attachments'))
   "
   ```

### 前端无法访问后端 API

1. **检查 Nginx 配置**:
   ```bash
   docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
   ```

2. **检查后端服务是否运行**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **查看 Nginx 日志**:
   ```bash
   docker-compose logs frontend
   ```

### Celery 任务不执行

1. **检查 Celery Worker 状态**:
   ```bash
   docker-compose ps celery_worker
   ```

2. **查看 Celery 日志**:
   ```bash
   docker-compose logs celery_worker
   ```

3. **检查 Redis 连接**:
   ```bash
   docker-compose exec celery_worker python -c "
   from app.celery_app import celery_app
   print(celery_app.control.inspect().active())
   "
   ```

## 生产环境部署

### 安全配置

1. **修改默认密码**:
   - PostgreSQL: 修改 `POSTGRES_PASSWORD`
   - MinIO: 修改 `MINIO_ROOT_USER` 和 `MINIO_ROOT_PASSWORD`
   - JWT: 使用强随机 `SECRET_KEY`

2. **使用 HTTPS**:
   - 配置 SSL 证书
   - 修改 Nginx 配置启用 HTTPS
   - 设置 `MINIO_SECURE=true`

3. **限制端口暴露**:
   - 移除不必要的端口映射
   - 使用反向代理 (如 Nginx) 统一入口

### 性能优化

1. **调整资源限制**:
   在 `docker-compose.yml` 中添加资源限制:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
           reservations:
             cpus: '1'
             memory: 1G
   ```

2. **启用日志轮转**:
   ```yaml
   services:
     backend:
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
   ```

3. **使用生产级数据库**:
   - 考虑使用外部托管的 PostgreSQL (如 AWS RDS, Azure Database)
   - 配置数据库连接池
   - 启用数据库备份

### 监控和日志

1. **集成监控系统**:
   - Prometheus + Grafana
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - 云服务监控 (AWS CloudWatch, Azure Monitor)

2. **配置告警**:
   - 服务健康检查失败
   - 资源使用率过高
   - 错误日志增加

### 备份和恢复

1. **数据库备份**:
   ```bash
   # 备份
   docker-compose exec postgres pg_dump -U postgres contract_review > backup.sql
   
   # 恢复
   docker-compose exec -T postgres psql -U postgres contract_review < backup.sql
   ```

2. **MinIO 数据备份**:
   ```bash
   # 使用 MinIO Client (mc)
   mc mirror minio/contract-attachments /backup/minio/
   ```

3. **定期备份脚本**:
   创建 cron 任务定期执行备份

### 更新和维护

1. **更新镜像**:
   ```bash
   # 拉取最新代码
   git pull
   
   # 重新构建镜像
   ./docker-build.sh
   
   # 重启服务
   docker-compose up -d
   ```

2. **滚动更新**:
   ```bash
   # 逐个更新服务,减少停机时间
   docker-compose up -d --no-deps --build backend
   docker-compose up -d --no-deps --build frontend
   ```

3. **数据库迁移**:
   ```bash
   # 在更新后运行迁移
   docker-compose exec backend alembic upgrade head
   ```

## 常用命令速查

```bash
# 构建镜像
./docker-build.sh

# 启动服务
./docker-start.sh

# 停止服务
./docker-stop.sh

# 查看日志
./docker-logs.sh [service]

# 查看服务状态
docker-compose ps

# 重启服务
docker-compose restart [service]

# 进入容器
docker-compose exec [service] bash

# 运行数据库迁移
docker-compose exec backend alembic upgrade head

# 清理所有容器和数据
docker-compose down -v

# 查看资源使用
docker stats
```

## 支持

如有问题,请查看:
- [项目 README](./README.md)
- [后端文档](./backend/README.md)
- [前端文档](./frontend/README.md)
- [API 文档](http://localhost:8000/docs)
