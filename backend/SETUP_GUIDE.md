# 合同预审看板系统 - 后端环境配置指南

## 目录

1. [环境准备](#环境准备)
2. [依赖服务安装](#依赖服务安装)
3. [项目配置](#项目配置)
4. [数据库初始化](#数据库初始化)
5. [启动服务](#启动服务)
6. [验证配置](#验证配置)
7. [常见问题](#常见问题)

## 环境准备

### 1. 安装 Python 3.11+

**macOS:**
```bash
# 使用 Homebrew
brew install python@3.11

# 验证安装
python3 --version
```

**Ubuntu/Debian:**
```bash
# 添加 deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# 安装 Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# 验证安装
python3.11 --version
```

**Windows:**
- 从 [Python 官网](https://www.python.org/downloads/) 下载安装包
- 安装时勾选 "Add Python to PATH"
- 验证: 打开 CMD 运行 `python --version`

### 2. 安装 Poetry (推荐)

```bash
# 安装 Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 验证安装
poetry --version

# 配置 Poetry (可选)
poetry config virtualenvs.in-project true  # 在项目目录创建虚拟环境
```

## 依赖服务安装

### 方法一: 使用 Docker (推荐)

最简单的方式是使用 Docker 运行所有依赖服务。

```bash
# 1. 安装 Docker Desktop
# macOS/Windows: 从 https://www.docker.com/products/docker-desktop 下载
# Linux: 使用包管理器安装

# 2. 验证安装
docker --version
docker-compose --version

# 3. 启动依赖服务
cd /path/to/project
docker-compose up -d postgres redis minio

# 4. 验证服务状态
docker-compose ps
```

### 方法二: 本地安装

#### PostgreSQL 15

**macOS:**
```bash
# 使用 Homebrew
brew install postgresql@15
brew services start postgresql@15

# 创建数据库
createdb contract_review
```

**Ubuntu/Debian:**
```bash
# 安装 PostgreSQL
sudo apt install postgresql-15

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库
sudo -u postgres createdb contract_review
```

**Windows:**
- 从 [PostgreSQL 官网](https://www.postgresql.org/download/windows/) 下载安装包
- 使用 pgAdmin 创建数据库 `contract_review`

#### Redis 7

**macOS:**
```bash
# 使用 Homebrew
brew install redis
brew services start redis

# 验证
redis-cli ping  # 应返回 PONG
```

**Ubuntu/Debian:**
```bash
# 安装 Redis
sudo apt install redis-server

# 启动服务
sudo systemctl start redis
sudo systemctl enable redis

# 验证
redis-cli ping
```

**Windows:**
- 从 [Redis 官网](https://redis.io/download/) 下载 Windows 版本
- 或使用 WSL2 安装 Linux 版本

#### MinIO (可选)

**使用 Docker (推荐):**
```bash
docker run -d \
  --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

**本地安装:**
```bash
# macOS
brew install minio/stable/minio
minio server /data

# Linux
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
./minio server /data

# Windows
# 从 https://min.io/download 下载 exe 文件
```

## 项目配置

### 1. 安装项目依赖

```bash
# 进入后端目录
cd backend

# 使用 Poetry
poetry install

# 或使用 pip
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 文件
nano .env  # 或使用其他编辑器
```

**必须配置的项目:**

```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/contract_review

# JWT 密钥 (生产环境必须修改!)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 钉钉配置 (从钉钉开放平台获取)
DINGTALK_APP_KEY=your-app-key
DINGTALK_APP_SECRET=your-app-secret
DINGTALK_REDIRECT_URI=http://localhost:3000/auth/callback

# AI 配置 (如使用 DeepSeek)
AI_PROVIDER=deepseek
AI_API_KEY=your-deepseek-api-key
```

**可选配置:**

```bash
# Redis 配置 (如果不是默认地址)
REDIS_URL=redis://localhost:6379/0

# MinIO 配置 (如果不是默认地址)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# CORS 配置 (添加前端地址)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 3. 生成安全密钥

```bash
# 生成 JWT 密钥
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# 将输出的密钥复制到 .env 文件中
```

## 数据库初始化

### 1. 验证数据库连接

```bash
# 使用 psql 连接数据库
psql -h localhost -U postgres -d contract_review

# 或使用 Python 测试
python3 -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:postgres@localhost:5432/contract_review')
with engine.connect() as conn:
    print('✅ 数据库连接成功!')
"
```

### 2. 运行数据库迁移

```bash
# 激活虚拟环境
poetry shell  # 或 source venv/bin/activate

# 运行迁移
alembic upgrade head

# 如果出现错误,可以查看迁移历史
alembic history
alembic current
```

### 3. 验证数据库表

```bash
# 连接数据库
psql -h localhost -U postgres -d contract_review

# 查看所有表
\dt

# 应该看到以下表:
# - users
# - contracts
# - reviews
# - comments
# - attachments
# - ai_summaries
# - alembic_version
```

## 启动服务

### 1. 启动后端服务

```bash
# 激活虚拟环境
poetry shell  # 或 source venv/bin/activate

# 启动服务 (开发模式)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 验证服务启动

打开浏览器访问:
- **健康检查**: http://localhost:8000/health
- **API 文档**: http://localhost:8000/api/docs
- **根路径**: http://localhost:8000/

应该看到类似以下输出:
```
🚀 合同预审看板系统 启动中...
📝 环境: development
🔗 数据库: localhost:5432/contract_review
✅ Redis 连接成功: redis://localhost:6379/0
✅ MinIO 连接成功: localhost:9000
✅ Bucket 初始化成功: contract-attachments
```

### 3. 启动 Celery Worker (可选)

如果需要使用 AI 功能,需要启动 Celery:

```bash
# 新开一个终端
cd backend
poetry shell

# 启动 Celery worker
celery -A app.celery_app worker --loglevel=info
```

## 验证配置

### 1. 运行配置验证脚本

```bash
# 运行验证脚本
python3 test_connections.py
```

应该看到:
```
✅ 数据库连接成功
✅ Redis 连接成功
✅ MinIO 连接成功
✅ 所有服务配置正确!
```

### 2. 测试 API 端点

```bash
# 测试健康检查
curl http://localhost:8000/health

# 应该返回:
# {"status":"healthy","environment":"development"}

# 测试根路径
curl http://localhost:8000/

# 应该返回:
# {"message":"合同预审看板系统 API","version":"0.1.0","status":"running"}
```

### 3. 测试数据库操作

访问 http://localhost:8000/api/docs 并尝试:
1. 展开 `/api/contracts` 端点
2. 点击 "Try it out"
3. 执行请求

## 常见问题

### 问题 1: 数据库连接失败

**错误信息:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决方案:**
1. 检查 PostgreSQL 是否运行
   ```bash
   # macOS/Linux
   sudo systemctl status postgresql
   # 或
   pg_isready
   ```

2. 检查数据库配置
   ```bash
   # 验证数据库存在
   psql -l | grep contract_review
   ```

3. 检查防火墙设置

### 问题 2: Redis 连接失败

**错误信息:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**解决方案:**
1. 检查 Redis 是否运行
   ```bash
   redis-cli ping
   ```

2. 检查 Redis 配置
   ```bash
   # 查看 Redis 配置
   redis-cli CONFIG GET bind
   redis-cli CONFIG GET port
   ```

### 问题 3: MinIO 连接失败

**错误信息:**
```
minio.error.S3Error: Connection refused
```

**解决方案:**
1. 检查 MinIO 是否运行
   ```bash
   curl http://localhost:9000/minio/health/live
   ```

2. 检查 MinIO 配置
   - 访问 http://localhost:9001 (MinIO Console)
   - 使用 minioadmin/minioadmin 登录

### 问题 4: 依赖安装失败

**错误信息:**
```
ERROR: Could not find a version that satisfies the requirement
```

**解决方案:**
1. 更新 pip
   ```bash
   pip install --upgrade pip
   ```

2. 使用国内镜像
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. 检查 Python 版本
   ```bash
   python3 --version  # 应该是 3.11+
   ```

### 问题 5: 端口被占用

**错误信息:**
```
OSError: [Errno 48] Address already in use
```

**解决方案:**
1. 查找占用端口的进程
   ```bash
   # macOS/Linux
   lsof -i :8000
   
   # Windows
   netstat -ano | findstr :8000
   ```

2. 终止进程或使用其他端口
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

### 问题 6: 数据库迁移失败

**错误信息:**
```
alembic.util.exc.CommandError: Target database is not up to date
```

**解决方案:**
1. 查看当前迁移状态
   ```bash
   alembic current
   alembic history
   ```

2. 重置数据库 (开发环境)
   ```bash
   # 删除所有表
   alembic downgrade base
   
   # 重新运行迁移
   alembic upgrade head
   ```

3. 如果仍然失败,删除 alembic_version 表
   ```sql
   DROP TABLE alembic_version;
   ```
   然后重新运行迁移

## 下一步

配置完成后,可以:

1. **启动前端服务**: 参考 `frontend/README.md`
2. **配置钉钉登录**: 参考钉钉开放平台文档
3. **配置 AI 服务**: 获取 DeepSeek API Key 或配置自部署模型
4. **开始开发**: 查看 `DEVELOPMENT.md` 了解开发指南

## 获取帮助

如果遇到问题:
1. 查看日志文件: `logs/app.log`
2. 查看 API 文档: http://localhost:8000/api/docs
3. 查看项目文档: `README.md`
4. 联系开发团队

---

**祝你配置顺利! 🚀**
