# 服务器 .env 配置参考与踩坑记录

> 最后更新：2026-05-28
> 适用环境：test（`/home/ubuntu/contract-review/backend/.env`）

---

## ⚠️ 重要说明

`backend/.env` 文件在 `.gitignore` 里，**不被 git 管理**，服务器上手动维护。
每次修改代码里的配置默认值（`config.py`）后，**必须同步检查并更新服务器上的 `.env`**，
否则 Pydantic Settings 会优先读取 `.env` 里的旧值，代码改动不生效。

**优先级**：环境变量 > `.env` 文件 > `config.py` 默认值

---

## 当前 test 环境完整配置

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

# AI（DeepSeek）
AI_PROVIDER=deepseek
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=sk-a4f19da0172247ff9573c00e48eabf4e
AI_MODEL=deepseek-v4-flash
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

## 踩坑记录

### 坑 1：AI_TIMEOUT=30 导致合规检查一直失败

**症状**：合规检查提交后，Celery worker 日志显示 `APITimeoutError: Request timed out`，
每次约 30 秒就超时，无论代码里怎么改 `AI_TIMEOUT` 默认值都不生效。

**根因**：服务器 `backend/.env` 里有 `AI_TIMEOUT=30`（历史遗留值），
Pydantic Settings 优先读取 `.env`，覆盖了 `config.py` 里的 `AI_TIMEOUT: int = 300`。

**修复**：
```bash
# 登录服务器修改
ssh -i kaifa.pem ubuntu@124.222.219.177
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

**背景**：`.env` 在 `.gitignore` 里，CI/CD 的 rsync 会跳过它（`--exclude='.env'`）。
这是故意的设计——避免把密钥推到 git。

**副作用**：如果 `.env` 里有配置项，即使 `config.py` 里改了默认值，
服务器上运行的程序仍然用 `.env` 里的旧值。

**规则**：
1. 新增配置项时，同步在服务器 `.env` 里加上
2. 修改配置默认值时，检查服务器 `.env` 是否有同名项需要同步更新
3. 本文档作为服务器 `.env` 的权威参考，每次修改后更新本文档

---

## 修改 .env 的操作步骤

```bash
# 1. SSH 登录服务器
ssh -i kaifa.pem ubuntu@124.222.219.177

# 2. 编辑 .env
vim /home/ubuntu/contract-review/backend/.env

# 3. 重启相关容器使配置生效
# backend 和 celery_worker 都读取同一个 .env（bind mount ./backend:/app）
docker restart contract_review_backend contract_review_celery_worker

# 4. 验证配置是否生效
docker exec contract_review_backend python3 -c \
  "from app.core.config import settings; print(vars(settings))"
```

---

## 各配置项说明

| 配置项 | 当前值 | 说明 |
|---|---|---|
| `AI_TIMEOUT` | `300` | AI API 单次请求超时秒数。DeepSeek 处理大合同+多规则时需要较长时间，不能低于 120 |
| `AI_MODEL` | `deepseek-v4-flash` | DeepSeek 模型名，注意与 API 文档保持一致 |
| `REDIS_URL` | `redis://redis:6379/0` | 主缓存 db=0，Celery broker 用 db=1，result backend 用 db=2 |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Celery 任务队列，与主缓存隔离 |
| `CORS_ORIGINS` | test+prod 两个域名 | 新增域名时需同步更新 |
| `MAX_FILE_SIZE` | `52428800`（50MB）| 合同文件上传大小限制 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440`（24小时）| JWT token 有效期 |
