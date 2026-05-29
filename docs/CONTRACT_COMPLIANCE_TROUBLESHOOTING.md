# 合规检查功能踩坑与排查指南

> 最后更新：2026-05-29
> 适用范围：`contract-compliance-check` + `compliance-rule-excel-import` 两个 spec 的实施与运维
> 目标读者：项目接手人 / 后续维护者 / AI 编码助手

---

## 0. TL;DR（30 秒读完）

合规检查的执行链路：

```
前端提交 → POST /checks → 后端 create_pending_check（同步）
        ↓ 立即返回 pending
        ↓ run_compliance_check_task.delay() 投递到 Celery
Celery worker → 从 MinIO 拉文件 → 文本抽取 → 查规则 → 调 DeepSeek → 写回 completed/failed
        ↓ 前端轮询 GET /checks/{id} 直到 status != 'pending'
```

**最容易踩的 4 个坑**：
1. `backend/.env` 和根目录 `.env` 都有同名配置时，**根目录优先**（注入容器环境变量）
2. CI/CD 部署重建 worker 容器时，正在跑的任务会**直接丢失** → 产生孤儿 pending 记录
3. Celery worker 是**独立容器**，pip 依赖装在 backend 容器里不会自动同步到 worker
4. SQLAlchemy async session 的 lazy load 在 commit 后访问关联对象会报 `MissingGreenlet`

---

## 1. 系统架构关键点

### 1.1 容器拓扑

| 容器 | 作用 | 镜像构建上下文 | bind mount |
|---|---|---|---|
| `contract_review_backend` | FastAPI HTTP API | `./backend/Dockerfile` | `./backend:/app` |
| `contract_review_celery_worker` | Celery 异步任务 | `./backend/Dockerfile` (同) | `./backend:/app` |
| `contract_review_postgres` | PostgreSQL 共享 | postgres:15 | (volume) |
| `contract_review_redis` | Redis 共享 | redis:7 | (volume) |
| `contract_review_minio` | MinIO 共享 | minio | (volume) |
| `contract_review_frontend` | Vite + Nginx | `./frontend/Dockerfile` | (无 bind mount) |

**关键**：backend 和 celery_worker 用同一个 Dockerfile 但**镜像独立构建**。改 `requirements.txt` 后必须重建**两个**镜像。

### 1.2 异步任务流程

```
[Backend Container]              [Redis db 1: celery broker]              [Celery Worker]
POST /checks                          ↓                                       ↓
  ↓ create_pending_check              ↓                                       ↓
  ↓   (校验+MinIO+DB:pending)         ↓                                       ↓
  ↓ commit                            ↓                                       ↓
  ↓ task.delay()  ─────────────→  [push task]  ─────────────→ run_compliance_check_task
  ↓                                                            ↓ MinIO get_file
return pending response                                        ↓ TextExtractor
                                                               ↓ AI check_compliance
                                                               ↓ DB update completed/failed
```

### 1.3 配置优先级（极易踩）

```
容器环境变量（来自根目录 .env，docker-compose.yml 注入）
    ↓ 高于
backend/.env（Pydantic Settings 通过 python-dotenv 读取）
    ↓ 高于
config.py 默认值
```

详见 `docs/ENV_CONFIG_REFERENCE.md`。

---

## 2. 故障排查 Cheatsheet

### 故障 1：合规检查一直「检查中」

**可能原因**（按概率排序）：

| 排查步骤 | 命令 | 期望结果 |
|---|---|---|
| 1. Celery worker 是否在线 | `docker logs contract_review_celery_worker --tail 5` | 看到 `celery@xxx ready.` |
| 2. Redis 队列是否堆积 | `docker exec contract_review_redis redis-cli -n 1 LLEN celery` | 0 = 已消费 |
| 3. 任务是否被收到 | `docker logs contract_review_celery_worker --tail 30 \| grep "Task.*received"` | 应有最近的任务记录 |
| 4. 任务是否报错 | `docker logs contract_review_celery_worker --tail 50 \| grep -E "ERROR\|Traceback"` | 无报错 |
| 5. 数据库状态 | `docker exec contract_review_postgres psql -U postgres -d contract_review -c "SELECT id, status, error_message FROM compliance_check_results ORDER BY requested_at DESC LIMIT 5;"` | 看具体状态 |

