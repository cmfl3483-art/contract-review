# 服务器 .env 配置参考与踩坑记录

> 最后更新：2026-05-28
> 适用环境：test（`/home/ubuntu/contract-review/`）

---

## ⚠️ 重要说明

服务器上有**两个** `.env` 文件，职责不同，修改时必须搞清楚改哪个：

| 文件 | 路径 | 作用 | 优先级 |
|---|---|---|---|
| 根目录 `.env` | `/home/ubuntu/contract-review/.env` | 被 `docker-compose.yml` 读取，注入为容器环境变量 | **最高** |
| backend `.env` | `/home/ubuntu/contract-review/backend/.env` | 被 Pydantic Settings 读取（`python-dotenv`） | 中 |
| `config.py` 默认值 | 代码里 | 兜底默认值 | 最低 |

**优先级**：容器环境变量（来自根目录 `.env`）> `backend/.env` > `config.py` 默认值

两个文件都在 `.gitignore` 里，**不被 git 管理**，服务器上手动维护。

---

## 当前 test 环境完整配置

### 根目录 `.env`（`/home/ubuntu/contract-review/.env`）

被 `docker-compose.yml` 的 `${VAR:-default}` 语法读取，注入为容器环境变量。

```env
# AI 配置（会覆盖 backend/.env 里的同名配置）
AI_PROVIDER=deepseek
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=sk-a4f19da0172247ff9573c00e48eabf4e
AI_MODEL=deepseek-v4-pro
```

### backend `.env`（`/home/ubuntu/contract-review/backend/.env`）

被 FastAPI/Celery 进程通过 Pydantic Settings 读取。

```env
PROJECT_NAME="合同预审看板系统"
ENVIRONMENT=production
DEBUG=false

# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/contract_review
DATABASE_ECHO=false

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_TTL=300

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET=contract-attachments

# JWT
SECRET_KEY=3JzN1P7IAKkCD5LfOD-gKtI5oV9cKh4spnQ4Suai9L0
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 钉钉
DINGTALK_APP_KEY=dingkyxfjd5bhgtr78rc
DINGTALK_APP_SECRET=PiNGAGUjtoh4byvBgNS-ZISS97COd7y4QftrFhGC8_ynuBS7N3B5aOeyMEhST2ag
DINGTALK_REDIRECT_URI=https://chenmin.yunumall.com/api/auth/dingtalk/callback

# AI（DeepSeek）—— 注意：AI_MODEL 实际由根目录 .env 的容器环境变量覆盖
AI_PROVIDER=deepseek
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=sk-a4f19da0172247ff9573c00e48eabf4e
AI_MODEL=deepseek-v4-pro
AI_TIMEOUT=300

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# CORS
CORS_ORIGINS=["https://chenmin.yunumall.com","https://chenmin0922.online"]

# 文件上传
MAX_FILE_SIZE=52428800

# 日志
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

---

## 修改配置的标准操作步骤

```bash
# 1. SSH 登录服务器
ssh -i kaifa.pem ubuntu@124.222.219.177

# 2. 同时修改两个 .env（以修改 AI_MODEL 为例）
sed -i "s/AI_MODEL=.*/AI_MODEL=新模型名/" /home/ubuntu/contract-review/.env
sed -i "s/AI_MODEL=.*/AI_MODEL=新模型名/" /home/ubuntu/contract-review/backend/.env

# 3. 用 docker compose up -d 重建容器（让新环境变量生效）
#    注意：docker restart 不会重新读取根目录 .env，必须用 up -d
docker compose -f /home/ubuntu/contract-review/docker-compose.yml up -d backend celery_worker

# 4. 验证配置是否生效
docker exec contract_review_celery_worker python3 -c \
  "from app.core.config import settings; print('AI_MODEL:', settings.AI_MODEL, 'AI_TIMEOUT:', settings.AI_TIMEOUT)"
