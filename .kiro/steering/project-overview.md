---
inclusion: always
---

# 合同预审看板系统 - 项目总览

企业内部合同协同评审平台。多角色（销售/法务/财务/业务/运营/人事）协作完成合同的创建、评审、讨论、审批，集成 AI 智能辅助。

- **生产环境**：https://chenmin.yunumall.com
- **钉钉 OAuth 回调（dev via ngrok）**：https://underfed-isolating-prolonged.ngrok-free.dev/api/auth/dingtalk/callback

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 19 + TypeScript + Vite + Ant Design 6 + Zustand 5 + TanStack Query 5 + Axios + Socket.io-client + Day.js |
| 后端 | FastAPI 0.109+ + SQLAlchemy 2.0 (async/asyncpg) + python-socketio + Celery |
| 数据库 | PostgreSQL 15 |
| 缓存 | Redis 7 |
| 存储 | MinIO (S3 兼容) |
| 认证 | 钉钉 OAuth 2.0 + JWT (HS256, 24h) |
| AI | OpenAI SDK + DeepSeek API (`deepseek-v4-flash`) |
| 部署 | Docker Compose + Nginx + ngrok（dev tunneling） |

## 目录结构

```
frontend/src/
  components/    React 组件
  pages/         页面
  stores/        Zustand 状态（持久化到 localStorage）
  hooks/         自定义 hooks（含 TanStack Query hooks）
  utils/         工具函数（含 axios 实例）
  config/        socket.ts 等配置
  types/         TypeScript 类型定义

backend/app/
  core/          config, database, redis_client, minio_client,
                 auth_middleware, socketio_server, error_handler, logging_config
  models/        SQLAlchemy ORM (User, Contract, Review, Comment,
                 Attachment, AISummary, Notification, ContractRevisionLog)
  routes/        FastAPI 路由 (auth, contracts, reviews, files, ai, users,
                 notifications, dingtalk)
  services/      业务逻辑 (ai_service, contract_service, review_service,
                 comment_service, dingtalk_auth_service, file_service,
                 notification_service_v2)
  schemas/       Pydantic 请求/响应
  tasks/         Celery 任务
  utils/         工具函数

backend/alembic/versions/   数据库迁移脚本
```

## 数据模型核心字段

- **User**：`union_id`、`open_id`、`name`、`role`（销售/法务/财务/业务/运营/人事）、`avatar`
- **Contract**：`name`、`description`、`status`（progress/completed）、`initiator_id`、`cc_users`(JSON)、`contract_number`
- **Review**：`contract_id`、`reviewer_id`、`role`、`step`、`status`（pending/reviewing/approved）、`opinion`
- **Comment**：`contract_id`、`review_id`、`parent_comment_id`、`author_id`、`content`、`mentioned_user_ids`、`likes`
- **Attachment**：`contract_id`、`filename`、`file_key`(MinIO)、`file_size`、`uploader_id`、`version`
- **AISummary**：`contract_id`、`approval_status`、`completed_count`、`total_count`、`review_count`、`key_issues`(JSONB)
- **Notification**：`recipient_id`、`actor_id`、`type`、`contract_id`、`anchor_id`、`preview`、`is_read`
- **ContractRevisionLog**：`contract_id`、`revised_by`、`changed_fields`(ARRAY)、`revised_at`

## 状态管理

- **服务端状态**：TanStack Query 5（`frontend/src/hooks/`），staleTime 5min，gcTime 10min
- **客户端状态**：Zustand 5（`frontend/src/stores/`），通过 `zustand/persist` 持久化到 localStorage
- **Auth Token**：存于 Zustand（localStorage key 为 `'user-storage'`）。`App.tsx` 挂载时从 localStorage 读取 token 注入 store；axios 通过 `useUserStore.getState().token` 读取。

## ⚠️ 关键约定（违反就会出 bug）

### 1. 前端必须用 axios 实例，不能直接 import axios
```typescript
// ✅ 正确
import axiosInstance from '../utils/axios';

// ❌ 错误 —— 缺少 Authorization header
import axios from 'axios';
```

### 2. FastAPI 异常处理器必须在中间件之前注册
中间件是 LIFO（后注册的最先执行）。异常处理器在中间件内部就接不到所有异常。
```python
register_exception_handlers(app)             # 先注册（最外层）
app.add_middleware(BaseHTTPMiddleware, ...)  # 后注册（最内层）
```

### 3. SQLAlchemy 枚举必须用 values_callable
数据库存小写值，但 SQLAlchemy 默认序列化为大写。所有 `SQLEnum` 列必须：
```python
SQLEnum(MyEnum, values_callable=lambda x: [e.value for e in x])
```

### 4. 合同筛选有 7 个类型（不是 5 个）
`全部` / `进行中` / `已完成` / `待我处理` / `抄送我` / `我发起的` / `我已审批`
- `全部`、`进行中`、`已完成` 已叠加数据权限隔离（仅展示与当前用户相关的合同）
- `待我处理`、`抄送我`、`我发起的`、`我已审批` 按各自原有逻辑