**孤儿记录修复**（超过 10 分钟还是 pending 的会被自动清理，但也可手动触发）：

```bash
# 后端启动时会自动扫描并重新投递孤儿任务（main.py 已实现）
docker restart contract_review_backend
```

### 故障 2：合规检查直接显示失败

看 `error_message` 字段，对照下表：

| error_message | 含义 | 修复 |
|---|---|---|
| `file_extraction_failed` | 文本抽取失败 | 检查容器是否有 python-docx / pdfplumber |
| `empty_extracted_text` | 抽取出的文本为空 | 合同是纯图片 PDF？换文件 |
| `ai_timeout` | AI 调用超时 | 检查 `AI_TIMEOUT` 是否够大（建议 ≥ 300） |
| `ai_invalid_response` | AI 返回的 JSON 无法解析 | 看 worker 日志 `raw=` 内容 |
| `task_lost` | 孤儿记录（worker 重建丢失） | 重新提交 |
| `import_transaction_failed` | DB 事务失败 | 看后端日志 traceback |

### 故障 3：AI 返回结果不一致 / 不准

LLM 的固有特性，无法完全消除。已做的改善：

- `temperature=0`
- 两阶段自检 prompt（见 `_COMPLIANCE_SYSTEM_PROMPT`）
- 后端关键词过滤（`compliant_keywords`）

如果差异过大，可考虑改为**每条规则单独调用 AI**（架构改动，未实施）。

### 故障 4：编辑/删除按钮无响应

通常是父组件没传回调函数。前端组件设计普遍用 `onXxx?.()` 形式，外层不传就是没反应。检查：

```
RuleTable / RuleSetTable 是否传了 onEdit / onCreateClick / onViewDetail
```

---

## 3. 部署相关

### 3.1 CI/CD 完整流程

```
git push origin develop
    ↓ GitHub Actions 触发 deploy-test.yml
    ↓ runner 上 checkout + scp 推送代码到服务器 /tmp/deploy_src
    ↓ rsync 到 /home/ubuntu/contract-review/（保留 .env）
    ↓ docker compose stop celery_worker（优雅退出，避免任务中断）
    ↓ docker compose build --no-cache backend frontend celery_worker
    ↓ docker compose up -d
    ↓ alembic upgrade head
    ↓ 健康检查
```

**总耗时**：约 8-10 分钟（前端 `--no-cache` build 最耗时）

### 3.2 关键改动后的部署清单

| 改动 | 必须重建的镜像 | 是否需要 alembic |
|---|---|---|
| 改 `requirements.txt` 加依赖 | backend + celery_worker | 否 |
| 改 backend 路由 / service 代码 | （bind mount 自动同步，重启即可） | 否 |
| 改 `models/*.py` ORM 字段 | （bind mount 同步） | **是**（需要建 migration） |
| 改前端代码 | frontend | 否 |
| 改 `docker-compose.yml` | 受影响的服务 | 否 |
| 改根目录 `.env` 或 `backend/.env` | 必须 `up -d` 而非 `restart` | 否 |

### 3.3 紧急热修（不走 CI/CD）

服务器上代码用 bind mount 同步，可以直接 scp + restart：

```bash
# 后端代码
scp -i kaifa.pem backend/app/services/xxx.py ubuntu@124.222.219.177:/home/ubuntu/contract-review/backend/app/services/
ssh -i kaifa.pem ubuntu@124.222.219.177 'docker restart contract_review_backend contract_review_celery_worker'
```

**注意**：热修必须当天 commit + push 回 git，避免下次 CI/CD 部署覆盖（参考 steering #17）。

---

## 4. 已踩过的坑（按主题分类）

### 4.1 依赖管理

#### 坑：requirements.txt 改了，但容器里没装新依赖

**症状**：`ModuleNotFoundError: No module named 'docx'` 或类似报错。

**根因**：CI/CD 之前没有重建 backend / celery_worker 镜像，只 rsync 了代码。bind mount 同步代码，但依赖装在镜像层，不会同步。

**修复**：CI/CD 已加上 `docker compose build --no-cache backend frontend celery_worker`，每次部署都重建。

