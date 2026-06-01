# 项目交接文档

> 交接日期：2026-06-01
> 交接人：陈敏
> 项目：合同预审看板系统

---

## 1. 项目概况

企业内部合同协同评审平台，支持多角色（销售/法务/财务/业务/运营/人事）协作完成合同的创建、评审、讨论、审批，集成 AI 智能辅助和合规检查功能。

- **生产环境**：https://chenmin0922.online
- **测试环境**：https://chenmin.yunumall.com
- **代码仓库**：https://github.com/cmfl3483-art/contract-review（public）
- **服务器**：腾讯云 124.222.219.177（4C/4G/40G，test + prod 共用一台）

---

## 2. 当前版本状态（重要）

### 分支说明

| 分支 | 对应环境 | 部署方式 |
|---|---|---|
| `develop` | 测试环境（chenmin.yunumall.com） | push 后 GitHub Actions 自动部署 |
| `main` | 生产环境（chenmin0922.online） | push 后需人工审批，GitHub Actions 部署 |

### ⚠️ 版本差异：测试环境已有，生产环境没有

**`develop` 分支比 `main` 分支超前 37 个 commit。**

下表列出了测试环境已上线、**生产环境尚未部署**的所有内容：

| 类别 | 功能/改动 | 说明 |
|---|---|---|
| 🆕 新功能 | **合规检查** | 上传合同 → 选规则集合 → AI 自动检查 → 返回违规项 |
| 🆕 新功能 | **合规规则管理** | 创建/编辑/删除规则集合，支持多条同时生效 |
| 🆕 新功能 | **Excel 批量导入规则** | 下载模板 → 填写 → 上传预览 → 确认导入 |
| 🔧 架构改动 | 合规检查异步化 | 提交后立即返回，Celery worker 后台处理，前端轮询 |
| 🔧 架构改动 | 数据库新增 3 张表 | `compliance_rule_sets`、`compliance_rules`、`compliance_check_results` |
| 🐛 Bug 修复 | 规则集合编辑按钮无响应 | 已修复 |
| 🐛 Bug 修复 | 合规检查详情页无法滚动 | 已修复 |
| 🐛 Bug 修复 | 时间显示差 8 小时 | 改为北京时间 |
| 🐛 Bug 修复 | 规则列表序号全是 0 | 改为自动行号 |
| 🐛 Bug 修复 | 新建合规检查规则集合未校验必填 | 已修复 |
| ⚙️ CI/CD | 每次部署重建 backend/celery_worker 镜像 | 确保依赖包正确安装 |
| 🔒 安全 | pre-commit hook 防密钥泄露 | 本地提交时自动扫描 |

### 生产环境当前功能（main 分支）

生产环境目前**只有**以下功能，**没有**上表中的任何内容：

- 合同 CRUD、附件版本管理
- 评审时间线、评论嵌套回复
- AI 总结 + AI 顾问
- 钉钉 OAuth 登录
- WebSocket 实时通信
- 消息通知中心
- 合同修改触发重审 + 审计日志
- 数据库版本：alembic `004`（测试环境是 `006`）

---

## 3. 上生产的操作步骤

### 方案 A：直接把 develop 合并到 main（推荐）

测试环境已充分验证，可以直接上生产：

```bash
git checkout main
git merge develop
git push origin main
# → GitHub Actions 触发，等待人工审批
# → 打开 https://github.com/cmfl3483-art/contract-review/actions 点 Approve
# → 约 8-10 分钟后生产环境更新
```

**上生产后必须手动执行**（CI/CD 会自动跑，但确认一下）：
```bash
ssh -i kaifa.pem ubuntu@124.222.219.177
docker compose -f /home/ubuntu/contract-review-prod/docker-compose.prod.yml \
  --env-file /home/ubuntu/contract-review-prod/.env.prod -p prod \
  exec backend alembic upgrade head
```

这会在生产数据库创建合规相关的表（migration `f3a1b2c4` + `005` + `006`）。

### 方案 B：先改需求再上生产

如果需要在上生产前修改需求：

1. 在 `develop` 分支上修改代码
2. push 到 `develop` → 自动部署到测试环境验证
3. 验证通过后，`git checkout main && git merge develop && git push origin main`
4. 审批后自动部署到生产

**不建议直接在 `main` 上改代码**，应该走 develop → main 的流程。

---

## 4. 生产环境特殊配置

生产环境有独立的配置文件，**不在 git 里**，在服务器上手动维护：

- 路径：`/home/ubuntu/contract-review-prod/.env.prod`
- 参考模板：`docs/ENV_CONFIG_REFERENCE.md`（占位符版本）

生产环境需要配置的关键项（与测试环境不同）：
- `SECRET_KEY`：必须与测试环境不同（用 `openssl rand -base64 32` 生成）
- `AI_API_KEY`：DeepSeek API Key（测试和生产可以共用，也可以分开）
- `DINGTALK_APP_KEY/SECRET`：生产用 `dingwbwrz9jazgvxzeyh`，测试用 `dingkyxfjd5bhgtr78rc`
- `DATABASE_URL`：生产用 `contract_review_prod` 数据库
- `REDIS_URL`：生产用 db 3/4/5，测试用 db 0/1/2

---

## 5. 服务器运维

### SSH 登录
```bash
ssh -i kaifa.pem ubuntu@124.222.219.177
```
`kaifa.pem` 在本地，**不在 git 里**，需要单独交接。

### 容器管理

