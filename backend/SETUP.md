# 后端设置指南

本文档说明如何配置和启动后端服务。

## 前置要求

1. **Python 3.11+**
   ```bash
   python --version
   ```

2. **Docker 和 Docker Compose**
   - 用于运行 PostgreSQL、Redis 和 MinIO
   - 安装指南: https://www.docker.com/get-started

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

或使用虚拟环境（推荐）：

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，根据需要修改配置。开发环境可以使用默认值。

### 3. 启动基础设施服务

在项目根目录执行：

```bash
cd ..  # 回到项目根目录
./start-services.sh
```

或手动启动：

```bash
docker compose up -d
```

### 4. 测试连接

```bash
cd backend
python test_connections.py
```

如果所有测试通过，说明配置正确。

### 5. 运行数据库迁移

```bash
alembic upgrade head
```

### 6. 启动开发服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务器将在 http://localhost:8000 启动。

访问 API 文档：
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 配置说明

### 数据库配置

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/contract_review
DATABASE_ECHO=false  # 设置为 true 可以看到 SQL 查询日志
```

- 使用 `asyncpg` 驱动实现异步数据库访问
- 连接池配置: pool_size=10, max_overflow=20

### Redis 配置

```env
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=300  # 默认缓存过期时间（秒）
```

Redis 用于：
- 缓存合同列表、详情等数据
- 存储用户会话
- Celery 任务队列

### MinIO 配置

```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false  # 开发环境使用 HTTP，生产环境应设置为 true
MINIO_BUCKET=contract-attachments
```

MinIO 用于存储合同附件文件。

### AI 配置

系统支持两种 AI 服务：

#### 1. DeepSeek API

```env
AI_PROVIDER=deepseek
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=your-deepseek-api-key
AI_MODEL=deepseek-chat
```

#### 2. 自部署模型（OpenAI 兼容 API）

```env
AI_PROVIDER=custom
AI_API_BASE=http://localhost:8000/v1  # 你的模型服务地址
AI_API_KEY=your-api-key  # 如果需要
AI_MODEL=qwen2.5-7b-instruct  # 你的模型名称
```

支持的自部署方案：
- vLLM
- Ollama
- LocalAI
- 其他 OpenAI 兼容 API

## 开发工具

### 代码格式化

```bash
# 使用 black 格式化代码
black app/

# 使用 isort 排序导入
isort app/
```

### 代码检查

```bash
# 使用 flake8 检查代码风格
flake8 app/

# 使用 mypy 检查类型
mypy app/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行特定测试文件
pytest tests/test_contracts.py
```

## 数据库迁移

### 创建新迁移

```bash
alembic revision --autogenerate -m "描述你的更改"
```

### 应用迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到特定版本
alembic upgrade <revision_id>
```

### 回滚迁移

```bash
# 回滚一个版本
alembic downgrade -1

# 回滚到特定版本
alembic downgrade <revision_id>
```

### 查看迁移历史

```bash
alembic history
```

## 故障排查

### 数据库连接失败

1. 确认 PostgreSQL 服务正在运行：
   ```bash
   docker compose ps postgres
   ```

2. 检查数据库连接字符串是否正确

3. 查看 PostgreSQL 日志：
   ```bash
   docker compose logs postgres
   ```

### Redis 连接失败

1. 确认 Redis 服务正在运行：
   ```bash
   docker compose ps redis
   ```

2. 测试 Redis 连接：
   ```bash
   redis-cli -h localhost -p 6379 ping
   ```

### MinIO 连接失败

1. 确认 MinIO 服务正在运行：
   ```bash
   docker compose ps minio
   ```

2. 访问 MinIO Console: http://localhost:9001

3. 检查 bucket 是否存在

### 导入错误

确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

### 端口被占用

如果端口 8000 被占用，可以使用其他端口：

```bash
uvicorn app.main:app --reload --port 8001
```

## 生产环境部署

⚠️ **重要**: 生产环境需要额外配置：

1. **修改所有默认密码和密钥**
   - DATABASE_URL 中的数据库密码
   - SECRET_KEY（使用强随机字符串）
   - MinIO 访问密钥
   - 钉钉应用密钥

2. **启用 HTTPS**
   - 设置 MINIO_SECURE=true
   - 配置 SSL 证书

3. **配置环境变量**
   - 设置 ENVIRONMENT=production
   - 设置 DEBUG=false

4. **使用生产级 WSGI 服务器**
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

5. **配置日志**
   - 使用结构化日志
   - 配置日志轮转
   - 集成日志监控

6. **数据库优化**
   - 调整连接池大小
   - 配置数据库备份
   - 启用慢查询日志

7. **安全加固**
   - 配置防火墙
   - 限制 CORS 源
   - 启用速率限制
   - 配置安全头

## 有用的命令

```bash
# 查看所有 Docker 服务状态
docker compose ps

# 查看服务日志
docker compose logs -f

# 重启服务
docker compose restart

# 停止所有服务
docker compose down

# 进入 PostgreSQL 容器
docker compose exec postgres psql -U postgres -d contract_review

# 进入 Redis 容器
docker compose exec redis redis-cli

# 清理所有数据（慎用！）
docker compose down -v
```

## 获取帮助

如果遇到问题：

1. 查看日志文件
2. 运行连接测试脚本
3. 检查环境变量配置
4. 查看 Docker 服务状态
5. 参考 DOCKER_SETUP.md 文档
