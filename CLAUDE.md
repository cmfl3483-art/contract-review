# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**合同预审看板系统** (Contract Pre-Review Kanban System) — A web-based collaborative platform for managing internal contract pre-review workflows. Supports multi-role collaboration with contract creation, review, discussion, and approval features, plus AI-powered assistance via DeepSeek API.

**Production deployment**: https://chenmin.yunumall.com
**ngrok dev URL**: https://underfed-isolating-prolonged.ngrok-free.dev (DingTalk OAuth callback)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19 + TypeScript, Vite, Ant Design 6, Zustand 5, TanStack Query 5, Axios, Socket.io-client, Day.js |
| Backend | FastAPI 0.109+, SQLAlchemy 2.0 (async via asyncpg), python-socketio |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Storage | MinIO (S3-compatible object storage) |
| Auth | DingTalk OAuth 2.0 + JWT (HS256, 24h expiry) |
| Tasks | Celery (AI summaries, async processing) |
| AI | OpenAI SDK (DeepSeek API: model `deepseek-v4-flash`) |
| Infra | Docker + Docker Compose, Nginx, ngrok (dev tunneling) |

## Architecture

```
frontend/          → React SPA (Vite dev :5173, Nginx prod :80)
backend/app/       → FastAPI app (uvicorn :8000)
  ├── core/        → config, database, redis_client, minio_client, auth_middleware,
  │                  socketio_server, error_handler, logging_config
  ├── models/      → SQLAlchemy ORM models (User, Contract, Review, Comment,
  │                  Attachment, AISummary, ContractRevisionLog)
  ├── routes/      → API modules (auth, contracts, reviews, files, ai, users, notifications, dingtalk)
  ├── services/    → Business logic (ai_service, contract_service, review_service,
  │                  comment_service, dingtalk_auth_service, file_service)
  └── schemas/     → Pydantic request/response schemas
```

Frontend entries: `frontend/src/main.tsx` (bootstrap) + `frontend/src/App.tsx` (routing + auth)
Backend entry: `backend/app/main.py`

## State Management

- **Server state**: TanStack Query 5 — `frontend/src/hooks/` — staleTime 5min, gcTime 10min
- **Client state**: Zustand 5 — `frontend/src/stores/` — persisted to localStorage via `zustand/persist`
- **Auth token**: Stored in Zustand (key: `'user-storage'` in localStorage). `App.tsx` reads token from localStorage on mount and hydrates the store. Axios reads from Zustand store via `useUserStore.getState().token`.
- **⚠️ Critical**: All API hooks must import `axiosInstance` from `'../utils/axios'`, NOT `'axios'` directly — otherwise Authorization header is missing.

## Commands

### Development (manual)

```bash
# 1. Start infrastructure
docker compose up -d postgres redis minio

# 2. Backend — migrations then server
cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Frontend
cd frontend && npm install && npm run dev
```

### Docker Compose (all-in-one, recommended)

```bash
docker compose up -d
docker compose exec backend alembic upgrade head  # run migrations after first start
```

### Testing

