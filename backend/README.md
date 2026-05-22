# 合同预审看板系统 - 后端服务

Contract Pre-Review System - Backend Service

## 快速开始 (5 分钟)

```bash
# 1. 启动依赖服务 (使用 Docker)
docker-compose up -d postgres redis minio

# 2. 安装依赖
cd backend
poetry install  # 或 pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件,至少配置 DATABASE_URL 和 SECRET_KEY

# 4. 初始化数据库
poetry run alembic upgrade head

# 5. 测试连接
poetry run python test_connections.py

# 6. 启动服务
poetry run uvicorn app.main:app --reload

# 访问 http://localhost:8000/api/docs 查看 API 文档
```

详细配置说明请查看 [SETUP_GUIDE.md](./SETUP_GUIDE.md)

---

## 技术栈

- **Python**: 3.11+
- **Web 框架**: FastAPI
- **ORM**: SQLAlchemy 2.0 (异步)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **文件存储**: MinIO
- **任务队列**: Celery
- **实时通信**: Socket.IO
- **AI 服务**: DeepSeek API / 自部署模型

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── core/                # 核心配置
│   │   ├── config.py        # 应用配置
│   │   ├── database.py      # 数据库配置
│   │   ├── redis_client.py  # Redis 客户端
│   │   └── logging_config.py # 日志配置
│   ├── models/              # SQLAlchemy 数据库模型
│   ├── schemas/             # Pydantic 数据模型
│   ├── routes/              # API 路由
│   ├── services/            # 业务逻辑服务层
│   └── utils/               # 工具函数
├── alembic/                 # 数据库迁移
├── tests/                   # 测试文件
├── logs/                    # 日志文件
├── pyproject.toml           # Poetry 配置
├── requirements.txt         # pip 依赖
├── .env.example             # 环境变量示例
└── README.md                # 项目说明
```

## 快速开始

### 前置条件

在开始之前,请确保已安装以下软件:

- **Python 3.11+**: [下载地址](https://www.python.org/downloads/)
- **PostgreSQL 15+**: [下载地址](https://www.postgresql.org/download/)
- **Redis 7+**: [下载地址](https://redis.io/download/)
- **MinIO**: [下载地址](https://min.io/download) (可选,用于文件存储)

### 安装步骤

#### 方法一: 使用 Poetry (推荐)

Poetry 是现代化的 Python 依赖管理工具,推荐使用。

```bash
# 1. 安装 Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 2. 进入项目目录
cd backend

# 3. 安装依赖
poetry install

# 4. 激活虚拟环境
poetry shell
```

#### 方法二: 使用 pip

如果不想使用 Poetry,也可以使用传统的 pip 方式。

```bash
# 1. 进入项目目录
cd backend

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 文件,根据实际环境修改配置
# 必须修改的配置项:
# - DATABASE_URL: PostgreSQL 数据库连接字符串
# - SECRET_KEY: JWT 密钥 (生产环境必须使用强随机字符串)
# - DINGTALK_APP_KEY: 钉钉应用 Key
# - DINGTALK_APP_SECRET: 钉钉应用 Secret
# - AI_API_KEY: AI 服务 API Key (如使用 DeepSeek)

# 使用你喜欢的编辑器打开
nano .env
# 或
vim .env
# 或
code .env
```

**重要配置说明:**

1. **数据库配置**: 确保 PostgreSQL 已启动,并创建了数据库
   ```bash
   # 创建数据库 (在 PostgreSQL 中执行)
   createdb contract_review
   ```

2. **JWT 密钥**: 生产环境必须使用强随机字符串
   ```bash
   # 生成安全的密钥
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **钉钉配置**: 从钉钉开放平台获取应用凭证
   - 访问: https://open.dingtalk.com/
   - 创建应用并获取 AppKey 和 AppSecret

4. **AI 配置**: 
   - 使用 DeepSeek: 从 https://platform.deepseek.com/ 获取 API Key
   - 使用自部署模型: 配置 OpenAI 兼容 API 地址

### 初始化数据库