```

---

## DeepSeek 模型名说明

DeepSeek 官方 API 的有效模型名（截至 2026-05）：

| 模型名 | 说明 | 适用场景 |
|---|---|---|
| `deepseek-v4-flash` | 轻量快速版，推理能力较弱 | 简单任务，追求速度 |
| `deepseek-v4-pro` | Pro 版，推理能力强，结果稳定 | 合同合规检查（当前使用） |
| `deepseek-chat` | DeepSeek-V3 官方名，等同于 Pro | 同上，官方推荐名 |
| `deepseek-reasoner` | DeepSeek-R1，深度推理模型 | 复杂逻辑推理 |

**注意**：`deepseek-v4-pro` 和 `deepseek-chat` 都指向同一个 Pro 级别模型，两个名字都有效。

---

## 踩坑记录

### 坑 1：AI_TIMEOUT=30 导致合规检查一直失败

**症状**：合规检查提交后，Celery worker 日志显示 `APITimeoutError: Request timed out`，
每次约 30 秒就超时，无论代码里怎么改 `AI_TIMEOUT` 默认值都不生效。

**根因**：服务器 `backend/.env` 里有 `AI_TIMEOUT=30`（历史遗留值），
Pydantic Settings 优先读取 `.env`，覆盖了 `config.py` 里的 `AI_TIMEOUT: int = 300`。

**修复**：
```bash
sed -i "s/AI_TIMEOUT=30/AI_TIMEOUT=300/" /home/ubuntu/contract-review/backend/.env
docker restart contract_review_backend contract_review_celery_worker
```

**验证**：
```bash
docker exec contract_review_celery_worker python3 -c \
  "from app.core.config import settings; print('AI_TIMEOUT:', settings.AI_TIMEOUT)"
# 应输出：AI_TIMEOUT: 300
```

**教训**：修改 `config.py` 里的配置默认值后，必须同步检查服务器 `.env` 是否有同名配置覆盖。

---

### 坑 2：.env 文件不在 git 里，代码改动不会自动同步

**背景**：两个 `.env` 都在 `.gitignore` 里，CI/CD 的 rsync 会跳过（`--exclude='.env'`）。

**副作用**：`config.py` 里改了默认值，服务器上运行的程序仍然用 `.env` 里的旧值。

**规则**：
1. 新增配置项时，同步在服务器两个 `.env` 里加上
2. 修改配置默认值时，检查服务器 `.env` 是否有同名项需要同步更新
3. 本文档作为服务器 `.env` 的权威参考，每次修改后更新本文档

---

### 坑 3：只改 backend/.env 的 AI_MODEL 不生效

**症状**：修改了 `backend/.env` 里的 `AI_MODEL`，重启容器后模型没有切换。

**根因**：`docker-compose.yml` 里有 `AI_MODEL: ${AI_MODEL:-deepseek-chat}`，
从**根目录 `.env`** 读取并注入为容器环境变量，优先级高于 `backend/.env`。

**修复**：必须同时修改根目录 `.env` 和 `backend/.env`，并用 `docker compose up -d` 重建容器：
```bash
sed -i "s/AI_MODEL=.*/AI_MODEL=deepseek-v4-pro/" /home/ubuntu/contract-review/.env
sed -i "s/AI_MODEL=.*/AI_MODEL=deepseek-v4-pro/" /home/ubuntu/contract-review/backend/.env
docker compose -f /home/ubuntu/contract-review/docker-compose.yml up -d backend celery_worker
```

**规则**：凡是 `docker-compose.yml` 里有 `${VAR:-default}` 形式的环境变量，
修改时必须改根目录 `.env`，并用 `up -d` 而不是 `restart`。

---

### 坑 4：docker restart 不会重新读取根目录 .env

**症状**：修改了根目录 `.env`，执行 `docker restart` 后配置没有生效。

**根因**：`docker restart` 只是重启容器进程，不会重新读取 `docker-compose.yml` 和根目录 `.env`。
容器的环境变量在 `docker compose up` 时就固定了。

**修复**：必须用 `docker compose up -d` 重建容器：
```bash
docker compose -f /home/ubuntu/contract-review/docker-compose.yml up -d backend celery_worker
```

---

## 各配置项说明

| 配置项 | 当前值 | 说明 |
|---|---|---|
| `AI_MODEL` | `deepseek-v4-pro` | DeepSeek Pro 模型，推理能力强，结果稳定。**同时存在于根目录 .env 和 backend/.env，修改时两处都要改** |
| `AI_TIMEOUT` | `300` | AI API 单次请求超时秒数。DeepSeek 处理大合同+多规则时需要较长时间，不能低于 120 |
| `REDIS_URL` | `redis://redis:6379/0` | 主缓存 db=0，Celery broker 用 db=1，result backend 用 db=2 |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Celery 任务队列，与主缓存隔离 |
| `CORS_ORIGINS` | test+prod 两个域名 | 新增域名时需同步更新 |
| `MAX_FILE_SIZE` | `52428800`（50MB）| 合同文件上传大小限制 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440`（24小时）| JWT token 有效期 |