| 容器名 | 环境 | 作用 |
|---|---|---|
| `contract_review_backend` | test | FastAPI API |
| `contract_review_celery_worker` | test | Celery 异步任务（AI 合规检查） |
| `contract_review_frontend` | test | 前端 Nginx |
| `prod_backend` | prod | FastAPI API |
| `prod_celery_worker` | prod | Celery 异步任务 |
| `prod_frontend` | prod | 前端 Nginx |
| `contract_review_postgres` | 共享 | PostgreSQL（test + prod 共用） |
| `contract_review_redis` | 共享 | Redis（test + prod 共用） |
| `contract_review_minio` | 共享 | MinIO 文件存储 |

⚠️ **postgres/redis/minio 是共享的**，不要在 test 目录跑 `docker compose down`，会把 prod 也停掉。

### 磁盘维护（重要）

CI/CD 每次部署会积累 Docker build 缓存，**定期清理**：
```bash
docker builder prune -af
```
2026-06-01 曾因磁盘满（40G 用满）导致 postgres 崩溃，清理了 27GB 缓存后恢复。建议每月清理一次，或者磁盘使用率超过 80% 时清理。

---

## 6. 关键文档索引

| 文档 | 路径 | 内容 |
|---|---|---|
| 双环境部署架构 | `docs/DUAL_ENV_DEPLOYMENT.md` | 整体架构、CI/CD 流程、踩坑记录 |
| 环境变量配置参考 | `docs/ENV_CONFIG_REFERENCE.md` | 服务器 .env 结构、配置坑 |
| 合规检查排查指南 | `docs/CONTRACT_COMPLIANCE_TROUBLESHOOTING.md` | 故障排查、所有踩坑、DB/Redis 操作 |
| 项目总览（steering） | `.kiro/steering/project-overview.md` | 技术栈、目录结构、22 条关键约定 |
| 合规检查 spec | `.kiro/specs/contract-compliance-check/` | 需求、设计、任务 |
| Excel 导入 spec | `.kiro/specs/compliance-rule-excel-import/` | 需求、设计、任务 |

---

## 7. 待办事项 / 已知问题

### 需要接手人决策的

1. **合规检查结果稳定性**：同一合同多次检查结果可能有差异（LLM 固有特性）。已做优化（temperature=0、两阶段自检 prompt），但无法完全消除。如果业务要求更高稳定性，可考虑改为每条规则单独调用 AI（架构改动，未实施）。

2. **生产环境上线时机**：合规检查功能已在测试环境验证，可以上生产。上线前需确认：
   - 生产环境 `.env.prod` 里有 `AI_API_KEY`（DeepSeek key）
   - 生产环境 celery_worker 容器已启动（`prod_celery_worker`）
   - alembic migration 已在生产数据库执行

3. **CI/CD 部署时间**：每次部署约 8-10 分钟（前端 `--no-cache` build 耗时）。可以优化为只在 `requirements.txt` 或 `package.json` 变化时才重建镜像，其他时候用缓存，部署时间可降到 1-2 分钟。

### 已知小问题（不影响主流程）

- AI 合规检查偶发 `ai_invalid_response`（DeepSeek 服务端偶尔返回空内容），点「重新检查」重试即可
- 合规检查结果的违规数在多次检查间可能有 ±1-2 条差异（LLM 不确定性）

---

## 8. 账号与密钥交接清单

以下需要单独交接（不在 git 里）：

- [ ] `kaifa.pem` SSH 私钥
- [ ] 服务器 `/home/ubuntu/contract-review/.env`（test 环境变量）
- [ ] 服务器 `/home/ubuntu/contract-review-prod/.env.prod`（prod 环境变量）
- [ ] DeepSeek API Key（已更换，旧 key 已废弃）
- [ ] 钉钉开放平台账号（test 应用 `dingkyxfjd5bhgtr78rc`，prod 应用 `dingwbwrz9jazgvxzeyh`）
- [ ] 腾讯云控制台账号（服务器管理）
- [ ] GitHub 仓库权限（https://github.com/cmfl3483-art/contract-review）
- [ ] MinIO 控制台（http://124.222.219.177:9001，账号密码在 .env 里）

---

## 9. 快速上手

接手后第一件事：

```bash
# 1. 克隆仓库（拉 develop 分支，这是最新代码）
git clone -b develop https://github.com/cmfl3483-art/contract-review.git
cd contract-review

# 注意：main 分支是生产版本（旧），develop 是最新版本（含合规检查等新功能）
# 日常开发都在 develop 上，改完推 develop 自动部署测试环境

# 2. 启用 pre-commit hook（防止密钥泄露）
git config core.hooksPath .githooks

# 3. 查看当前测试环境状态
ssh -i kaifa.pem ubuntu@124.222.219.177 'docker ps --format "{{.Names}}\t{{.Status}}"'

# 4. 查看最近部署日志
# https://github.com/cmfl3483-art/contract-review/actions

# 5. 访问测试环境
# https://chenmin.yunumall.com
```

**日常开发流程**：
```
在 develop 上改代码
    ↓ git push origin develop
    ↓ GitHub Actions 自动部署到测试环境（约 8-10 分钟）
    ↓ 在 https://chenmin.yunumall.com 验证
    ↓ 验证通过后上生产：
git checkout main && git merge develop && git push origin main
    ↓ GitHub Actions 等待审批
    ↓ 打开 https://github.com/cmfl3483-art/contract-review/actions 点 Approve
    ↓ 约 8-10 分钟后 https://chenmin0922.online 更新
```

如有问题，优先查 `docs/CONTRACT_COMPLIANCE_TROUBLESHOOTING.md` 和 `docs/DUAL_ENV_DEPLOYMENT.md`。