```bash
# 1. 确保数据库已创建并可连接
# 2. 运行数据库迁移
alembic upgrade head

# 如果需要创建新的迁移 (开发时使用)
alembic revision --autogenerate -m "描述迁移内容"
```

### 启动服务

```bash
# 开发模式 (支持热重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后,访问:
- **API 文档**: http://localhost:8000/api/docs
- **健康检查**: http://localhost:8000/health

## 运行命令

### 开发模式

```bash
# 使用 uvicorn 运行 (热重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 指定日志级别
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

访问地址:
- **API 根路径**: http://localhost:8000/
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **健康检查**: http://localhost:8000/health

### 生产模式

```bash
# 使用 uvicorn 运行 (多进程)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 或使用 gunicorn + uvicorn worker (推荐)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 启动依赖服务

在启动后端服务之前,确保以下服务已启动:

```bash
# 启动 PostgreSQL (如果使用 Docker)
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=contract_review \
  -p 5432:5432 \
  postgres:15

# 启动 Redis (如果使用 Docker)
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7

# 启动 MinIO (如果使用 Docker)
docker run -d \
  --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

### 启动 Celery Worker (异步任务)

```bash
# 启动 Celery worker
celery -A app.celery_app worker --loglevel=info

# 启动 Celery beat (定时任务)
celery -A app.celery_app beat --loglevel=info

# 同时启动 worker 和 beat
celery -A app.celery_app worker --beat --loglevel=info
```

## API 文档

启动服务后,访问以下地址查看 API 文档:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## 测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行特定测试文件
pytest tests/test_contracts.py

# 运行特定测试函数
pytest tests/test_contracts.py::test_create_contract
```

## 代码质量

```bash
# 代码格式化
black app/

# 代码检查
flake8 app/

# 类型检查
mypy app/

# 导入排序
isort app/
```

## Docker 部署

### 使用 Docker Compose (推荐)

最简单的部署方式是使用 Docker Compose,它会自动启动所有依赖服务。

```bash
# 1. 确保已安装 Docker 和 Docker Compose
docker --version
docker-compose --version

# 2. 进入项目根目录
cd /path/to/project

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f backend

# 6. 停止所有服务
docker-compose down
```

Docker Compose 会启动以下服务:
- **backend**: FastAPI 后端服务 (端口 8000)
- **postgres**: PostgreSQL 数据库 (端口 5432)
- **redis**: Redis 缓存 (端口 6379)
- **minio**: MinIO 对象存储 (端口 9000, 9001)
- **frontend**: React 前端应用 (端口 3000)

### 单独构建后端镜像

```bash
# 构建镜像
docker build -t contract-review-backend .

# 运行容器
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name backend \
  contract-review-backend

# 查看日志
docker logs -f backend

# 停止容器
docker stop backend

