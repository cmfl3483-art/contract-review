# 合同预审看板系统 - 问题修复总结

## 修复日期
2026-05-19

## 已修复的问题

### 1. Authorization 头缺失问题
**问题**: 前端请求没有发送 Authorization 头，导致后端返回 401 错误
**原因**: 
- 所有 hooks 和组件直接从 'axios' 包导入，而不是使用配置好的 `axiosInstance`
- 只有 `axiosInstance` 有请求拦截器来添加 Authorization 头

**修复**:
- 修改所有 hooks 从 `'../utils/axios'` 导入
- 修改 `ContractForm.tsx` 从 `'../../utils/axios'` 导入
- 重新构建前端

**文件**:
- `frontend/src/hooks/useContracts.ts`
- `frontend/src/hooks/useAI.ts`
- `frontend/src/hooks/useAuth.ts`
- `frontend/src/hooks/useAttachments.ts`
- `frontend/src/hooks/useReviews.ts`
- `frontend/src/components/ContractForm/ContractForm.tsx`

### 2. SQLAlchemy Enum 序列化问题
**问题**: 数据库 enum 值是小写（如 "pending"），但 SQLAlchemy 传递的是大写（如 "PENDING"）
**原因**: SQLAlchemy 默认使用 enum 的 `.name` 而不是 `.value`

**修复**:
- 为所有 `SQLEnum` 添加 `values_callable=lambda x: [e.value for e in x]` 参数
- 修复了 3 个 enum 类型：
  * `ReviewStatus` (pending, reviewing, approved)
  * `ContractStatus` (progress, completed)
  * `ApprovalStatus` (completed, in_progress)

**文件**:
- `backend/app/models/review.py`
- `backend/app/models/contract.py`
- `backend/app/models/ai_summary.py`

### 3. 用户列表使用 Mock 数据问题
**问题**: 前端使用 Mock 用户数据（'user1', 'user2'），导致创建合同时 UUID 验证失败
**原因**: 没有用户列表 API，前端使用硬编码的测试数据

**修复**:
- 创建用户列表 API: `GET /api/users/list`
- 添加 8 个测试用户到数据库
- 修改前端从 API 获取真实用户列表
- 前端在打开表单时自动加载用户列表

**文件**:
- `backend/app/routes/users.py` (新建)
- `backend/app/main.py` (注册路由)
- `frontend/src/components/ContractForm/ContractForm.tsx`

**测试用户**:
- 张三 (销售)
- 李四 (法务)
- 王五 (财务)
- 赵六 (业务)
- 钱七 (运营)
- 孙八 (人事)
- 周九 (法务)
- 吴十 (财务)

### 4. 合同列表重复格式化问题
**问题**: 获取合同列表时报错 "'dict' object has no attribute 'id'"
**原因**: `contract_service.get_contract_list()` 已经返回格式化的字典，但路由代码又试图将它们当作对象来访问属性

**修复**:
- 修改 `contracts.py` 路由，直接使用 service 返回的格式化数据
- 删除重复的格式化代码

**文件**:
- `backend/app/routes/contracts.py`

### 5. Redis 缓存包含错误数据
**问题**: 修复后仍然返回错误，因为 Redis 缓存了旧的错误响应
**修复**: 清空 Redis 缓存 `redis-cli FLUSHALL`

## 系统当前状态

### 后端服务
- ✅ PostgreSQL: 运行正常
- ✅ Redis: 运行正常
- ✅ MinIO: 运行正常
- ✅ Backend API: 运行正常 (端口 8000)
- ✅ Celery Worker: 运行正常

### 前端服务
- ✅ Frontend: 运行正常 (Nginx)
- ✅ ngrok 隧道: `https://underfed-isolating-prolonged.ngrok-free.dev`

### 数据库
- ✅ 用户表: 9 个用户（1 个真实用户 + 8 个测试用户）
- ✅ 合同表: 1 个测试合同
- ✅ 评审表: 1 个评审记录
- ✅ 所有表结构正常

### API 测试结果
- ✅ `GET /api/users/list` - 200 OK
- ✅ `GET /api/contracts` - 200 OK
- ✅ `GET /api/contracts/{id}` - 200 OK
- ✅ `POST /api/contracts` - 200 OK
- ✅ `GET /api/contracts?filter=待我处理` - 200 OK

## 功能验证

### 已验证功能
1. ✅ 钉钉 OAuth 登录
2. ✅ Token 持久化（Zustand + localStorage）
3. ✅ Authorization 头自动添加
4. ✅ 用户列表获取
5. ✅ 合同创建
6. ✅ 合同列表查询
7. ✅ 合同详情查询
8. ✅ 筛选功能（全部/进行中/待我处理）

### 待验证功能
- ⏳ 合同详情页面显示
- ⏳ 评审功能
- ⏳ 评论功能
- ⏳ 附件上传
- ⏳ AI 总结

## 使用说明

### 访问系统
1. 打开浏览器访问: `https://underfed-isolating-prolonged.ngrok-free.dev`
2. 自动跳转到钉钉登录
3. 登录后进入合同列表页面

### 创建合同
1. 点击"发起合同预审"按钮
2. 填写合同名称和描述
3. 选择评审人（从真实用户列表中选择）
4. 可选：选择抄送人
5. 可选：上传附件
6. 点击"提交"

### 查看合同
1. 在合同列表中点击任意合同
2. 查看合同详情、评审状态、附件等

## 技术栈

### 后端
- FastAPI 0.104+
- SQLAlchemy 2.0+ (异步)
- PostgreSQL 15
- Redis 7
- MinIO
- Celery
- DeepSeek AI API

### 前端
- React 18
- TypeScript
- Ant Design 5
- React Query (TanStack Query)
- Zustand (状态管理)
- Axios
- Socket.IO Client

## 环境变量

### 后端 (.env)
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/contract_review
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
SECRET_KEY=3JzN1P7IAKkCD5LfOD-gKtI5oV9cKh4spnQ4Suai9L0
DINGTALK_APP_KEY=dingkyxfjd5bhgtr78rc
DINGTALK_APP_SECRET=PiNGAGUjtoh4byvBgNS-ZISS97COd7y4QftrFhGC8_ynuBS7N3B5aOeyMEhST2ag
DINGTALK_REDIRECT_URI=https://underfed-isolating-prolonged.ngrok-free.dev/api/auth/dingtalk/callback
AI_API_KEY=sk-50b210fd06654e228bf4c85278174b95
AI_MODEL=deepseek-v4-flash
```

## 故障排查

### 如果遇到 500 错误
1. 检查后端日志: `docker-compose logs backend --tail=50`
2. 检查数据库连接: `docker-compose ps postgres`
3. 清除 Redis 缓存: `docker-compose exec redis redis-cli FLUSHALL`
4. 重启后端: `docker-compose restart backend`

### 如果前端显示错误
1. 清除浏览器缓存: `Command + Option + E` (Safari)
2. 强制刷新: `Command + Shift + R`
3. 检查前端日志: `docker-compose logs frontend --tail=50`
4. 重新构建前端: `docker-compose build --no-cache frontend && docker-compose up -d frontend`

### 如果 Authorization 头缺失
1. 检查 localStorage: 在控制台运行 `localStorage.getItem('user-storage')`
2. 检查 token 是否存在
3. 重新登录

## 下一步

1. 验证合同详情页面是否正常显示
2. 测试评审功能
3. 测试评论功能
4. 测试附件上传
5. 测试 AI 总结生成

## 联系信息

如有问题，请检查：
1. 后端日志
2. 前端控制台
3. 网络请求（Network 标签）
4. Redis 缓存状态