```bash
# Backend
cd backend && pytest

# Frontend E2E (Playwright)
cd frontend && npm run test:e2e
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Key Configuration

- `backend/app/core/config.py` — pydantic-settings; critical env vars:
  - `DATABASE_URL` — PostgreSQL async connection string
  - `REDIS_URL` — Redis connection
  - `MINIO_ENDPOINT` — MinIO host:port
  - `SECRET_KEY` — JWT signing key
  - `DINGTALK_APP_KEY`, `DINGTALK_APP_SECRET` — OAuth credentials
  - `DINGTALK_REDIRECT_URI` — Must match the callback URL configured in DingTalk console
  - `AI_PROVIDER=deepseek`, `AI_API_KEY`, `AI_MODEL=deepseek-v4-flash`
- `frontend/.env` — `VITE_API_BASE_URL`, `VITE_WS_BASE_URL`
- Root `.env` — used by docker-compose for deployed services

### DingTalk OAuth Callback

The callback URL configured in DingTalk console is:
```
https://underfed-isolating-prolonged.ngrok-free.dev/api/auth/dingtalk/callback
```
For local dev, use `ngrok http 5173` (frontend port) and update the DingTalk console callback URL accordingly.

## Auth Flow

1. User clicks "钉钉登录" → `GET /api/auth/dingtalk/login` → redirect to DingTalk OAuth
2. DingTalk redirects to `/api/auth/dingtalk/callback?code=xxx`
3. Callback route exchanges code for access_token, fetches user info, creates/updates local User via `unionId`
4. Callback returns an HTML page with JS that saves JWT + user to localStorage and redirects to `/`
5. `App.tsx` reads localStorage on mount, hydrates Zustand store, sets axios Authorization header

## WebSocket

Socket.io server runs inside FastAPI via `python-socketio`. Frontend connects via `frontend/src/config/socket.ts`, joining rooms `user:{user_id}` and `contract:{contract_id}`. Events: `contract:updated`, `review:added`, `comment:added`, `reply:added`, `like:updated`, `pending:changed`.

## Important Implementation Notes (Lesser-Known Quirks)

### FastAPI Middleware Registration Order
Exception handlers must be registered BEFORE middleware. FastAPI middleware is LIFO (last registered = first executed). If exception handlers are inside middleware, they won't catch all exceptions.
```python
# ✅ Correct order
register_exception_handlers(app)  # registers HTTPException handler first (outermost)
app.add_middleware(BaseHTTPMiddleware, dispatch=AuthMiddleware())  # runs first (innermost)
```
See `backend/app/main.py` and `backend/app/core/error_handler.py`.

### SQLAlchemy Enum Serialization
Database stores lowercase enum values but SQLAlchemy defaults to uppercase. All `SQLEnum` columns must use `values_callable`:
```python
values_callable=lambda x: [e.value for e in x]
```
See `backend/app/models/contract.py` and `backend/app/models/__init__.py`.

### Contract Filter Types
`FilterBar` has 6 filter types (not 5): `全部` / `进行中` / `已完成` / `待我处理` / `抄送我` / `我发起的`. The last one is implemented in `frontend/src/utils/filter.ts` and `backend/app/services/contract_service.py`.

### Chinese Filenames
File downloads with Chinese characters caused HTTP 500. Fix: RFC 5987 encoding in Content-Disposition header (implemented in `backend/app/routes/files.py`).

### Redis Cache Invalidation
Contract list and pending count are cached in Redis (5min TTL). Cache is invalidated on contract status changes, review submissions, and comments. See `backend/app/services/contract_service.py`.

## Performance Optimizations (Implemented)

- `React.memo` on 8+ components to prevent unnecessary re-renders
- Debounced search (300ms) in `useDebouncedSearch` hook
- Throttled events via `useThrottle` hook
- Route-level code splitting with `React.lazy`
- Vite vendor chunking (manual chunks for antd, react, axios, etc.)
- Image lazy loading via `useImageLazyLoad` hook
- WebSocket reconnection with exponential backoff

## Error Handling (Implemented)

- Axios interceptor with automatic retry (exponential backoff: 1s, 2s, 4s)
- ErrorBoundary with error frequency detection
- Circuit breaker and timeout utilities in `frontend/src/utils/error.ts`
- `safeLocalStorage` wrapper for SSR compatibility
- WebSocket connection state tracking

## Access URLs

| Service | Local Dev | Production |
|---------|-----------|------------|
| Frontend | http://localhost:5173 | https://chenmin.yunumall.com |
| Backend API | http://localhost:8000 | https://chenmin.yunumall.com/api |
| API Docs | http://localhost:8000/docs | https://chenmin.yunumall.com/api/docs |
| MinIO Console | http://localhost:9001 | (not exposed externally) |

## Database Models

- **User** — DingTalk `union_id`, `open_id`, `name`, `role` (销售/法务/财务/业务/运营/人事), `avatar`
- **Contract** — `name`, `description`, `status` (进行中/已完成), `initiator_id`, `cc_users` (JSON), `contract_number`
- **Review** — `contract_id`, `reviewer_id`, `role`, `step`, `status`, `opinion`
- **Comment** — `contract_id`, `review_id`, `author_id`, `content`, `parent_comment_id`, `likes`
- **Attachment** — `contract_id`, `filename`, `file_key` (MinIO), `file_size`, `uploader_id`, `version`
- **AISummary** — `contract_id`, `approval_status`, `completed_count`, `total_count`, `review_count`, `key_issues`
- **ContractRevisionLog** — revision history

## Docker Deployment (Critical: Bind Mount)

When deploying via `docker-compose`, the backend `volumes` bind mount must be **uncommented** in `docker-compose.yml`:

```yaml
services:
  backend:
    volumes:
      - ./backend:/app   # ← MUST be uncommented for code changes to take effect
      - backend_logs:/app/logs
```

Without this, the container runs the **stale code baked into the image** at build time, even if you've synced new files via `rsync/scp`. All your code fixes will silently fail to deploy.

**How to verify bind mount is working:**
```bash
# Compare file dates inside container vs host — must match
sudo docker exec <container> ls -la /app/app/core/error_handler.py
ls -la backend/app/core/error_handler.py

# Inspect actual mount configuration
sudo docker inspect <container> --format='{{json .Mounts}}' | python3 -m json.tool
# A working bind mount shows: "Type": "bind", "Source": ".../backend", "Destination": "/app"
# If you only see named volumes (e.g. backend_logs), bind mount is NOT active
```

**Code update strategies:**
| Method | When to use | How it takes effect |
|--------|-------------|---------------------|
| bind mount (`./backend:/app`) | Dev/debugging | Restart container |
| `docker compose build` + up | Production CI/CD | Rebuilds image |
| `docker cp` | Temporary fixes only | Lost on container recreate |

**Debug 500 errors in Docker:**
1. **First**: `docker exec <container> cat /path/to/file.py` to confirm the running code matches your fix
2. Do NOT assume `rsync/scp` success = deployment success
3. Check `docker inspect` Mounts before assuming the bug is in the code

## Known Limitations

- ngrok free tier has connection limits
- Virtual scrolling not implemented (may have performance issues with 1000+ contracts)
- Mobile layout is responsive but not PWA-optimized
