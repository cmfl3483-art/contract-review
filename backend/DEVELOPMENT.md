# 开发环境配置指南

Development Environment Setup Guide

本文档详细说明如何配置和启动合同预审看板系统的开发环境。

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [常见问题](#常见问题)
- [开发工具](#开发工具)

## 系统要求

### 必需软件

- **Python**: 3.11 或更高版本
- **PostgreSQL**: 15 或更高版本
- **Redis**: 7 或更高版本
- **Node.js**: 18 或更高版本 (前端开发)

### 可选软件

- **MinIO**: 用于本地文件存储测试
- **Docker**: 用于容器化部署
- **Poetry**: Python 依赖管理工具 (推荐)

## 快速开始

### 1. 使用 Docker Compose (推荐)

最简单的方式是使用 Docker Compose 启动所有依赖服务:

```bash
# 在项目根目录
cd /path/to/project

# 启动所有服务 (PostgreSQL, Redis, MinIO)
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 2. 安装 Python 依赖

```bash
cd backend

# 方式 1: 使用 Poetry (推荐)
poetry install
poetry shell

# 方式 2: 使用 pip
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

**最小配置** (使用 Docker Compose 默认值):

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/contract_review
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
SECRET_KEY=your-secret-key-here
```

### 4. 初始化数据库

```bash
# 创建数据库迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 5. 启动开发服务器

```bash
# 启动 FastAPI 服务 (热重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/api/docs 查看 API 文档。

## 详细配置

### 环境变量说明

#### 基础配置

```env
# 项目名称
PROJECT_NAME="合同预审看板系统"

# 环境: development, staging, production
ENVIRONMENT=development

# 调试模式 (生产环境设置为 false)
DEBUG=true
```

#### 数据库配置

```env
# PostgreSQL 连接字符串
# 格式: postgresql+asyncpg://用户名:密码@主机:端口/数据库名
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/contract_review

# 是否打印 SQL 语句 (调试用)
DATABASE_ECHO=false
```

**创建数据库**:

```bash
# 使用 psql
psql -U postgres
CREATE DATABASE contract_review;
\q

# 或使用 Docker
docker exec -it postgres psql -U postgres -c "CREATE DATABASE contract_review;"
```

#### Redis 配置

```env
# Redis 连接字符串
# 格式: redis://主机:端口/数据库编号
REDIS_URL=redis://localhost:6379/0

# 缓存过期时间 (秒)
REDIS_CACHE_TTL=300
```

**测试 Redis 连接**:

```bash
redis-cli ping
# 应返回: PONG
```

#### MinIO 配置

```env
# MinIO 服务地址 (不包含 http://)
MINIO_ENDPOINT=localhost:9000

# MinIO 访问凭证
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# 是否使用 HTTPS
MINIO_SECURE=false

# 存储桶名称
MINIO_BUCKET=contract-attachments
```

**访问 MinIO 控制台**:

- URL: http://localhost:9001
- 用户名: minioadmin
- 密码: minioadmin

#### JWT 配置

```env
# JWT 密钥 (生产环境必须使用强随机字符串)
SECRET_KEY=your-secret-key-change-in-production

# 加密算法
ALGORITHM=HS256

# Token 过期时间 (分钟)
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

**生成安全的 SECRET_KEY**:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 钉钉配置

```env
# 钉钉应用凭证 (从钉钉开放平台获取)
DINGTALK_APP_KEY=your-dingtalk-app-key
DINGTALK_APP_SECRET=your-dingtalk-app-secret

# 钉钉授权回调地址
DINGTALK_REDIRECT_URI=http://localhost:3000/auth/callback
```

**获取钉钉凭证**:

1. 访问 [钉钉开放平台](https://open-dev.dingtalk.com/)
2. 创建应用
3. 获取 AppKey 和 AppSecret
4. 配置回调地址

#### AI 配置

```env
# AI 服务提供商: deepseek 或 custom
AI_PROVIDER=deepseek

# DeepSeek API 配置
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=your-deepseek-api-key
AI_MODEL=deepseek-chat

# AI 请求超时时间 (秒)
AI_TIMEOUT=30
```

**使用自部署模型** (OpenAI 兼容 API):

```env
AI_PROVIDER=custom
AI_API_BASE=http://localhost:8000/v1
AI_API_KEY=your-api-key-or-empty
AI_MODEL=qwen2.5-7b-instruct
```

#### CORS 配置

```env
# 允许的跨域源 (多个源用逗号分隔)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**添加新的前端地址**:

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://192.168.1.100:3000
```

#### 日志配置

```env
# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# 日志文件路径
LOG_FILE=logs/app.log
```

### 数据库迁移

#### 创建新迁移

```bash
# 自动生成迁移脚本
alembic revision --autogenerate -m "描述你的更改"

# 手动创建迁移脚本
alembic revision -m "描述你的更改"
```

#### 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到特定版本
alembic upgrade <revision_id>

# 降级一个版本
alembic downgrade -1

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

### Celery 任务队列

#### 启动 Celery Worker

```bash
# 启动 worker
celery -A app.celery_app worker --loglevel=info

# 启动 worker (Windows)
celery -A app.celery_app worker --loglevel=info --pool=solo

# 启动 beat (定时任务)
celery -A app.celery_app beat --loglevel=info
```

#### 监控 Celery

```bash
# 查看活跃任务
celery -A app.celery_app inspect active

# 查看注册的任务
celery -A app.celery_app inspect registered

# 查看统计信息
celery -A app.celery_app inspect stats
```

## 常见问题

### 1. 数据库连接失败

**错误**: `could not connect to server: Connection refused`

**解决方案**:

```bash
# 检查 PostgreSQL 是否运行
pg_isready -h localhost -p 5432

# 启动 PostgreSQL (Docker)
docker-compose up -d postgres

# 启动 PostgreSQL (系统服务)
sudo systemctl start postgresql  # Linux
brew services start postgresql@15  # Mac
```

### 2. Redis 连接失败

**错误**: `Error connecting to Redis`

**解决方案**:

```bash
# 检查 Redis 是否运行
redis-cli ping

# 启动 Redis (Docker)
docker-compose up -d redis

# 启动 Redis (系统服务)
sudo systemctl start redis  # Linux
brew services start redis  # Mac
```

### 3. MinIO 连接失败

**错误**: `MinIO connection failed`

**解决方案**:

```bash
# 启动 MinIO (Docker)
docker-compose up -d minio

# 检查 MinIO 是否运行
curl http://localhost:9000/minio/health/live
```

### 4. 端口被占用

**错误**: `Address already in use`

**解决方案**:

```bash
# 查找占用端口的进程
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# 杀死进程
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows

# 或使用其他端口
uvicorn app.main:app --reload --port 8001
```

### 5. 依赖安装失败

**错误**: `Failed building wheel for ...`

**解决方案**:

```bash
# 升级 pip
pip install --upgrade pip setuptools wheel

# 安装系统依赖 (Ubuntu/Debian)
sudo apt-get install python3-dev libpq-dev

# 安装系统依赖 (Mac)
brew install postgresql
```

### 6. Alembic 迁移冲突

**错误**: `Multiple head revisions are present`

**解决方案**:

```bash
# 查看所有头版本
alembic heads

# 合并头版本
alembic merge heads -m "Merge migrations"

# 执行合并后的迁移
alembic upgrade head
```

## 开发工具

### 代码格式化

```bash
# 使用 Black 格式化代码
black app/

# 使用 isort 排序导入
isort app/

# 使用 autopep8
autopep8 --in-place --recursive app/
```

### 代码检查

```bash
# 使用 flake8 检查代码风格
flake8 app/

# 使用 pylint 检查代码质量
pylint app/

# 使用 mypy 检查类型
mypy app/
```

### 测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_contracts.py

# 运行特定测试函数
pytest tests/test_contracts.py::test_create_contract

# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### API 测试

```bash
# 使用 httpie
http GET http://localhost:8000/health

# 使用 curl
curl http://localhost:8000/health

# 使用 Postman
# 导入 OpenAPI 规范: http://localhost:8000/api/openapi.json
```

### 数据库管理

```bash
# 使用 psql 连接数据库
psql -U postgres -d contract_review

# 常用 SQL 命令
\dt  # 列出所有表
\d table_name  # 查看表结构
\q  # 退出

# 使用 pgAdmin (图形界面)
# 下载: https://www.pgadmin.org/download/
```

### Redis 管理

```bash
# 使用 redis-cli
redis-cli

# 常用命令
KEYS *  # 列出所有键
GET key_name  # 获取键值
DEL key_name  # 删除键
FLUSHDB  # 清空当前数据库
QUIT  # 退出

# 使用 RedisInsight (图形界面)
# 下载: https://redis.com/redis-enterprise/redis-insight/
```

## 性能优化

### 数据库优化

```bash
# 分析查询性能
EXPLAIN ANALYZE SELECT * FROM contracts WHERE status = 'progress';

# 创建索引
CREATE INDEX idx_contracts_status ON contracts(status);

# 查看索引使用情况
SELECT * FROM pg_stat_user_indexes;
```

### Redis 优化

```bash
# 查看内存使用
redis-cli INFO memory

# 查看慢查询
redis-cli SLOWLOG GET 10

# 设置最大内存
redis-cli CONFIG SET maxmemory 256mb
```

### 应用优化

```python
# 使用连接池
from sqlalchemy.pool import NullPool, QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
)

# 使用缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def get_user(user_id: str):
    # ...
```

## 安全建议

### 生产环境配置

```env
# 使用强密钥
SECRET_KEY=<使用 secrets.token_urlsafe(32) 生成>

# 关闭调试模式
DEBUG=false

# 限制 CORS 源
CORS_ORIGINS=https://your-production-domain.com

# 使用 HTTPS
MINIO_SECURE=true

# 限制日志级别
LOG_LEVEL=WARNING
```

### 敏感信息保护

```bash
# 不要提交 .env 文件到版本控制
echo ".env" >> .gitignore

# 使用环境变量管理工具
# - AWS Secrets Manager
# - HashiCorp Vault
# - Kubernetes Secrets
```

## 更多资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Alembic 文档](https://alembic.sqlalchemy.org/)
- [Redis 文档](https://redis.io/documentation)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
- [MinIO 文档](https://min.io/docs/)

## 获取帮助

如有问题,请:

1. 查看本文档的常见问题部分
2. 查看项目 README.md
3. 查看 API 文档: http://localhost:8000/api/docs
4. 联系开发团队