# 删除容器
docker rm backend
```

### 生产环境部署建议

1. **使用环境变量**: 不要在镜像中包含敏感信息
2. **使用外部数据库**: 不要在容器中运行数据库
3. **配置健康检查**: 确保服务可用性
4. **使用反向代理**: 使用 Nginx 或 Traefik
5. **配置日志收集**: 使用 ELK 或类似工具
6. **配置监控**: 使用 Prometheus + Grafana

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 数据库连接字符串 | - |
| `REDIS_URL` | Redis 连接字符串 | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT 密钥 | - |
| `DINGTALK_APP_KEY` | 钉钉应用 Key | - |
| `DINGTALK_APP_SECRET` | 钉钉应用 Secret | - |
| `AI_API_KEY` | AI 服务 API Key | - |
| `MINIO_ENDPOINT` | MinIO 服务地址 | `localhost:9000` |

## 开发指南

### 添加新的 API 端点

1. 在 `app/routes/` 创建路由文件
2. 在 `app/services/` 创建服务类
3. 在 `app/schemas/` 创建 Pydantic 模型
4. 在 `app/main.py` 中注册路由

### 添加数据库模型

1. 在 `app/models/` 创建模型文件
2. 在 `app/models/__init__.py` 中导入模型
3. 运行 `alembic revision --autogenerate -m "描述"`
4. 运行 `alembic upgrade head`

## 常见问题

### 数据库连接失败

**问题**: 启动时提示数据库连接失败

**解决方案**:
1. 检查 PostgreSQL 是否运行
   ```bash
   # Linux/Mac
   sudo systemctl status postgresql
   # 或
   pg_isready
   ```

2. 检查 `.env` 中的数据库配置是否正确
   ```bash
   # 格式: postgresql+asyncpg://用户名:密码@主机:端口/数据库名
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/contract_review
   ```

3. 确保数据库已创建
   ```bash
   createdb contract_review
   ```

### Redis 连接失败

**问题**: 启动时提示 Redis 连接失败

**解决方案**:
1. 检查 Redis 是否运行
   ```bash
   redis-cli ping
   # 应该返回 PONG
   ```

2. 检查 `.env` 中的 Redis 配置
   ```bash
   REDIS_URL=redis://localhost:6379/0
   ```

### MinIO 连接失败

**问题**: 文件上传失败或 MinIO 连接失败

**解决方案**:
1. 检查 MinIO 是否运行
   ```bash
   curl http://localhost:9000/minio/health/live
   ```

2. 检查 `.env` 中的 MinIO 配置
   ```bash
   MINIO_ENDPOINT=localhost:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   ```

3. 确保 bucket 已创建 (应用启动时会自动创建)

### 文件上传失败

**问题**: 上传文件时提示文件过大或类型不支持

**解决方案**:
1. 检查文件大小是否超过限制 (默认 20MB)
   ```bash
   # 在 .env 中修改
   MAX_FILE_SIZE=20971520  # 20MB
   ```

2. 检查文件类型是否支持
   - 支持的类型: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX
   - 在 `app/core/config.py` 中查看 `ALLOWED_FILE_TYPES`

### 钉钉授权登录失败

**问题**: 钉钉授权登录失败或回调错误

**解决方案**:
1. 检查钉钉应用配置
   - 确保 AppKey 和 AppSecret 正确
   - 确保回调地址已在钉钉开放平台配置

2. 检查 `.env` 中的钉钉配置
   ```bash
   DINGTALK_APP_KEY=your-app-key
   DINGTALK_APP_SECRET=your-app-secret
   DINGTALK_REDIRECT_URI=http://localhost:3000/auth/callback
   ```

### AI 服务调用失败

**问题**: AI 智能总结或顾问功能不可用

**解决方案**:
1. 检查 AI 服务配置
   ```bash
   # DeepSeek 配置
   AI_PROVIDER=deepseek
   AI_API_KEY=your-api-key
   
   # 自部署模型配置
   AI_PROVIDER=custom
   AI_API_BASE=http://localhost:8000/v1
   ```

2. 检查 API Key 是否有效
3. 检查网络连接是否正常
4. 查看日志文件 `logs/app.log` 获取详细错误信息

### 数据库迁移失败

**问题**: 运行 `alembic upgrade head` 失败

**解决方案**:
1. 检查数据库连接是否正常
2. 删除 `alembic/versions/` 中的迁移文件,重新生成
   ```bash
   # 删除旧的迁移文件
   rm alembic/versions/*.py
   
   # 重新生成迁移
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

3. 如果数据库已有数据,可能需要手动处理冲突

### 端口被占用

**问题**: 启动时提示端口 8000 已被占用

**解决方案**:
1. 查找占用端口的进程
   ```bash
   # Linux/Mac
   lsof -i :8000
   
   # Windows
   netstat -ano | findstr :8000
   ```

2. 终止占用端口的进程或使用其他端口
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

### 日志文件过大

**问题**: 日志文件占用大量磁盘空间

**解决方案**:
1. 配置日志轮转 (使用 logrotate 或类似工具)
2. 定期清理旧日志
   ```bash
   # 清理 7 天前的日志
   find logs/ -name "*.log" -mtime +7 -delete
   ```

3. 调整日志级别
   ```bash
   # 在 .env 中设置
   LOG_LEVEL=WARNING  # 只记录警告和错误
   ```

## 许可证

MIT License

## 联系方式

如有问题,请联系开发团队。