### 5. 中文文件名下载必须 RFC 5987 编码 Content-Disposition
否则 HTTP 500（已在 `backend/app/routes/files.py` 实现）

### 6. Redis 缓存失效
合同列表 + 待办数量 TTL 5min；写操作（评审、评论、状态变更）必须主动清缓存。
未读通知数 TTL 60s。

### 7. Docker 部署 bind mount 必须挂上
`docker-compose.yml` 里 `./backend:/app` 不能注释。注释了就跑镜像里的旧代码，`rsync/scp` 同步无效。
排查：`docker inspect <container> --format='{{json .Mounts}}'` 看 Type 是否为 `bind`。

### 8. UUID 字段比较必须 str() 包一层
SQLAlchemy `Mapped[uuid.UUID]` 字段直接与字符串 `!=` 比较，结果**永远为 True**（review_service 的 reviewer_id 校验已踩过）。

```python
# ❌ 永远不等
if review.reviewer_id != reviewer_id_str:

# ✅ 正确
if str(review.reviewer_id) != str(reviewer_id_str):
```

### 9. 鉴权下载禁止用原生 `<a href>`
浏览器原生导航不走 axios 拦截器，没有 `Authorization` header → 401。文件下载必须走 `axios.get(url, { responseType: 'blob' })` + `URL.createObjectURL` + `<a download>`。

### 10. 钉钉用户身份的唯一标识必须用 unionId
两条代码路径写 `dingtalk_user_id`：通讯录拉成员写的是 staff userid，OAuth 登录写的是 unionId。同一个人会被拆成两条 user 记录 → 「待我处理」永远为空。

修复方案：登录 `sync_user_info` **优先按 `dingtalk_union_id == unionId` 匹配**，找到就只更新基础字段、不覆盖 `dingtalk_user_id`。新建用户也要同时填 `union_id` 和 `user_id`。

### 11. 钉钉 OAuth 回调必须返回 HTML（不是 JSON）
回调端点 `/api/auth/dingtalk/callback` 返回内嵌 JS 的 HTML 页面：JS 把 token + user 写到 `localStorage`（key 用 `'token'` 和 `'user'`），然后 `window.location.href = '/'`。`App.tsx` 挂载时再把 localStorage 的两个 key 迁到 Zustand store（key `'user-storage'`），并清掉旧 key。

### 12. 钉钉 redirect URI 三处必须一致
- `backend/.env` 的 `DINGTALK_REDIRECT_URI`
- `docker-compose.yml` 里 backend 的环境变量
- 钉钉开放平台「安全设置 → 重定向 URL」

少了路径或协议（必须 `https://...`）就会 `redirect_uri_mismatch` 死循环。修改钉钉控制台后如果仍报错，**删旧记录 → 保存 → 重加 → 保存**（开放平台有缓存）。

### 13. 候选人选择走钉钉接口，不是 `/api/users`
评审人/抄送人选人弹窗（`UserPicker`）调的是 `/api/dingtalk/users` 和 `/api/dingtalk/contacts`（含部门树）。`/api/users` 留作向后兼容，不删但不主动用。

### 14. `formatRelativeTime` 只接受 ISO 字符串
传 `Date` 对象进去会被 `normalizeIsoString` 处理成非法字符串 → `Invalid Date` → fallback 返回 Date 对象 → React 抛 "Objects are not valid as a React child" → ErrorBoundary 兜底显示「组件加载失败」。

```tsx
// ❌
formatRelativeTime(new Date(message.timestamp))

// ✅ message.timestamp 本身就是 ISO 字符串
formatRelativeTime(message.timestamp)
```

### 15. `pg_dump` 必须加 `--clean --if-exists`
迁移到新数据库时，目标库已经被 `alembic upgrade head` 建好结构，没加这两个参数 → 表结构冲突 → 数据全部跳过。
```bash
pg_dump -U postgres -d contract_review --no-owner --no-privileges --clean --if-exists > dump.sql
```

### 16. Antd Badge 的 offset 正值会被兄弟元素遮
`offset={[10, 0]}` 把红点推到按钮外面，被相邻按钮的渲染层级盖住。用法：
- `[-2, 6]` 贴角内嵌（推荐）
- `.ant-badge-count { z-index: 2 }` 兜底

### 17. 服务器侧热修必须回流到 git
"在服务器上 `vim` 改一改让它跑起来"是高频陷阱：
- 改完没提交 → CI/CD 重新拉代码就把热修覆盖了
- 改完没提交 → 换台机器或重建容器就丢了
- 改完没提交 → 别人 clone 仓库跑不起来

典型案例：`backend/Dockerfile` 在服务器上加过腾讯镜像源加速 build（apt + pip），但没回流到 git。导致后续在 GitHub Actions 里全新构建时走默认源，apt-get install 卡 30+ 分钟。

**规则**：所有服务器侧的临时改动**必须**当天回流到 git，不允许"我先这样能跑就好"。

### 18. 长 SSH 命令在腾讯云会被踢
`ssh ubuntu@server 'long-running-command'` 类型的连接，docker build 之类长时间无 stdout flush 会被腾讯云 SSH 网关切断（约 5 分钟 idle）。