**遗留问题**：每次部署都重新下载所有依赖，部署慢（8-10 分钟）。如果以后想优化，去掉 `--no-cache`，让 Docker layer cache 在 `requirements.txt` 不变时跳过 pip install。

---

### 4.2 Celery 异步任务

#### 坑：Celery worker 里 `minio_client` 未连接

**症状**：`RuntimeError: MinIO client not connected`

**根因**：MinIO 客户端的连接在 FastAPI 的 lifespan 里建立，Celery worker 是独立进程，不走 lifespan。

**修复**：在 task 里使用前手动 `connect()`：
```python
if minio_client.client is None:
    minio_client.connect()
```

#### 坑：asyncio event loop 冲突 (`got Future attached to a different loop`)

**症状**：Celery 任务执行 DB 查询时报 `RuntimeError: got Future attached to a different loop`

**根因**：`compliance_tasks.py` 里在模块级别创建了 SQLAlchemy `engine` 和 `sessionmaker`，绑定到模块导入时的 event loop。但 `asyncio.run()` 每次创建新 loop，导致连接池里的 Future 绑定旧 loop。

**修复**：每次任务执行时按需创建新的 engine + sessionmaker：
```python
def _make_session_factory():
    engine = create_async_engine(settings.DATABASE_URL, ...)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@celery_app.task(...)
async def my_task(self, ...):
    async with _make_session_factory()() as db:
        ...
```

#### 坑：CI/CD 重建容器导致正在执行的任务丢失（孤儿记录）

**症状**：DB 里某条记录长期 pending，Redis 队列空，worker 日志看不到对应任务。

**根因**：`docker compose up -d celery_worker` 重建容器时，正在执行的任务被 SIGKILL，DB 里的 pending 记录变成孤儿。

**修复**（三层防御）：
1. CI/CD 在重建前先 `docker compose stop celery_worker`，让 worker 优雅退出
2. 任务配置 `acks_late=True` + `reject_on_worker_lost=True` + `max_retries=2`
3. backend 启动时扫描并重新投递超过 2 分钟的孤儿 pending 记录（`main.py` lifespan）
4. `GET /checks` 列表接口自动清理超过 10 分钟的孤儿记录为 `failed`

---

### 4.3 SQLAlchemy async

#### 坑：`MissingGreenlet: greenlet_spawn has not been called`

**症状**：API 返回 500，traceback 里有 `MissingGreenlet`，定位到访问关联对象的代码。

**根因**：SQLAlchemy async session 的关联对象默认是 lazy load。`db.commit()` 后 session identity map 被清空，访问关联对象（如 `check_result.rule_set.rules`）会触发同步 IO，在 async 上下文外报错。

**修复**：用 `selectinload` 在查询时 eager load 所有需要访问的关联：
```python
result = await db.execute(
    select(ComplianceCheckResult)
    .where(ComplianceCheckResult.id == check_id)
    .options(
        selectinload(ComplianceCheckResult.rule_set).selectinload(ComplianceRuleSet.rules),
        selectinload(ComplianceCheckResult.requester),
    )
)
```

**规则**：commit 后还需要序列化访问关联的 ORM 对象，必须重新查询并 eager load。

---

### 4.4 Redis 客户端封装

#### 坑：`redis_client.get()` 自动 json.loads，再 `json.loads(raw)` 报错

**症状**：`TypeError: the JSON object must be str, bytes or bytearray, not list`

**根因**：项目里的 `RedisClient.get()` 内部已经做了 `json.loads`，返回的是 Python 对象，不是字符串。

**规则**：用项目的 `redis_client` 时，**不要**再手动 `json.loads`：
```python
# ❌ 错误
raw = await redis_client.get(key)
data = json.loads(raw)

# ✅ 正确
data = await redis_client.get(key)
```

`set` 同理：传非字符串值会自动 `json.dumps`。

---

### 4.5 AI / DeepSeek API

#### 坑：`AI_TIMEOUT=30` 导致合规检查总超时

**症状**：`APITimeoutError: Request timed out`，每次约 30 秒就超时。

**根因**：服务器 `backend/.env` 里有 `AI_TIMEOUT=30`（历史遗留），优先级高于 `config.py` 默认值 300。

