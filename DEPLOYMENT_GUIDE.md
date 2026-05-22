# 合同预审看板系统 - 部署指南

本文档提供合同预审看板系统的完整部署指南，包括开发环境和生产环境的部署步骤。

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [配置说明](#配置说明)
- [数据备份与恢复](#数据备份与恢复)
- [故障排查](#故障排查)
- [性能优化](#性能优化)
- [安全建议](#安全建议)

---

## 系统要求

### 硬件要求

**最低配置:**
- CPU: 2 核
- 内存: 4GB
- 磁盘: 20GB

**推荐配置:**
- CPU: 4 核
- 内存: 8GB
- 磁盘: 50GB (SSD)

### 软件要求

**必需软件:**
- Docker 20.10+
- Docker Compose V2
- Git

**开发环境额外要求:**
- Node.js 18+
- Python 3.11+
- npm 或 yarn

### 端口要求

确保以下端口未被占用:
- `80` - 前端应用 / Nginx
- `8000` - 后端 API
- `5432` - PostgreSQL
- `6379` - Redis
- `9000` - MinIO API
- `9001` - MinIO Console

---

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd contract-review-system
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
vim .env
```

### 3. 构建和启动

```bash
# 构建 Docker 镜像
./scripts/build.sh

# 启动所有服务
./scripts/start.sh
```

### 4. 访问应用

- 前端应用: http://localhost
- API 文档: http://localhost:8000/api/docs
- MinIO Console: http://localhost:9001

---

## 开发环境部署

### 方式一: 使用 Docker Compose (推荐)

#### 1. 启动基础设施服务

```bash
# 启动 PostgreSQL, Redis, MinIO
./start-services.sh
```

#### 2. 启动后端服务

```bash
# 在新终端窗口
./start-backend.sh
```

#### 3. 启动前端服务

```bash
# 在新终端窗口
./start-frontend.sh
```

### 方式二: 本地开发

#### 1. 启动基础设施

```bash
docker-compose up -d
```

#### 2. 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

---

## 生产环境部署

### 准备工作

#### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo apt install docker-compose-plugin

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER
```

#### 2. 克隆项目

```bash
git clone <repository-url>
cd contract-review-system
```

#### 3. 配置环境变量

```bash
cp .env.example .env
vim .env
```

**重要配置项:**

```bash
# 数据库配置
POSTGRES_PASSWORD=<strong-password>

# Redis 配置
REDIS_PASSWORD=<strong-password>

# MinIO 配置
MINIO_ROOT_USER=<admin-username>
MINIO_ROOT_PASSWORD=<strong-password>

# JWT 配置
JWT_SECRET_KEY=<random-secret-key>

# AI 配置
AI_PROVIDER=deepseek  # 或 custom
AI_API_KEY=<your-api-key>

# 钉钉配置
DINGTALK_APP_KEY=<your-app-key>
DINGTALK_APP_SECRET=<your-app-secret>
```

### 部署步骤

#### 1. 构建镜像

```bash
./scripts/build.sh
```

#### 2. 启动服务

```bash
./scripts/start.sh
```

#### 3. 检查服务状态

```bash
./scripts/status.sh
```

#### 4. 查看日志

```bash
# 查看所有服务日志
./scripts/logs.sh

# 查看特定服务日志
./scripts/logs.sh backend
```

### 配置 HTTPS (可选但推荐)

#### 使用 Let's Encrypt

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

#### 更新 Nginx 配置

编辑 `docker/nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # ... 其他配置
}
```

---

## 配置说明

### 环境变量详解

#### 数据库配置

```bash
# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=contract_review

# 连接池配置
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

#### Redis 配置

```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-password
REDIS_DB=0

# 缓存过期时间 (秒)
CACHE_TTL_CONTRACT_LIST=300
CACHE_TTL_CONTRACT_DETAIL=600
CACHE_TTL_PENDING_COUNT=60
```

#### MinIO 配置

```bash
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET=contract-attachments
MINIO_SECURE=false  # 生产环境设置为 true
```

#### AI 服务配置

```bash
# DeepSeek API
AI_PROVIDER=deepseek
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=your-api-key
AI_MODEL=deepseek-chat

# 自部署模型
# AI_PROVIDER=custom
# AI_API_BASE=http://your-model-server:8000/v1
# AI_MODEL=qwen2.5-7b-instruct
```

#### 钉钉配置

```bash
DINGTALK_APP_KEY=your-app-key
DINGTALK_APP_SECRET=your-app-secret
DINGTALK_REDIRECT_URI=http://your-domain.com/api/auth/dingtalk/callback
```

#### 应用配置

```bash
# 环境
ENVIRONMENT=production  # development, staging, production

# 日志级别
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# CORS 配置
CORS_ORIGINS=http://localhost,http://your-domain.com

# JWT 配置
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440  # 24 小时
```

---

## 数据备份与恢复

### 自动备份

#### 创建备份脚本

```bash
# 执行备份
./scripts/backup.sh
```

备份内容包括:
- PostgreSQL 数据库
- Redis 缓存数据
- MinIO 对象存储
- 环境变量配置

#### 设置定时备份

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点备份
0 2 * * * /path/to/project/scripts/backup.sh >> /var/log/contract-review-backup.log 2>&1

# 添加每周日清理 30 天前的备份
0 3 * * 0 find /path/to/project/backups -name '*.tar.gz' -mtime +30 -delete
```

### 手动备份

#### 备份数据库

```bash
docker compose exec postgres pg_dump -U postgres contract_review > backup.sql
```

#### 备份 MinIO

```bash
docker cp $(docker compose ps -q minio):/data ./minio_backup
```

### 数据恢复

```bash
# 从备份文件恢复
./scripts/restore.sh backups/20250101_120000.tar.gz
```

---

## 故障排查

### 常见问题

#### 1. 服务无法启动

**问题:** Docker 容器启动失败

**解决方案:**
```bash
# 查看容器日志
./scripts/logs.sh

# 检查端口占用
sudo lsof -i :80
sudo lsof -i :8000

# 清理并重新启动
./scripts/stop.sh
docker system prune -f
./scripts/start.sh
```

#### 2. 数据库连接失败

**问题:** 后端无法连接数据库

**解决方案:**
```bash
# 检查 PostgreSQL 状态
docker compose exec postgres pg_isready -U postgres

# 查看数据库日志
./scripts/logs.sh postgres

# 检查环境变量
cat .env | grep POSTGRES
```

#### 3. 前端无法访问

**问题:** 浏览器无法打开前端页面

**解决方案:**
```bash
# 检查 Nginx 状态
./scripts/logs.sh nginx

# 检查前端构建
ls -la frontend/dist

# 重新构建前端
cd frontend && npm run build
```

#### 4. AI 服务不可用

**问题:** AI 总结或顾问功能无法使用

**解决方案:**
```bash
# 检查 AI 配置
cat .env | grep AI_

# 测试 API 连接
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer $AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'

# 查看后端日志
./scripts/logs.sh backend | grep -i "ai"
```

### 性能问题

#### 1. 响应速度慢

```bash
# 检查资源使用
./scripts/status.sh

# 查看慢查询
docker compose exec postgres psql -U postgres -d contract_review -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 清理 Redis 缓存
docker compose exec redis redis-cli FLUSHDB
```

#### 2. 内存不足

```bash
# 查看内存使用
docker stats

# 调整 Docker 内存限制
# 编辑 docker-compose.prod.yml
services:
  backend:
    mem_limit: 2g
  frontend:
    mem_limit: 1g
```

---

## 性能优化

### 数据库优化

#### 1. 添加索引

```sql
-- 合同查询索引
CREATE INDEX idx_contract_status ON contracts(status);
CREATE INDEX idx_contract_created_at ON contracts(created_at DESC);

-- 评审查询索引
CREATE INDEX idx_review_contract_id ON reviews(contract_id);
CREATE INDEX idx_review_status ON reviews(status);
```

#### 2. 连接池配置

```bash
# .env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
```

### Redis 缓存优化

```bash
# 增加缓存时间
CACHE_TTL_CONTRACT_LIST=600  # 10 分钟
CACHE_TTL_CONTRACT_DETAIL=1800  # 30 分钟

# 配置 Redis 内存限制
docker compose exec redis redis-cli CONFIG SET maxmemory 2gb
docker compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 前端优化

#### 1. 启用 Gzip 压缩

编辑 `docker/nginx/nginx.conf`:

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;
```

#### 2. 配置浏览器缓存

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## 安全建议

### 1. 修改默认密码

```bash
# 生成强密码
openssl rand -base64 32

# 更新 .env 文件
POSTGRES_PASSWORD=<generated-password>
REDIS_PASSWORD=<generated-password>
MINIO_SECRET_KEY=<generated-password>
JWT_SECRET_KEY=<generated-password>
```

### 2. 配置防火墙

```bash
# 只允许必要的端口
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 3. 限制数据库访问

```bash
# 只允许本地访问
# docker-compose.prod.yml
services:
  postgres:
    ports:
      - "127.0.0.1:5432:5432"
```

### 4. 启用 SSL/TLS

```bash
# 使用 Let's Encrypt
sudo certbot --nginx -d your-domain.com

# 强制 HTTPS
# nginx.conf
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

### 5. 定期更新

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 更新 Docker 镜像
docker compose pull
./scripts/restart.sh
```

### 6. 监控和日志

```bash
# 设置日志轮转
# /etc/logrotate.d/contract-review
/var/log/contract-review/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
}

# 监控磁盘空间
df -h

# 监控服务状态
./scripts/status.sh
```

---

## 维护建议

### 日常维护

1. **每天**: 检查服务状态和日志
   ```bash
   ./scripts/status.sh
   ./scripts/logs.sh | grep -i error
   ```

2. **每周**: 清理 Docker 资源
   ```bash
   docker system prune -f
   ```

3. **每月**: 检查磁盘空间和备份
   ```bash
   df -h
   ls -lh backups/
   ```

### 升级流程

1. **备份数据**
   ```bash
   ./scripts/backup.sh
   ```

2. **拉取最新代码**
   ```bash
   git pull origin main
   ```

3. **重新构建**
   ```bash
   ./scripts/build.sh
   ```

4. **运行数据库迁移**
   ```bash
   docker compose exec backend alembic upgrade head
   ```

5. **重启服务**
   ```bash
   ./scripts/restart.sh
   ```

6. **验证功能**
   ```bash
   ./scripts/status.sh
   curl http://localhost:8000/health
   ```

---

## 联系支持

如有问题，请联系:
- 技术支持: support@example.com
- 文档: https://docs.example.com
- Issue 跟踪: https://github.com/your-org/contract-review/issues

---

## 附录

### A. 完整的环境变量模板

参考 `.env.example` 文件

### B. 数据库 Schema

参考 `backend/alembic/versions/` 目录

### C. API 文档

访问 http://localhost:8000/api/docs

### D. 架构图

参考 `docs/architecture.md`