**对策**：
- 短命令直接 SSH 跑
- 长命令在服务器上写脚本 + `nohup setsid xxx.sh < /dev/null > /tmp/log 2>&1 & disown`，脱离 SSH session
- 然后用独立的短 SSH 命令轮询 `/tmp/log` 看进度

## WebSocket 事件

Socket.io 嵌在 FastAPI 中。前端 `frontend/src/config/socket.ts` 连接，加入房间 `user:{user_id}` 和 `contract:{contract_id}`。

事件清单：
- `contract:updated` - 合同信息更新
- `contract:revised` - 发起人修改合同触发重审
- `review:added` - 新增评审
- `comment:added` - 新增评论
- `reply:added` - 新增回复
- `like:updated` - 点赞变化
- `pending:changed` - 待办数量变化
- `notification:new` - 新通知

## 常用命令

### 启动（开发）
```bash
docker compose up -d postgres redis minio
cd backend && alembic upgrade head && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm install && npm run dev
```

### 启动（一键）
```bash
docker compose up -d
docker compose exec backend alembic upgrade head
```

### 测试
```bash
cd backend && pytest
cd frontend && npm run test:e2e   # Playwright E2E
```

### 数据库迁移
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 访问 URL

| 服务 | 本地 dev | 生产 |
|---|---|---|
| 前端 | http://localhost:5173 | https://chenmin.yunumall.com |
| 后端 API | http://localhost:8000 | https://chenmin.yunumall.com/api |
| API 文档 | http://localhost:8000/docs | https://chenmin.yunumall.com/api/docs |
| MinIO 控制台 | http://localhost:9001 | (不对外) |

## Spec 演进脉络

`.kiro/specs/` 下三个 spec 按时间顺序叠加：

1. **contract-pre-review**（底座）—— 合同 CRUD、附件版本、评审时间线、评论嵌套回复、AI 总结+顾问、钉钉登录、WebSocket、Docker 部署
2. **contract-enhancements**（协作增强）—— 评论 @ 提及、消息通知中心、"我已审批"筛选、数据权限隔离
3. **contract-revision-and-ai-improvements**（最新一轮）—— 合同修改触发重审 + 审计日志、@ 候选人收窄到合同相关人员、AI 总结输出 `[ref:...]` 引用标记 + 长回复折叠

三个 spec 都已交付。新增功能优先看是否需要新建 spec。

## 限制

- ngrok 免费版有连接数限制
- 前端未实现虚拟滚动，1000+ 合同列表可能卡顿
- 移动端是响应式但未做 PWA

## Docker 部署 cheatsheet

改前端代码后部署不生效？先判断是哪种模式：

| 模式 | 标志 | 生效方式 |
|---|---|---|
| dev | `docker-compose.yml` 有 `./frontend:/app` 挂载 | Vite HMR 自动 |
| prod | 多阶段构建（`builder → nginx`），无源码挂载 | 必须 rebuild |

prod 模式下 `docker compose build` 可能命中缓存导致改动没进镜像 → **直接用 `--no-cache`**：

```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

浏览器还看到旧版？让用户 `Cmd+Shift+R` 硬刷新（Vite 哈希化静态资源会缓存）。

## 生产服务器架构（腾讯云）

```
用户 → 域名:443 → 宿主机 Nginx（80/443）
                   ├─ /        → 127.0.0.1:8080 (frontend 容器)
                   └─ /api/    → 127.0.0.1:8000 (backend 容器)
```

- 前端容器 `ports: "127.0.0.1:8080:80"`（不是 `80:80`），避免和宿主 Nginx 冲突
- SSL 证书走 Let's Encrypt，存在 `/etc/letsencrypt/live/<domain>/`
- 换域名时：宿主 Nginx config + 钉钉控制台 + backend `.env` 的 `DINGTALK_REDIRECT_URI` + CORS 三处同步

## 排查 500 错误的检查清单

1. **先看 docker logs**：`docker logs <container> --tail 100`，看 `Traceback`
2. **确认代码真的在跑**：`docker exec <container> cat /path/to/file.py | head -50`
3. **bind mount 检查**：`docker inspect <container> --format='{{json .Mounts}}'`，看是否真的挂上了
4. **Redis 缓存可能有脏数据**：`docker exec <redis> redis-cli FLUSHALL`
5. **前端"组件加载失败"先看浏览器 Console**，多半是渲染异常（如 14 条），而非网络问题

## 历史遗留文档

根目录下有 40+ 份 md（`*_FIXED.md`、`TASK_*_COMPLETE.md`、`FINAL_STATUS*.md` 等）是开发过程的打卡记录，多数已过时。当前权威信息源：
- 本 steering 文件
- `CLAUDE.md`
- `.kiro/specs/` 下三个 spec
- `DAILY_WORK_LOG_2026-05-19.md`（最近一次大改的实战记录，约定都已抽到本文件）
- `经验沉淀_腾讯云部署与域名迁移.md`（部署相关）
