# 合同预审看板系统

一个基于Web的协作平台,用于管理企业内部合同的预审流程。支持多角色协同工作,提供合同创建、评审、讨论和审批功能,并集成AI辅助能力。

## ✨ 核心功能

### 1. 合同管理
- 📝 创建合同并指定评审人和抄送人
- 📋 合同列表展示和筛选 (全部/进行中/已完成/待我处理/抄送我)
- 🔍 按合同名称或发起人搜索
- 📊 待办数量实时统计

### 2. 评审流程
- ✅ 评审人审批合同
- 💬 评论和嵌套回复
- 👍 点赞评审意见和评论
- 📈 自动更新合同状态

### 3. 文件管理
- 📎 上传合同附件 (PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX)
- 📦 自动版本管理
- ⬇️ 文件下载和权限控制
- 🗂️ 按文件名分组展示

### 4. AI智能助手
- 🤖 智能总结审批进度和关键问题
- 💡 AI合同顾问问答
- 🎯 自动提取风险项和建议
- 🔄 支持DeepSeek API和自部署模型

### 5. 实时通信
- ⚡ WebSocket实时更新 (待实现)
- 🔔 新评论和状态变更通知
- 🔄 多客户端同步

### 6. 钉钉集成
- 🔐 钉钉OAuth授权登录
- 👤 自动同步用户信息
- 🎫 JWT Token认证

## 🏗️ 技术架构

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI库**: Ant Design 5
- **状态管理**: Zustand
- **数据获取**: React Query (TanStack Query)
- **HTTP客户端**: Axios
- **WebSocket**: Socket.io-client
- **日期处理**: Day.js
- **路由**: React Router

### 后端
- **框架**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **文件存储**: MinIO
- **认证**: 钉钉OAuth + JWT
- **任务队列**: Celery
- **WebSocket**: python-socketio
- **AI**: OpenAI SDK (兼容DeepSeek和自部署模型)

### 部署
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx (待配置)

## 📁 项目结构

```
contract-pre-review/
├── frontend/                    # 前端项目
│   ├── src/
│   │   ├── components/         # React组件
│   │   ├── pages/              # 页面组件
│   │   ├── stores/             # Zustand状态管理
│   │   ├── services/           # API服务
│   │   ├── hooks/              # 自定义Hooks
│   │   ├── utils/              # 工具函数
│   │   └── types/              # TypeScript类型定义
│   ├── package.json
│   └── vite.config.ts
├── backend/                     # 后端项目
│   ├── app/
│   │   ├── core/               # 核心配置
│   │   ├── models/             # 数据模型
│   │   ├── services/           # 业务逻辑
│   │   ├── routes/             # API路由
│   │   └── main.py             # 应用入口
│   ├── alembic/                # 数据库迁移
│   ├── requirements.txt
│   └── pyproject.toml
├── docker-compose.yml           # Docker Compose配置
├── start-backend.sh            # 后端启动脚本
├── start-frontend.sh           # 前端启动脚本
└── README.md                    # 项目说明
```

## 🚀 快速开始

### 前置要求

- **Node.js** 18+ 和 npm
- **Python** 3.11+
- **Docker** 和 Docker Compose
- **钉钉开放平台账号** (用于OAuth登录)
- **DeepSeek API Key** (可选,用于AI功能)

### 1. 克隆项目

```bash
git clone <repository-url>
cd contract-pre-review
```

### 2. 配置环境变量

#### 后端配置

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件,配置以下关键项:

```env
# 钉钉配置 (必需)
DINGTALK_APP_KEY=your-dingtalk-app-key
DINGTALK_APP_SECRET=your-dingtalk-app-secret
DINGTALK_REDIRECT_URI=http://localhost:5173/auth/callback

# JWT密钥 (必需,生产环境请更换)
SECRET_KEY=your-secret-key-change-in-production

# AI配置 (可选)
AI_PROVIDER=deepseek
AI_API_KEY=your-deepseek-api-key
AI_MODEL=deepseek-chat
```

#### 前端配置

```bash
cd frontend
cp .env.example .env
```

编辑 `.env` 文件:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=http://localhost:8000
```

### 3. 启动服务

#### 方式一: 使用启动脚本 (推荐)

```bash
# 启动后端 (在一个终端)
./start-backend.sh

# 启动前端 (在另一个终端)
./start-frontend.sh
```

#### 方式二: 手动启动

**启动Docker服务:**

```bash
docker-compose up -d
```

**启动后端:**

```bash
cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端:**

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问应用

- **前端**: http://localhost:5173
- **后端API文档**: http://localhost:8000/api/docs
- **MinIO控制台**: http://localhost:9001 (用户名/密码: minioadmin/minioadmin)

## 📖 使用指南

### 登录

1. 访问前端地址 http://localhost:5173
2. 点击"钉钉登录"按钮
3. 使用钉钉扫码或账号密码登录
4. 授权后自动跳转回应用