**修复**：改 `.env`，重启容器。

#### 坑：OpenAI SDK 内置重试导致超时叠加

**症状**：明明 `timeout=120`，却 90 秒就报 `APITimeoutError`。

**根因**：OpenAI SDK 默认 `max_retries=2`，每次请求超时 30 秒，3 次叠加约 90 秒。我们代码里又有自己的 `for attempt in range(2)` 重试，两层叠加。

**修复**：
```python
self.client = AsyncOpenAI(
    api_key=settings.AI_API_KEY,
    timeout=settings.AI_TIMEOUT,
    max_retries=0,   # 禁用 SDK 内置重试
)
```

#### 坑：`deepseek-v4-pro` 不支持 `response_format=json_object`

**症状**：API 返回 200 但 `content=''`，导致 `json.loads('')` 失败，标 `ai_invalid_response`。

**根因**：`deepseek-v4-pro` 模型不支持 `response_format` 参数。简单测试不会触发，复杂的合规检查 prompt 必现。

**修复**：去掉 `response_format`，改用 `deepseek-chat`（官方 V3 名称，支持 json_object），或在 prompt 里强约束 JSON 格式。

#### 坑：AI 把合规项也列入 violations

**症状**：违规列表里出现 `"suggestion": "无需修改"` 的项。

**根因**：AI 的"过度尽职"——即使合规也想"汇报"一下。

**修复**（双保险）：
1. Prompt 里明确要求 violations 只列真正违规的项，不允许 suggestion 出现「无需修改」类表述
2. 后端 `_postprocess` 关键词过滤兜底：
```python
compliant_keywords = ("无需修改", "无需调整", "无须修改", "无须调整", "符合要求，无需", "已满足要求", "符合规定，无需")
if any(kw in suggestion for kw in compliant_keywords):
    continue
```

#### 坑：同一合同多次检查结果不一致

**现象**：同一合同 5 次检查，违规数 8-11，分数 0-20。

**根因**：LLM 的固有不确定性。即使 `temperature=0`，DeepSeek 推理引擎并行计算的浮点误差也会导致输出不完全一致。

**改善措施**：
1. `temperature=0`
2. 两阶段 prompt（先扫描，再自检复核）
3. 后端关键词过滤

**未做但可考虑的方案**：每条规则单独调用 AI（API 调用次数 ×N，但每条判断更稳定）。

---

### 4.6 前端 / 时间显示

#### 坑：时间显示与北京时间差 8 小时

**根因**：后端用 `datetime.utcnow()` 返回无时区后缀的 ISO 字符串，前端 `dayjs(val)` 默认按本地时间解析（实际是 UTC 0 解析成北京 +8）。

**修复**：用 `frontend/src/utils/time.ts` 里的 `formatToBeijing(val)`：
```typescript
import { formatToBeijing } from '../../utils/time';
// 替代所有 dayjs(val).format(...)
formatToBeijing(val)            // 默认 'YYYY-MM-DD HH:mm'
formatToBeijing(val, 'YYYY-MM-DD HH:mm:ss')
```

内部用 `Intl.DateTimeFormat` 强制转 `Asia/Shanghai`。

#### 坑：编辑按钮无响应

**根因**：父组件没传 `onEdit` 回调，`onClick={() => onEdit?.(record)}` 等于调用 undefined。

**排查**：在浏览器 React DevTools 看 props 是否传了 `onEdit`。

---

## 5. 数据库手工操作 Cheatsheet

```bash
# 进入 psql
docker exec -it contract_review_postgres psql -U postgres -d contract_review

# 看最近 5 条合规检查
SELECT id, status, error_message, requested_at
FROM compliance_check_results ORDER BY requested_at DESC LIMIT 5;

# 把孤儿 pending 标为 failed（10 分钟前）
UPDATE compliance_check_results
SET status='failed', error_message='task_lost'
WHERE status='pending' AND requested_at < NOW() - INTERVAL '10 minutes';

# 看某条检查的违规项
SELECT jsonb_pretty(violations::jsonb)
FROM compliance_check_results WHERE id='xxxx';

# 删除测试数据（保留生产）
DELETE FROM compliance_check_results WHERE requested_at < '2026-05-29';
```

