# Docker 环境配置说明

本文档说明如何使用 Docker Compose 启动项目所需的基础设施服务。

## 服务列表

项目使用以下服务：

1. **PostgreSQL 15** - 主数据库
   - 端口: 5432
   - 用户名: postgres
   - 密码: postgres
   - 数据库: contract_review

2. **Redis 7** - 缓存和会话存储
   - 端口: 6379
   - 持久化: AOF (Append Only File)

3. **MinIO** - 对象存储（兼容 S3 API）
   - API 端口: 9000
   - Console 端口: 9001
   - 用户名: minioadmin
   - 密码: minioadmin
   - Bucket: contract-attachments

## 快速开始

### 1. 启动所有服务

```bash
# 在项目根目录执行
docker-compose up -d
```

### 2. 查看服务状态

```bash
docker-compose ps
```

### 3. 查看服务日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f minio
```

### 4. 停止所有服务

```bash
docker-compose down
```

### 5. 停止并删除数据卷（慎用！）

```bash
docker-compose down -v
```

## 服务访问

### PostgreSQL

使用任何 PostgreSQL 客户端连接：

```
Host: localhost
Port: 5432
Database: contract_review
Username: postgres
Password: postgres
```

连接字符串：
```
postgresql://postgres:postgres@localhost:5432/contract_review
```

### Redis

使用 redis-cli 连接：

```bash
redis-cli -h localhost -p 6379
```

或使用 Redis Desktop Manager 等 GUI 工具。

### MinIO

1. **MinIO Console (Web UI)**
   - URL: http://localhost:9001
   - 用户名: minioadmin
   - 密码: minioadmin

2. **MinIO API**
   - Endpoint: http://localhost:9000
   - Access Key: minioadmin
   - Secret Key: minioadmin

## 健康检查

所有服务都配置了健康检查，可以通过以下命令查看：

```bash
docker-compose ps
```

健康状态会显示在 STATUS 列中。

## 数据持久化

数据存储在 Docker 卷中，即使容器停止，数据也不会丢失：

- `postgres_data` - PostgreSQL 数据
- `redis_data` - Redis 数据
- `minio_data` - MinIO 对象存储数据

查看数据卷：

```bash
docker volume ls | grep contract_review
```

## 故障排查

### PostgreSQL 无法启动

1. 检查端口 5432 是否被占用：
   ```bash
   lsof -i :5432
   ```

2. 查看日志：
   ```bash
   docker-compose logs postgres
   ```

### Redis 无法启动

1. 检查端口 6379 是否被占用：
   ```bash
   lsof -i :6379
   ```

2. 查看日志：
   ```bash
   docker-compose logs redis
   ```

### MinIO 无法启动

1. 检查端口 9000 和 9001 是否被占用：
   ```bash
   lsof -i :9000
   lsof -i :9001
   ```

2. 查看日志：
   ```bash
   docker-compose logs minio
   ```

## 开发环境配置

确保后端 `.env` 文件中的配置与 Docker 服务匹配：

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/contract_review

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET=contract-attachments
```

## 生产环境注意事项

⚠️ **重要**: 本配置仅用于开发环境，生产环境需要：

1. 修改所有默认密码
2. 启用 SSL/TLS
3. 配置防火墙规则
4. 使用外部数据卷或云存储
5. 配置备份策略
6. 限制网络访问
7. 使用 secrets 管理敏感信息

## 清理环境

如果需要完全清理环境并重新开始：

```bash
# 停止并删除容器、网络、数据卷
docker-compose down -v

# 删除镜像（可选）
docker rmi postgres:15-alpine redis:7-alpine minio/minio:latest

# 重新启动
docker-compose up -d
```