### 创建合同

1. 点击"发起合同预审"按钮
2. 填写合同名称和描述
3. 选择评审人和抄送人
4. 上传合同附件
5. 提交创建

### 评审合同

1. 在"待我处理"筛选中查看待审批合同
2. 点击合同查看详情
3. 在评审区域填写意见
4. 点击"同意"按钮提交

### 讨论和评论

1. 在时间线区域查看所有评审意见
2. 点击"回复"按钮添加评论
3. 支持嵌套回复
4. 可以点赞评审意见和评论

### AI助手

1. 在右侧AI顾问面板输入问题
2. 支持询问:
   - 法务意见是什么?
   - 有哪些风险项?
   - 待我处理的任务有哪些?
3. 查看AI智能总结 (自动生成)

## 🔧 开发指南

### 后端开发

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 创建数据库迁移
alembic revision --autogenerate -m "description"

# 运行迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload

# 运行测试
pytest
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 运行测试
npm run test

# 代码检查
npm run lint
```

### API文档

后端启动后访问:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 📊 数据库模型

### User (用户)
- 钉钉用户信息
- 角色 (销售/法务/财务/业务/运营/人事)

### Contract (合同)
- 合同基本信息
- 状态 (进行中/已完成)
- 发起人和抄送人

### Review (评审记录)
- 评审人和角色
- 评审意见和状态
- 点赞信息

### Comment (评论)
- 评论内容
- 支持嵌套回复
- 点赞信息

### Attachment (附件)
- 文件信息
- 版本管理
- MinIO存储键

### AISummary (AI总结)
- 审批进度
- 关键问题
- 自动生成

## 🔒 安全特性

- ✅ JWT Token认证
- ✅ 钉钉OAuth授权
- ✅ 文件类型和大小验证
- ✅ 权限验证 (文件下载)
- ✅ CORS配置
- ✅ SQL注入防护
- ✅ XSS防护 (React自动转义)

## 🎯 性能优化

- ✅ Redis缓存 (合同列表、待办数量、AI总结)
- ✅ 数据库索引优化
- ✅ 异步处理 (数据库、文件、AI)
- ✅ 连接池 (数据库、Redis)
- ⏳ 虚拟滚动 (前端,待实现)
- ⏳ 代码分割 (前端,待实现)

## 📝 待完成功能

### 高优先级
- [ ] WebSocket实时通信
- [ ] 前端组件开发
- [ ] Celery异步任务
- [ ] 单元测试和集成测试

### 中优先级
- [ ] 邮件通知
- [ ] 数据导出
- [ ] 审计日志
- [ ] API限流

### 低优先级
- [ ] 移动端适配
- [ ] 国际化支持
- [ ] 主题切换
- [ ] 数据统计和报表

## 🐛 故障排除

### Docker服务无法启动

```bash
# 检查端口占用
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9000  # MinIO

# 停止并重启
docker-compose down
docker-compose up -d
```

### 数据库连接失败

```bash
# 检查Docker服务状态
docker-compose ps

# 查看日志
docker-compose logs postgres

# 重新运行迁移
cd backend
alembic upgrade head
```

### 前端无法连接后端

1. 检查后端是否启动: http://localhost:8000/health
2. 检查CORS配置: `backend/app/core/config.py`
3. 检查前端环境变量: `frontend/.env`

### MinIO文件上传失败

```bash
# 检查MinIO服务
docker-compose logs minio

# 访问MinIO控制台
open http://localhost:9001

# 检查bucket是否创建
# 用户名/密码: minioadmin/minioadmin
```

## 📚 相关文档

- [后端开发完成总结](./BACKEND_COMPLETE.md)
- [实施进度](./IMPLEMENTATION_PROGRESS.md)
- [Docker配置说明](./DOCKER_SETUP.md)
- [需求文档](./.kiro/specs/contract-pre-review/requirements.md)
- [技术设计](./.kiro/specs/contract-pre-review/design.md)
- [任务列表](./.kiro/specs/contract-pre-review/tasks.md)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 团队

- **项目负责人**: [Your Name]
- **后端开发**: [Your Name]
- **前端开发**: [Your Name]
- **UI/UX设计**: [Your Name]

## 📞 联系方式

- **项目主页**: [GitHub Repository]
- **问题反馈**: [GitHub Issues]
- **邮箱**: your-email@example.com

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [React](https://react.dev/) - 用户界面库
- [Ant Design](https://ant.design/) - 企业级UI组件库
- [DeepSeek](https://www.deepseek.com/) - AI模型服务
- [钉钉开放平台](https://open.dingtalk.com/) - 企业通讯和协作平台

---

**注意**: 本项目仍在开发中,部分功能可能尚未完全实现。欢迎贡献代码和提出建议!


<!-- CI/CD Pipeline Active. Last validated deployment: 2026-05-27 -->
