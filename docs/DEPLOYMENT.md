# 合同预审看板系统 - 部署文档

## 📋 文档概述

本文档提供合同预审看板系统的完整部署指南，包括环境要求、安装步骤、配置说明和常见问题解答。

**文档版本:** 1.0  
**最后更新:** 2025年1月  
**适用版本:** v1.0.0

---

## 目录

1. [环境要求](#环境要求)
2. [快速开始](#快速开始)
3. [详细安装步骤](#详细安装步骤)
4. [配置说明](#配置说明)
5. [部署验证](#部署验证)
6. [常见问题解答](#常见问题解答)
7. [维护和升级](#维护和升级)
8. [故障排查](#故障排查)

---

## 环境要求

### 硬件要求

#### 最低配置
- **CPU:** 2核心
- **内存:** 4GB RAM
- **磁盘:** 20GB 可用空间
- **网络:** 稳定的互联网连接

#### 推荐配置
- **CPU:** 4核心或更多
- **内存:** 8GB RAM 或更多
- **磁盘:** 50GB SSD
- **网络:** 100Mbps 或更快

### 软件要求

#### 必需软件

| 软件 | 版本要求 | 用途 |
|------|---------|------|
| Docker | 20.10+ | 容器运行环境 |
| Docker Compose | V2.0+ | 多容器编排 |
| Git | 2.0+ | 代码版本控制 |

#### 可选软件（开发环境）

| 软件 | 版本要求 | 用途 |
|------|---------|------|
| Node.js | 18+ | 前端开发 |
| Python | 3.11+ | 后端开发 |
| npm/yarn | 最新版 | 前端包管理 |


### 端口要求

确保以下端口未被占用：

| 端口 | 服务 | 说明 |
|------|------|------|
| 80 | Nginx | 前端应用入口 |
| 8000 | FastAPI | 后端 API 服务 |
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存服务 |
| 9000 | MinIO API | 对象存储 API |
| 9001 | MinIO Console | 对象存储管理界面 |

### 外部服务要求

#### 钉钉开放平台
- 已注册的钉钉企业账号
- 已创建的钉钉应用
- 获取 App Key 和 App Secret
- 配置回调地址

#### AI 服务（可选）
- **选项 1:** DeepSeek API Key
- **选项 2:** 自部署大模型服务（支持 OpenAI 兼容 API）

---

## 快速开始

### 1. 检查环境

```bash
# 检查 Docker 版本
docker --version
# 输出示例: Docker version 24.0.0

# 检查 Docker Compose 版本
docker compose version
# 输出示例: Docker Compose version v2.20.0

# 检查 Git 版本
git --version
# 输出示例: git version 2.40.0
```


### 2. 克隆项目

```bash
# 克隆代码仓库
git clone <repository-url>
cd contract-pre-review

# 查看项目结构
ls -la
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.production.example .env.production

# 编辑配置文件
vim .env.production
# 或使用其他编辑器: nano, code, etc.
```

**必需配置项：**

```bash
# 钉钉配置（必填）
DINGTALK_APP_KEY=your-app-key
DINGTALK_APP_SECRET=your-app-secret
DINGTALK_CORP_ID=your-corp-id

# JWT 密钥（必填，使用强随机字符串）
SECRET_KEY=your-very-secure-random-secret-key

# AI 配置（可选，如需使用 AI 功能）
AI_PROVIDER=deepseek
AI_API_KEY=your-deepseek-api-key
```

### 4. 构建和启动

```bash
# 构建 Docker 镜像
./docker-build.sh

# 启动所有服务
./docker-start.sh
```

### 5. 访问系统

- **前端应用:** http://localhost
- **API 文档:** http://localhost:8000/docs
- **MinIO 控制台:** http://localhost:9001

**默认管理员账号:**
- MinIO: minioadmin / minioadmin


---

## 详细安装步骤

### 步骤 1: 准备服务器环境

#### Linux (Ubuntu/Debian)

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo apt install docker-compose-plugin

# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录以使组权限生效
newgrp docker

# 验证安装
docker --version
docker compose version
```

#### macOS

```bash
# 使用 Homebrew 安装 Docker Desktop
brew install --cask docker

# 启动 Docker Desktop
open /Applications/Docker.app

# 验证安装
docker --version
docker compose version
```

#### Windows

1. 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. 启用 WSL2 支持
3. 重启计算机
4. 打开 PowerShell 验证安装：
   ```powershell
   docker --version
   docker compose version
   ```


### 步骤 2: 获取项目代码

```bash
# 克隆项目
git clone <repository-url>
cd contract-pre-review

# 查看项目结构
tree -L 2
# 或
ls -la
```

**项目目录结构：**

```
contract-pre-review/
├── backend/              # 后端代码
├── frontend/             # 前端代码
├── nginx/                # Nginx 配置
├── scripts/              # 部署脚本
├── docs/                 # 文档
├── docker-compose.yml    # Docker Compose 配置
├── .env.production.example  # 环境变量模板
└── README.md             # 项目说明
```

### 步骤 3: 配置钉钉应用

#### 3.1 创建钉钉应用

1. 登录 [钉钉开放平台](https://open.dingtalk.com/)
2. 进入"应用开发" → "企业内部开发"
3. 点击"创建应用"
4. 填写应用信息：
   - 应用名称：合同预审看板系统
   - 应用描述：企业合同预审协作平台
   - 应用图标：上传应用图标

#### 3.2 配置应用权限

在应用管理页面，配置以下权限：

- **基础权限:**
  - 通讯录只读权限
  - 用户信息读权限
  
- **接口权限:**
  - 获取用户详情
  - 获取部门列表
  - 获取部门用户详情

#### 3.3 配置回调地址

在"开发配置"中设置：

```
回调地址: http://your-domain.com/api/auth/dingtalk/callback
```

**注意:** 开发环境可以使用 `http://localhost/api/auth/dingtalk/callback`

#### 3.4 获取凭证

记录以下信息：
- **App Key (Client ID)**
- **App Secret (Client Secret)**
- **Corp ID (企业 ID)**


### 步骤 4: 配置环境变量

```bash
# 复制环境变量模板
cp .env.production.example .env.production

# 编辑配置文件
vim .env.production
```

**完整配置示例：**

```bash
# ==================== 应用配置 ====================
# 环境: development, staging, production
ENVIRONMENT=production

# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# ==================== 钉钉配置 ====================
DINGTALK_APP_KEY=dingxxxxxxxxxxxxxxxx
DINGTALK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DINGTALK_CORP_ID=dingxxxxxxxxxxxxxxxx
DINGTALK_REDIRECT_URI=http://your-domain.com/api/auth/dingtalk/callback

# ==================== JWT 配置 ====================
# 使用以下命令生成强随机密钥:
# openssl rand -base64 32
SECRET_KEY=your-very-secure-random-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ==================== 数据库配置 ====================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=contract_review

# 数据库连接池
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# ==================== Redis 配置 ====================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0

# 缓存过期时间（秒）
CACHE_TTL_CONTRACT_LIST=300
CACHE_TTL_CONTRACT_DETAIL=600
CACHE_TTL_PENDING_COUNT=60

# ==================== MinIO 配置 ====================
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=your-minio-secret-key
MINIO_BUCKET=contract-attachments
MINIO_SECURE=false

# ==================== AI 配置 ====================
# 选项 1: DeepSeek API
AI_PROVIDER=deepseek
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=your-deepseek-api-key
AI_MODEL=deepseek-chat

# 选项 2: 自部署模型（取消注释以使用）
# AI_PROVIDER=custom
# AI_API_BASE=http://your-model-server:8000/v1
# AI_API_KEY=your-api-key-or-empty
# AI_MODEL=qwen2.5-7b-instruct

# ==================== CORS 配置 ====================
CORS_ORIGINS=http://localhost,http://your-domain.com
```


### 步骤 5: 构建 Docker 镜像

```bash
# 使用构建脚本
./docker-build.sh

# 或手动构建
docker compose build
```

**构建过程说明：**

1. **前端构建** - 编译 React 应用为静态文件
2. **后端构建** - 安装 Python 依赖
3. **Nginx 构建** - 配置反向代理

**预期输出：**

```
[+] Building 120.5s (45/45) FINISHED
 => [frontend internal] load build definition
 => [backend internal] load build definition
 => [nginx internal] load build definition
 ...
 => => naming to docker.io/library/contract-pre-review-frontend
 => => naming to docker.io/library/contract-pre-review-backend
 => => naming to docker.io/library/contract-pre-review-nginx
```

### 步骤 6: 启动服务

```bash
# 使用启动脚本
./docker-start.sh

# 或手动启动
docker compose up -d
```

**启动顺序：**

1. PostgreSQL 数据库
2. Redis 缓存
3. MinIO 对象存储
4. 后端 API 服务
5. Celery 任务队列
6. 前端 Nginx 服务

**查看启动状态：**

```bash
# 查看所有容器状态
docker compose ps

# 预期输出:
NAME                    STATUS              PORTS
postgres                Up (healthy)        5432/tcp
redis                   Up (healthy)        6379/tcp
minio                   Up (healthy)        9000-9001/tcp
backend                 Up (healthy)        8000/tcp
celery_worker           Up                  -
frontend                Up (healthy)        80/tcp
```


### 步骤 7: 初始化数据库

```bash
# 运行数据库迁移
docker compose exec backend alembic upgrade head

# 预期输出:
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> 001_initial
INFO  [alembic.runtime.migration] Running upgrade 001_initial -> 002_add_indexes
```

### 步骤 8: 验证部署

```bash
# 检查服务健康状态
curl http://localhost:8000/health

# 预期输出:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "minio": "connected"
}

# 访问前端应用
curl -I http://localhost

# 预期输出:
HTTP/1.1 200 OK
Server: nginx/1.25.0
Content-Type: text/html
```

---

## 配置说明

### 核心配置项详解

#### 1. 钉钉配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| DINGTALK_APP_KEY | 钉钉应用 Key | dingxxxxxxxx |
| DINGTALK_APP_SECRET | 钉钉应用密钥 | xxxxxxxxxxxxxxxx |
| DINGTALK_CORP_ID | 企业 ID | dingxxxxxxxx |
| DINGTALK_REDIRECT_URI | 回调地址 | http://domain.com/api/auth/dingtalk/callback |

**获取方式：** 钉钉开放平台 → 应用管理 → 应用详情


#### 2. JWT 配置

| 配置项 | 说明 | 推荐值 |
|--------|------|--------|
| SECRET_KEY | JWT 签名密钥 | 使用 `openssl rand -base64 32` 生成 |
| ALGORITHM | 加密算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token 有效期（分钟） | 1440 (24小时) |

**安全建议：**
- 生产环境必须使用强随机密钥
- 定期轮换密钥
- 不要在代码中硬编码密钥

#### 3. 数据库配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| POSTGRES_HOST | 数据库主机 | postgres |
| POSTGRES_PORT | 数据库端口 | 5432 |
| POSTGRES_USER | 数据库用户 | postgres |
| POSTGRES_PASSWORD | 数据库密码 | 需修改 |
| POSTGRES_DB | 数据库名称 | contract_review |
| DB_POOL_SIZE | 连接池大小 | 20 |
| DB_MAX_OVERFLOW | 最大溢出连接 | 10 |

**性能调优：**
- 根据并发量调整连接池大小
- 监控连接池使用情况
- 考虑使用外部托管数据库（生产环境）

#### 4. Redis 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| REDIS_HOST | Redis 主机 | redis |
| REDIS_PORT | Redis 端口 | 6379 |
| REDIS_PASSWORD | Redis 密码 | 需设置 |
| REDIS_DB | 数据库编号 | 0 |
| CACHE_TTL_* | 缓存过期时间 | 见配置文件 |

**缓存策略：**
- 合同列表缓存：5分钟
- 合同详情缓存：10分钟
- 待办数量缓存：1分钟
- AI 总结缓存：30分钟


#### 5. MinIO 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| MINIO_ENDPOINT | MinIO 端点 | minio:9000 |
| MINIO_ACCESS_KEY | 访问密钥 | minioadmin |
| MINIO_SECRET_KEY | 密钥 | 需修改 |
| MINIO_BUCKET | 存储桶名称 | contract-attachments |
| MINIO_SECURE | 是否使用 HTTPS | false |

**文件存储：**
- 支持的文件类型：PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX
- 单文件大小限制：20MB
- 自动版本管理

#### 6. AI 配置

**选项 1: DeepSeek API**

| 配置项 | 说明 | 示例 |
|--------|------|------|
| AI_PROVIDER | AI 提供商 | deepseek |
| AI_API_BASE | API 地址 | https://api.deepseek.com/v1 |
| AI_API_KEY | API 密钥 | sk-xxxxxxxx |
| AI_MODEL | 模型名称 | deepseek-chat |

**选项 2: 自部署模型**

| 配置项 | 说明 | 示例 |
|--------|------|------|
| AI_PROVIDER | AI 提供商 | custom |
| AI_API_BASE | API 地址 | http://your-server:8000/v1 |
| AI_API_KEY | API 密钥 | 可选 |
| AI_MODEL | 模型名称 | qwen2.5-7b-instruct |

**AI 功能：**
- 智能总结审批进度
- 提取关键问题和风险项
- AI 合同顾问问答

### 高级配置

#### 日志配置

```bash
# 日志级别
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# 日志格式
LOG_FORMAT=json  # json, text

# 日志输出
LOG_OUTPUT=stdout  # stdout, file
```


#### CORS 配置

```bash
# 允许的源（多个用逗号分隔）
CORS_ORIGINS=http://localhost,http://your-domain.com,https://your-domain.com

# 允许的方法
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS

# 允许的头
CORS_HEADERS=*
```

#### 文件上传配置

```bash
# 最大文件大小（字节）
MAX_FILE_SIZE=20971520  # 20MB

# 允许的文件类型
ALLOWED_FILE_TYPES=pdf,doc,docx,ppt,pptx,xls,xlsx

# 上传临时目录
UPLOAD_TMP_DIR=/tmp/uploads
```

---

## 部署验证

### 1. 服务健康检查

```bash
# 检查所有容器状态
docker compose ps

# 检查后端健康状态
curl http://localhost:8000/health

# 检查前端访问
curl -I http://localhost

# 检查 MinIO 状态
curl http://localhost:9000/minio/health/live
```

### 2. 功能测试

#### 2.1 测试钉钉登录

1. 访问 http://localhost
2. 点击"钉钉登录"按钮
3. 扫码或输入账号密码登录
4. 验证是否成功跳转回应用

#### 2.2 测试合同创建

1. 登录后点击"发起合同预审"
2. 填写合同信息
3. 选择评审人
4. 上传附件
5. 提交并验证是否创建成功


#### 2.3 测试文件上传

```bash
# 使用 curl 测试文件上传
curl -X POST http://localhost:8000/api/contracts/{contract_id}/attachments \
  -H "Authorization: Bearer {your_token}" \
  -F "file=@test.pdf"
```

#### 2.4 测试 AI 功能

1. 在合同详情页查看 AI 智能总结
2. 在 AI 顾问面板输入问题
3. 验证 AI 响应是否正常

### 3. 性能测试

```bash
# 使用 Apache Bench 进行压力测试
ab -n 1000 -c 100 http://localhost/

# 查看响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://localhost/api/health
```

**curl-format.txt 内容：**

```
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_appconnect:  %{time_appconnect}\n
time_pretransfer:  %{time_pretransfer}\n
time_redirect:  %{time_redirect}\n
time_starttransfer:  %{time_starttransfer}\n
----------\n
time_total:  %{time_total}\n
```

### 4. 日志检查

```bash
# 查看所有服务日志
./docker-logs.sh

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres

# 查看错误日志
docker compose logs | grep -i error
docker compose logs | grep -i exception
```

---

## 常见问题解答

### Q1: Docker 容器无法启动怎么办？

**A:** 按以下步骤排查：

```bash
# 1. 检查端口占用
lsof -i :80
lsof -i :8000
lsof -i :5432

# 2. 查看容器日志
docker compose logs [service_name]

# 3. 检查 Docker 资源
docker system df

# 4. 清理并重启
docker compose down
docker system prune -f
docker compose up -d
```


### Q2: 数据库连接失败怎么办？

**A:** 检查以下几点：

```bash
# 1. 确认 PostgreSQL 容器运行正常
docker compose ps postgres

# 2. 测试数据库连接
docker compose exec postgres pg_isready -U postgres

# 3. 检查数据库日志
docker compose logs postgres

# 4. 验证环境变量配置
cat .env.production | grep POSTGRES

# 5. 手动连接测试
docker compose exec postgres psql -U postgres -d contract_review
```

### Q3: 前端页面无法访问怎么办？

**A:** 排查步骤：

```bash
# 1. 检查 Nginx 容器状态
docker compose ps frontend

# 2. 查看 Nginx 日志
docker compose logs frontend

# 3. 测试后端 API
curl http://localhost:8000/health

# 4. 检查 Nginx 配置
docker compose exec frontend cat /etc/nginx/nginx.conf

# 5. 重启 Nginx
docker compose restart frontend
```

### Q4: 文件上传失败怎么办？

**A:** 检查以下配置：

```bash
# 1. 检查 MinIO 服务状态
docker compose ps minio

# 2. 访问 MinIO 控制台
open http://localhost:9001

# 3. 检查 bucket 是否存在
docker compose exec backend python -c "
from app.core.minio_client import minio_client
print(minio_client.bucket_exists('contract-attachments'))
"

# 4. 检查文件大小限制
# 确保文件小于 20MB

# 5. 查看后端日志
docker compose logs backend | grep -i upload
```


### Q5: AI 功能不可用怎么办？

**A:** 检查 AI 配置：

```bash
# 1. 验证 AI 配置
cat .env.production | grep AI_

# 2. 测试 DeepSeek API 连接
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer $AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'

# 3. 查看后端日志中的 AI 相关错误
docker compose logs backend | grep -i "ai\|deepseek"

# 4. 检查 Celery 任务队列
docker compose logs celery_worker
```

### Q6: 钉钉登录失败怎么办？

**A:** 验证钉钉配置：

```bash
# 1. 检查钉钉配置
cat .env.production | grep DINGTALK

# 2. 验证回调地址配置
# 确保钉钉开放平台配置的回调地址与 DINGTALK_REDIRECT_URI 一致

# 3. 检查应用权限
# 登录钉钉开放平台，确认应用已获得必要权限

# 4. 查看认证日志
docker compose logs backend | grep -i "dingtalk\|auth"
```

### Q7: Redis 缓存不生效怎么办？

**A:** 检查 Redis 配置：

```bash
# 1. 检查 Redis 服务状态
docker compose ps redis

# 2. 测试 Redis 连接
docker compose exec redis redis-cli ping
# 应返回: PONG

# 3. 查看缓存键
docker compose exec redis redis-cli KEYS "*"

# 4. 清空缓存重试
docker compose exec redis redis-cli FLUSHDB

# 5. 检查 Redis 日志
docker compose logs redis
```

### Q8: 如何修改默认端口？

**A:** 修改 docker-compose.yml：

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 将前端端口改为 8080
  
  backend:
    ports:
      - "8001:8000"  # 将后端端口改为 8001
```

然后重启服务：

```bash
docker compose down
docker compose up -d
```


### Q9: 如何查看系统资源使用情况？

**A:** 使用以下命令：

```bash
# 查看所有容器资源使用
docker stats

# 查看磁盘使用
docker system df

# 查看特定容器资源
docker stats contract_review_backend

# 查看数据卷大小
docker volume ls
du -sh /var/lib/docker/volumes/*
```

### Q10: 如何备份和恢复数据？

**A:** 使用备份脚本：

```bash
# 备份所有数据
./scripts/backup.sh

# 备份文件位置
ls -lh backups/

# 恢复数据
./scripts/restore.sh backups/20250101_120000.tar.gz
```

**手动备份：**

```bash
# 备份数据库
docker compose exec postgres pg_dump -U postgres contract_review > backup.sql

# 备份 MinIO 数据
docker cp $(docker compose ps -q minio):/data ./minio_backup

# 恢复数据库
docker compose exec -T postgres psql -U postgres contract_review < backup.sql
```

---

## 维护和升级

### 日常维护

#### 1. 查看服务状态

```bash
# 每天检查
./scripts/status.sh

# 或使用 docker compose
docker compose ps
```

#### 2. 查看日志

```bash
# 查看所有日志
./scripts/logs.sh

# 查看错误日志
docker compose logs | grep -i error

# 查看最近 100 行日志
docker compose logs --tail=100
```


#### 3. 清理资源

```bash
# 清理未使用的镜像
docker image prune -f

# 清理未使用的容器
docker container prune -f

# 清理未使用的网络
docker network prune -f

# 清理所有未使用资源
docker system prune -f

# 清理所有资源（包括数据卷，慎用！）
docker system prune -a --volumes
```

#### 4. 监控磁盘空间

```bash
# 检查磁盘使用
df -h

# 检查 Docker 磁盘使用
docker system df

# 检查日志文件大小
du -sh /var/lib/docker/containers/*/*-json.log
```

### 系统升级

#### 升级流程

```bash
# 1. 备份数据
./scripts/backup.sh

# 2. 拉取最新代码
git pull origin main

# 3. 停止服务
./scripts/stop.sh

# 4. 重新构建镜像
./docker-build.sh

# 5. 运行数据库迁移
docker compose up -d postgres redis minio
docker compose exec backend alembic upgrade head

# 6. 启动所有服务
./scripts/start.sh

# 7. 验证升级
curl http://localhost:8000/health
```

#### 回滚流程

```bash
# 1. 停止服务
./scripts/stop.sh

# 2. 切换到旧版本
git checkout <previous-version-tag>

# 3. 恢复数据
./scripts/restore.sh backups/latest.tar.gz

# 4. 重新构建和启动
./docker-build.sh
./scripts/start.sh
```


### 定期任务

#### 设置自动备份

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点备份
0 2 * * * /path/to/project/scripts/backup.sh >> /var/log/contract-review-backup.log 2>&1

# 添加每周日清理 30 天前的备份
0 3 * * 0 find /path/to/project/backups -name '*.tar.gz' -mtime +30 -delete

# 添加每天检查服务状态
0 */6 * * * /path/to/project/scripts/status.sh >> /var/log/contract-review-status.log 2>&1
```

#### 日志轮转

创建 `/etc/logrotate.d/contract-review`：

```
/var/log/contract-review/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker compose restart frontend backend
    endscript
}
```

---

## 故障排查

### 常见故障场景

#### 场景 1: 服务启动失败

**症状：** 容器无法启动或频繁重启

**排查步骤：**

```bash
# 1. 查看容器状态
docker compose ps

# 2. 查看失败容器的日志
docker compose logs [failed_service]

# 3. 检查端口占用
sudo lsof -i :[port]

# 4. 检查资源限制
docker stats

# 5. 检查配置文件
cat .env.production
```

**常见原因：**
- 端口被占用
- 环境变量配置错误
- 资源不足（内存、磁盘）
- 依赖服务未就绪


#### 场景 2: 数据库性能下降

**症状：** API 响应变慢，数据库查询超时

**排查步骤：**

```bash
# 1. 检查数据库连接数
docker compose exec postgres psql -U postgres -d contract_review -c "SELECT count(*) FROM pg_stat_activity;"

# 2. 查看慢查询
docker compose exec postgres psql -U postgres -d contract_review -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# 3. 检查索引使用情况
docker compose exec postgres psql -U postgres -d contract_review -c "SELECT schemaname, tablename, indexname FROM pg_indexes WHERE schemaname = 'public';"

# 4. 分析表大小
docker compose exec postgres psql -U postgres -d contract_review -c "SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

**优化建议：**
- 增加数据库连接池大小
- 添加缺失的索引
- 定期执行 VACUUM
- 考虑使用外部托管数据库

#### 场景 3: 内存不足

**症状：** 容器被 OOM Killer 杀死

**排查步骤：**

```bash
# 1. 查看系统内存
free -h

# 2. 查看容器内存使用
docker stats --no-stream

# 3. 查看系统日志
dmesg | grep -i "out of memory"

# 4. 检查 Docker 内存限制
docker inspect [container_name] | grep -i memory
```

**解决方案：**

```yaml
# 在 docker-compose.yml 中设置内存限制
services:
  backend:
    mem_limit: 2g
    mem_reservation: 1g
  
  postgres:
    mem_limit: 1g
    mem_reservation: 512m
```


#### 场景 4: 磁盘空间不足

**症状：** 容器无法写入数据，日志显示磁盘满

**排查步骤：**

```bash
# 1. 检查磁盘使用
df -h

# 2. 查找大文件
du -sh /* | sort -rh | head -10

# 3. 检查 Docker 磁盘使用
docker system df

# 4. 查找大日志文件
find /var/lib/docker/containers -name "*-json.log" -exec ls -lh {} \; | sort -k5 -rh | head -10
```

**清理方案：**

```bash
# 清理 Docker 资源
docker system prune -a -f

# 清理日志文件
truncate -s 0 /var/lib/docker/containers/*/*-json.log

# 清理旧备份
find /path/to/backups -mtime +30 -delete

# 配置日志轮转（见上文）
```

#### 场景 5: WebSocket 连接失败

**症状：** 实时更新不工作，前端无法建立 WebSocket 连接

**排查步骤：**

```bash
# 1. 检查 Nginx WebSocket 配置
docker compose exec frontend cat /etc/nginx/nginx.conf | grep -A 10 "socket.io"

# 2. 测试 WebSocket 连接
# 使用浏览器开发者工具 Network -> WS 标签

# 3. 查看后端 Socket.IO 日志
docker compose logs backend | grep -i "socket\|websocket"

# 4. 检查防火墙规则
sudo iptables -L -n | grep 8000
```

**常见原因：**
- Nginx 未正确配置 WebSocket 代理
- 防火墙阻止 WebSocket 连接
- 后端 Socket.IO 服务未启动
- CORS 配置问题


### 诊断工具

#### 健康检查脚本

创建 `scripts/health-check.sh`：

```bash
#!/bin/bash

echo "=== 合同预审看板系统健康检查 ==="
echo ""

# 检查容器状态
echo "1. 容器状态:"
docker compose ps

# 检查后端健康
echo ""
echo "2. 后端健康状态:"
curl -s http://localhost:8000/health | jq .

# 检查前端访问
echo ""
echo "3. 前端访问:"
curl -I http://localhost 2>&1 | head -1

# 检查数据库连接
echo ""
echo "4. 数据库连接:"
docker compose exec -T postgres pg_isready -U postgres

# 检查 Redis 连接
echo ""
echo "5. Redis 连接:"
docker compose exec -T redis redis-cli ping

# 检查 MinIO 状态
echo ""
echo "6. MinIO 状态:"
curl -s http://localhost:9000/minio/health/live

# 检查磁盘空间
echo ""
echo "7. 磁盘空间:"
df -h | grep -E "Filesystem|/$"

# 检查内存使用
echo ""
echo "8. 内存使用:"
free -h

echo ""
echo "=== 健康检查完成 ==="
```

使用方法：

```bash
chmod +x scripts/health-check.sh
./scripts/health-check.sh
```

---

## 安全建议

### 1. 修改默认密码

```bash
# 生成强密码
openssl rand -base64 32

# 更新所有默认密码
# - PostgreSQL: POSTGRES_PASSWORD
# - Redis: REDIS_PASSWORD
# - MinIO: MINIO_SECRET_KEY
# - JWT: SECRET_KEY
```


### 2. 配置防火墙

```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 3. 启用 HTTPS

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

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # ... 其他配置
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 4. 限制数据库访问

```yaml
# docker-compose.yml
services:
  postgres:
    ports:
      - "127.0.0.1:5432:5432"  # 只允许本地访问
```

### 5. 定期更新

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 更新 Docker 镜像
docker compose pull
docker compose up -d

# 更新应用代码
git pull origin main
./docker-build.sh
./scripts/restart.sh
```


### 6. 备份策略

```bash
# 设置自动备份
crontab -e

# 每天备份
0 2 * * * /path/to/project/scripts/backup.sh

# 每周清理旧备份
0 3 * * 0 find /path/to/backups -mtime +30 -delete
```

### 7. 监控和告警

推荐使用以下监控方案：

- **Prometheus + Grafana** - 指标监控
- **ELK Stack** - 日志分析
- **Uptime Kuma** - 服务可用性监控
- **Sentry** - 错误追踪

---

## 性能优化

### 1. 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_contract_status ON contracts(status);
CREATE INDEX idx_contract_created_at ON contracts(created_at DESC);
CREATE INDEX idx_review_contract_id ON reviews(contract_id);

-- 定期维护
VACUUM ANALYZE;
REINDEX DATABASE contract_review;
```

### 2. Redis 优化

```bash
# 配置 Redis 内存限制
docker compose exec redis redis-cli CONFIG SET maxmemory 2gb
docker compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 启用持久化
docker compose exec redis redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

### 3. Nginx 优化

```nginx
# 启用 Gzip 压缩
gzip on;
gzip_vary on;
gzip_comp_level 6;
gzip_types text/plain text/css text/javascript application/json;

# 配置缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# 连接优化
keepalive_timeout 65;
keepalive_requests 100;
```


### 4. 应用优化

```bash
# 调整连接池大小
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20

# 调整缓存时间
CACHE_TTL_CONTRACT_LIST=600
CACHE_TTL_CONTRACT_DETAIL=1800

# 启用 Celery 并发
CELERY_WORKER_CONCURRENCY=4
```

---

## 附录

### A. 环境变量完整列表

参考 `.env.production.example` 文件

### B. API 文档

访问 http://localhost:8000/docs 查看完整 API 文档

### C. 数据库 Schema

参考 `backend/alembic/versions/` 目录中的迁移文件

### D. 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (端口 80)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  静态文件    │  │  API 代理    │  │  WebSocket   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                FastAPI 后端 (端口 8000)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  REST API    │  │  WebSocket   │  │  认证服务    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │    MinIO     │
│  (端口 5432) │  │  (端口 6379) │  │  (端口 9000) │
└──────────────┘  └──────────────┘  └──────────────┘
```


### E. 常用命令速查表

| 操作 | 命令 |
|------|------|
| 构建镜像 | `./docker-build.sh` |
| 启动服务 | `./docker-start.sh` |
| 停止服务 | `./docker-stop.sh` |
| 查看状态 | `docker compose ps` |
| 查看日志 | `./docker-logs.sh [service]` |
| 进入容器 | `docker compose exec [service] bash` |
| 数据库迁移 | `docker compose exec backend alembic upgrade head` |
| 备份数据 | `./scripts/backup.sh` |
| 恢复数据 | `./scripts/restore.sh [backup_file]` |
| 健康检查 | `curl http://localhost:8000/health` |
| 清理资源 | `docker system prune -f` |
| 重启服务 | `docker compose restart [service]` |

### F. 端口映射表

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|---------|---------|------|
| Nginx | 80 | 80 | 前端入口 |
| FastAPI | 8000 | 8000 | 后端 API |
| PostgreSQL | 5432 | 5432 | 数据库 |
| Redis | 6379 | 6379 | 缓存 |
| MinIO API | 9000 | 9000 | 对象存储 API |
| MinIO Console | 9001 | 9001 | 对象存储管理 |

### G. 相关文档链接

- [项目 README](../README.md)
- [Docker 部署指南](../DOCKER_DEPLOYMENT.md)
- [Nginx 配置说明](../NGINX_SETUP.md)
- [后端开发文档](../backend/README.md)
- [前端开发文档](../frontend/README.md)
- [API 文档](http://localhost:8000/docs)

---

## 联系支持

如有问题或需要帮助，请通过以下方式联系：

- **技术支持邮箱:** support@example.com
- **项目主页:** https://github.com/your-org/contract-review
- **问题反馈:** https://github.com/your-org/contract-review/issues
- **文档中心:** https://docs.example.com

---

## 更新日志

### v1.0.0 (2025-01-XX)

- ✅ 初始版本发布
- ✅ 完整的部署文档
- ✅ Docker Compose 配置
- ✅ 钉钉登录集成
- ✅ AI 功能支持
- ✅ 文件上传和版本管理
- ✅ 实时通信（WebSocket）

---

**文档结束**