```bash
# Redis 操作
docker exec contract_review_redis redis-cli -n 1 LLEN celery   # Celery 队列长度
docker exec contract_review_redis redis-cli -n 0 KEYS 'compliance:*'   # 主缓存里合规相关 key
docker exec contract_review_redis redis-cli -n 0 DEL compliance:active-rule-set   # 清生效规则集合缓存
```

```bash
# 重新投递某条孤儿任务（在 backend 容器内执行）
docker exec contract_review_backend python3 -c "
from app.tasks.compliance_tasks import run_compliance_check_task
run_compliance_check_task.delay('check_id_here')
"
```

---

## 6. 关键文件索引

### 后端
- `backend/app/services/compliance_service.py` — 主业务逻辑，含 `create_pending_check` / `_run_extraction_and_ai`
- `backend/app/services/ai_service.py` — DeepSeek 调用 + system prompt + 后处理
- `backend/app/services/compliance_import_service.py` — Excel 模板/解析/导入
- `backend/app/tasks/compliance_tasks.py` — Celery 异步任务
- `backend/app/routes/compliance.py` — 所有 `/api/compliance/*` 路由
- `backend/app/main.py` — 启动时孤儿任务恢复逻辑

### 前端
- `frontend/src/pages/Compliance/ComplianceCheckNewPage.tsx` — 提交合规检查页
- `frontend/src/pages/Compliance/ComplianceCheckDetailPage.tsx` — 详情页（含轮询）
- `frontend/src/pages/Compliance/ComplianceListPage.tsx` — 列表页（含权限按钮）
- `frontend/src/pages/Compliance/admin/RuleSetListPage.tsx` — 规则集合管理
- `frontend/src/components/Compliance/RuleImportModal.tsx` — Excel 导入弹窗
- `frontend/src/hooks/useCompliance.ts` — 所有合规相关 TanStack Query hooks
- `frontend/src/utils/time.ts` — `formatToBeijing` 时间格式化

### 配置 / 部署
- `docker-compose.yml` — 容器编排
- `.github/workflows/deploy-test.yml` — CI/CD
- `docs/ENV_CONFIG_REFERENCE.md` — 环境变量配置参考
- `docs/DUAL_ENV_DEPLOYMENT.md` — 双环境部署架构

### Spec
- `.kiro/specs/contract-compliance-check/` — 合规检查功能 spec
- `.kiro/specs/compliance-rule-excel-import/` — Excel 批量导入 spec

---

## 7. 给后续维护者的建议

1. **任何 Celery 任务相关改动，必须重启 worker**（`docker restart contract_review_celery_worker`），代码热更不会自动生效。

2. **改 prompt 后**，建议同一合同跑 3 次看稳定性。LLM 不可能 100% 一致，但波动应控制在 ±20% 以内。

3. **AI_TIMEOUT 不要低于 300 秒**。DeepSeek 处理大合同+多规则可能要 60-180 秒。

4. **新增 Pydantic Settings 配置项时**，必须同步在服务器 `backend/.env` 加上同名行，否则容器重启后用代码默认值会出现"本地能跑、线上失败"。

5. **改 ORM 字段 / 加表**，必须 `alembic revision --autogenerate -m "..."` 生成 migration 并推到 git，CI/CD 会自动 `alembic upgrade head`。

6. **服务器侧热修必须当天 commit 回 git**（参考 steering #17）。

7. **不要在 backend 路由里写耗时操作**（>5 秒）。所有 AI 调用、长时间任务都应该走 Celery。否则 Nginx 504、浏览器超时各种问题都会出现。

8. **测试合规检查必须用真实合同**，不能简化。某些 bug（比如 `response_format` 在长 prompt 下返回空）只在真实场景复现。

---

## 8. 历史时间线

| 日期 | 事件 |
|---|---|
| 2026-05-19 | `contract-revision-and-ai-improvements` 上线 |
| 2026-05-27 | 双环境（test + prod）部署完成 |
| 2026-05-28 | `compliance-rule-excel-import` 开发 + 上线，期间踩坑 N 个，本文档主要内容 |
| 2026-05-29 | 合规检查异步化（同步 → Celery） |
