# 🚀 合同预审系统 - 启动指南

## ✅ 已完成的配置

### 1. 环境变量配置
所有必要的密钥和配置已经设置好：

**后端配置** (`backend/.env`):
- ✅ 钉钉 AppKey: `dingkrwl72tqfsl781ns`
- ✅ 钉钉 AppSecret: 已配置
- ✅ DeepSeek API Key: 已配置
- ✅ DeepSeek 模型: `deepseek-v4-flash`
- ✅ JWT 密钥: 已生成强随机密钥
- ✅ 数据库、Redis、MinIO 配置: 已设置

**前端配置** (`frontend/.env`):
- ✅ API 地址: `http://localhost:8000`
- ✅ WebSocket 地址: `ws://localhost:8000`

### 2. Docker 服务
基础设施服务已启动：
- ✅ PostgreSQL (端口 5432)
- ✅ Redis (端口 6379)
- ✅ MinIO (端口 9000, 9001)

---

## ⚠️ 当前问题

由于你的系统使用了 **Python 3.14**（非常新的版本），一些 Python 包还不完全兼容。主要问题：

1. `asyncpg` 和 `pydantic-core` 需要从源码编译
2. 虚拟环境和系统 Python 版本混淆

---

## 🔧 解决方案

### 方案 1: 使用 Python 3.11 或 3.12（推荐）

Python 3.14 太新了，建议使用更稳定的版本：

```bash
# 安装 Python 3.11 或 3.12
brew install python@3.11

# 重新创建虚拟环境
cd /Users/cm/Documents/kiro/project/backend
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 方案 2: 使用 Docker Compose（最简单）

完全使用 Docker，避免 Python 版本问题：

```bash
cd /Users/cm/Documents/kiro/project

# 停止当前的服务
docker compose down

# 启动所有服务（包括后端和前端）
docker compose up -d

# 查看日志
docker compose logs -f

# 访问应用
# 前端: http://localhost
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

**注意**: 使用 Docker Compose 时，需要创建一个 `.env` 文件在项目根目录：

```bash
# 在项目根目录创建 .env 文件
cat > .env << 'EOF'
# 钉钉配置
DINGTALK_APP_KEY=dingkrwl72tqfsl781ns
DINGTALK_APP_SECRET=XcPgi6KsK1dU9cor1gANWQuYSym-yxw71xy8xeA1hufW-1QYX0XXK8_QM76vQSqB

# AI 配置
AI_PROVIDER=deepseek
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=sk-50b210fd06654e228bf4c85278174b95
AI_MODEL=deepseek-v4-flash

# JWT 密钥
SECRET_KEY=3JzN1P7IAKkCD5LfOD-gKtI5oV9cKh4spnQ4Suai9L0
EOF
```

### 方案 3: 手动启动（如果方案 1 成功）

如果你成功使用 Python 3.11/3.12 重新创建了虚拟环境：

**终端 1 - 后端**:
```bash
cd /Users/cm/Documents/kiro/project/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**终端 2 - 前端**:
```bash
cd /Users/cm/Documents/kiro/project/frontend
npm install  # 首次运行需要
npm run dev
```

---

## 📍 访问地址

### 使用 Docker Compose:
- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **MinIO 控制台**: http://localhost:9001 (用户名/密码: minioadmin/minioadmin)

### 手动启动:
- **前端**: http://localhost:5173 (Vite 开发服务器)
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **MinIO 控制台**: http://localhost:9001

---

## 🔍 验证服务

### 1. 检查后端健康状态
```bash
curl http://localhost:8000/health
```

应该返回:
```json
{
  "status": "healthy",
  "timestamp": "..."
}
```

### 2. 查看 API 文档
浏览器访问: http://localhost:8000/docs

### 3. 检查 Docker 服务
```bash
docker compose ps
```

---

## 🐛 常见问题

### 问题 1: 端口被占用
```bash
# 查看端口占用
lsof -i :8000
lsof -i :5173

# 停止占用端口的进程
kill -9 <PID>
```

### 问题 2: Docker 服务无法启动
```bash
# 停止所有服务
docker compose down

# 清理并重新启动
docker system prune -f
docker compose up -d
```

### 问题 3: 数据库连接失败
```bash
# 检查 PostgreSQL 状态
docker compose logs postgres

# 重启 PostgreSQL
docker compose restart postgres
```

### 问题 4: Python 包安装失败
如果使用 Python 3.14 遇到问题，请切换到 Python 3.11 或 3.12（见方案 1）

---

## 💡 我的建议

**推荐使用方案 2（Docker Compose）**，因为：

1. ✅ 无需担心 Python 版本兼容性
2. ✅ 一键启动所有服务
3. ✅ 环境隔离，不影响系统
4. ✅ 与生产环境一致
5. ✅ 容易清理和重置

只需要：
1. 在项目根目录创建 `.env` 文件（见上面的内容）
2. 运行 `docker compose up -d`
3. 访问 http://localhost

---

## 📞 关于钉钉回调

由于你没有公网 IP，钉钉 OAuth 登录可能无法正常工作。解决方案：

### 临时方案: 使用内网穿透
```bash
# 安装 ngrok
brew install ngrok

# 启动内网穿透（前端端口）
ngrok http 3000

# 会得到一个公网地址，如: https://xxxx.ngrok.io
# 将这个地址配置到钉钉开放平台的回调地址
```

### 测试方案: 跳过登录
直接使用 API 文档测试功能: http://localhost:8000/docs

---

## 📚 下一步

1. **启动服务**（推荐使用 Docker Compose）
2. **访问 API 文档**: http://localhost:8000/docs
3. **测试健康检查**: `curl http://localhost:8000/health`
4. **查看 MinIO**: http://localhost:9001
5. **配置钉钉回调**（如果需要登录功能）

---

## 🎯 快速命令参考

```bash
# Docker Compose 方式
cd /Users/cm/Documents/kiro/project
docker compose up -d              # 启动所有服务
docker compose ps                 # 查看服务状态
docker compose logs -f            # 查看日志
docker compose down               # 停止所有服务

# 手动方式（需要先解决 Python 版本问题）
./start-services.sh               # 启动基础设施
./start-backend.sh                # 启动后端（新终端）
./start-frontend.sh               # 启动前端（新终端）
```

---

需要帮助？请告诉我你选择哪个方案，我会继续协助你！
