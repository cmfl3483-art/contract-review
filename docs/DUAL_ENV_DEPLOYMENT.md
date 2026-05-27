# 双环境部署 + CI/CD 经验沉淀

> 完成日期：2026-05-27
> 范围：将单环境系统拆为 test + prod 双环境，并接入 GitHub Actions 自动化部署
> 目标读者：项目接手人 / AI 编码助手 / 未来的自己

## 0. TL;DR（30 秒读完）

- **架构**：腾讯云 4C/4G 单机，跑两套独立应用栈（test + prod），共享一份基础设施（postgres/redis/minio），通过不同 DB / Redis db / bucket 物理隔离数据
- **域名**：test → `chenmin.yunumall.com`，prod → `chenmin0922.online`
- **钉钉**：两个独立应用，AppKey 各自独立配回调
- **代码**：单仓库双分支：`develop` → 自动部署 test，`main` → 审批后部署 prod
- **CI/CD**：GitHub Actions + SSH，从 push 到部署完成约 1 分钟
- **服务器目录**：test 在 `/home/ubuntu/contract-review/`，prod 在 `/home/ubuntu/contract-review-prod/`，**两个目录都是独立 git repo**

完整架构图、命令、踩坑见后文。

---

## 1. 为什么需要双环境

之前项目只有一套部署（在 `chenmin.yunumall.com`），事实上就是大家测试 + 数据上线混着用。痛点：

- 想验证一个改动会不会出问题，没有干净环境可测
- 真实合同数据和测试合同混在一个库里，不敢删
- 想做 CI/CD 但没有"先 test 再 prod"的流转目标

目标：

- **test 环境**：随便折腾，挂了不要紧
- **prod 环境**：稳定，库里只放真实业务数据
- **互不干扰**：test 跑挂不能影响 prod 用户

## 2. 关键架构决策（连同被否决的方案）

### 决策 1：1 个仓库 + 多分支，不是 N 个仓库

**否决方案**：3 个仓库（dev/test/prod 各一套代码） — 改一个 bug 要改 3 遍 = 灾难
**采纳方案**：单仓库，分支代表环境
- `main` → prod
- `develop` → test
- `feature/*` → 本地开发

### 决策 2：方案 B 共享基础设施（不是各跑一套）

**否决方案 A**：test 和 prod 各跑一套完整栈（postgres/redis/minio + 应用）
- 内存预估：test 1.2G + prod 1.2G + 系统 ≈ 3.5G+，4G 服务器吃不消

**采纳方案 B**：基础设施只一份，应用层各一份
- postgres：一个进程，两个 DB（`contract_review` 和 `contract_review_prod`）
- redis：一个进程，不同 db number（test 用 0/1/2，prod 用 3/4/5）
- minio：一个进程，两个 bucket（`contract-attachments` 和 `contract-attachments-prod`）
- 应用层各跑一份（backend、celery_worker、frontend）

**实现技巧**：prod 的 docker-compose 通过 `external network` 加入 test 那套已存在的 Docker network，从而能用 `postgres`/`redis`/`minio` 这些容器别名访问。

```yaml
# docker-compose.prod.yml 末尾
networks:
  shared:
    name: contract-review_contract_review_network
    external: true
```

**风险提醒（已写进 SOP 和 steering）**：test 跑挂 postgres 进程会同时影响 prod。所以**不要在 test 上跑大压测**。

### 决策 3：端口分配

| 项 | test（保持现状）| prod（新搭）|
|---|---|---|
| frontend | `127.0.0.1:8080` | `127.0.0.1:8090` |
| backend | `0.0.0.0:8000` | `127.0.0.1:8001` |
| celery | 内部 | 内部 |

prod 全部绑定 127.0.0.1，由宿主 Nginx 反代到外网。

### 决策 4：钉钉应用拆分

- `dingkyxfjd5bhgtr78rc`（test）→ 回调 `https://chenmin.yunumall.com/api/auth/dingtalk/callback`
- `dingwbwrz9jazgvxzeyh`（prod）→ 回调 `https://chenmin0922.online/api/auth/dingtalk/callback`

**为什么要拆**：避免开发时不小心把 test 流量打到 prod 钉钉应用，或反过来。代价是 prod 应用要重新申请所有权限。

### 决策 5：bind mount 保留

`docker-compose.prod.yml` 仍配 `./backend:/app` 卷挂载，**不**走纯镜像内代码模式。代价：镜像里的代码和真实运行的代码可能不一致；好处：`git pull` 后 `docker restart prod_backend` 立即生效，不用重 build。

历史教训（CLAUDE.md 已写）：本项目踩过"bind mount 被注释掉但 rsync 改了文件"的坑，运行的是镜像内旧代码。所以**保留 bind mount + 强制 git pull** 是当前最稳的做法。

### 共享层连带影响速查

方案 B 共享基础设施意味着 test 的 `docker-compose.yml` 同时管着 postgres/redis/minio。日常 CI/CD 推 develop 是安全的（docker compose 智能识别哪些服务定义没变就不重启），但有几种操作会拖累 prod：

| 操作 | 触发 docker compose 重建？ | prod 影响 |
|---|---|---|
| 改 backend/celery/frontend 镜像构建上下文 | 这些服务重建 | ❌ 不影响 |
| 改 backend 的 environment 段 | backend 重启 | ❌ 不影响 |
| 改 backend 的 volume 挂载 | backend 重建 | ❌ 不影响 |
| **改 postgres/redis/minio 的镜像版本** | 共享层重建 | ⚠️ 数秒失连 |
| **改 postgres/redis/minio 的 environment** | 共享层重建 | ⚠️ 数秒失连 |
| **改 postgres/redis/minio 的 volume** | 共享层重建 | ⚠️ 数秒失连，⚠️ 数据迁移风险 |
| **`docker compose down`** | 全停 | 💀 完全挂 |
| **`docker restart contract_review_postgres`** | 重启 postgres | ⚠️ 数秒失连 |

防护规则（已写进 steering #20）：
1. 不要在 test 目录跑 `docker compose down`
2. 改 postgres/redis/minio 的服务定义前先告知团队，选低峰期
3. 真要停 test 应用层只用 `docker compose -f docker-compose.yml stop backend celery_worker frontend`，不要 `down`
4. 如果以后频繁要动共享层，可以做"方案 B 升级版"：把 postgres/redis/minio 抽到 `docker-compose.shared.yml`，test 和 prod 都通过 external network 引用，彻底分离

## 3. 完整架构

```
┌────────────────────────────────────────────────────────────────────┐
│                        GitHub                                      │
│                                                                    │
│   feature/* ─► PR ─► develop ───────► Actions: deploy-test          │
│                                              ↓                      │
│                                       自动部署                       │
│                                                                    │
│   develop ───► PR ─► main ──────────► Actions: deploy-prod          │
│                                              ↓                      │
│                                       要求审批                       │
└──────────────────────────────────┬─────────────────────────────────┘
                                   │ SSH (kaifa.pem)
                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│  腾讯云服务器 124.222.219.177 (4C/4G/40G + 2G Swap)                │
│                                                                    │
│  ┌────────── 宿主 Nginx (80/443) ─ Let's Encrypt ──────────────┐ │
│  │  chenmin.yunumall.com    → 127.0.0.1:8080 (test 前端)         │ │
│  │                          → 127.0.0.1:8000 (test 后端 /api)    │ │
│  │  chenmin0922.online      → 127.0.0.1:8090 (prod 前端)         │ │
│  │                          → 127.0.0.1:8001 (prod 后端 /api)    │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─────── /home/ubuntu/contract-review/ (test) ─────────┐         │
│  │  git: develop branch                                  │         │
│  │  docker compose -f docker-compose.yml ...            │         │
│  │  容器：contract_review_backend / frontend /            │         │
│  │       celery_worker (各自连共享层)                     │         │
│  └───────────────────────────────────────────────────────┘         │
│                                                                    │
│  ┌─────── /home/ubuntu/contract-review-prod/ (prod) ────┐         │
│  │  git: main branch                                     │         │
│  │  docker compose -f docker-compose.prod.yml \         │         │
│  │      --env-file .env.prod -p prod ...                │         │
│  │  容器：prod_backend / prod_frontend /                  │         │
│  │       prod_celery_worker (各自连共享层)                │         │
│  └───────────────────────────────────────────────────────┘         │
│                                                                    │
│  ┌─────── 共享基础设施层 ─────────────────────────────────┐         │
│  │  contract_review_postgres :5432                        │         │
│  │     ├─ DB: contract_review       (test)                │         │
│  │     └─ DB: contract_review_prod  (prod)                │         │
│  │  contract_review_redis :6379                           │         │
│  │     ├─ db 0/1/2 (test 主/celery_broker/celery_result)  │         │
│  │     └─ db 3/4/5 (prod 主/celery_broker/celery_result)  │         │
│  │  contract_review_minio :9000                           │         │
│  │     ├─ contract-attachments       (test)               │         │
│  │     └─ contract-attachments-prod  (prod)               │         │
│  │  Docker network: contract-review_contract_review_network│        │
│  └────────────────────────────────────────────────────────┘         │
│                                                                    │
│  内存预估：基础设施 ~800MB + test ~600MB + prod ~600MB ≈ 2GB        │
│           系统/Docker daemon ~500MB，剩 ~700MB-1GB 可用            │
└────────────────────────────────────────────────────────────────────┘
```

## 4. 关键文件清单（项目里的）

| 文件 | 作用 | 谁会动它 |
|---|---|---|
| `docker-compose.yml` | test 环境编排，所有基础设施 + test 应用 | 推到 develop 分支会被部署 |
| `docker-compose.prod.yml` | prod 应用层（不含基础设施，加入共享 network） | 推到 main 分支会被部署 |
| `.env` | test 环境变量（**仅服务器上**，git 不跟踪）| 服务器上手动维护 |
| `.env.prod` | prod 环境变量（**仅服务器上**，git 不跟踪）| 服务器上手动维护 |
| `.env.prod.example` | prod 模板，供新服务器初始化时参考 | git 跟踪，无敏感值 |
| `nginx/chenmin0922.online.conf` | 宿主 Nginx 站点配置（部署时复制到 `/etc/nginx/sites-available/`）| git 跟踪 |
| `.github/workflows/deploy-test.yml` | develop 分支推送触发的 workflow | git 跟踪 |
| `.github/workflows/deploy-prod.yml` | main 分支推送触发的 workflow（带审批门槛）| git 跟踪 |
| `docs/PROD_DEPLOYMENT_SOP.md` | 从零搭 prod 的一次性 runbook | git 跟踪 |
| `docs/DUAL_ENV_DEPLOYMENT.md` | 本文，整体经验沉淀 | git 跟踪 |
| `docs/CICD_QUICK_REFERENCE.md` | 日常操作速查 | git 跟踪 |
| `kaifa.pem` | SSH 私钥 | **绝对不能进 git**（在 .gitignore 里）|

## 5. 日常工作流（已通过端到端验证）

### 5.1 开发阶段
```bash
# 在 main 或 feature/* 分支写代码
git checkout main
git pull origin main
git checkout -b feature/some-feature

# 改代码，本地跑通
# ...

# 提交
git add .
git commit -m "feat: ..."
```

### 5.2 部署到 test
```bash
# 合到 develop
git checkout develop
git merge feature/some-feature
git push origin develop

# → 自动触发 GitHub Actions deploy-test
# → 1 分钟内服务器上 test 容器重建
# → 浏览器打开 https://chenmin.yunumall.com 验证
```

### 5.3 部署到 prod
```bash
# test 验证通过后，合到 main
git checkout main
git merge develop  # 或 git merge feature/some-feature
git push origin main

# → GitHub Actions deploy-prod 触发，但停在 "Waiting for review"
# → GitHub 邮件通知你审批
# → 打开 GitHub Actions 页面，点 Approve
# → 1 分钟内 prod 容器重建
# → 浏览器打开 https://chenmin0922.online 验证
```

### 5.4 紧急回滚 prod
```bash
# 找到上一个稳定的 commit
git log --oneline -5

# 创建 revert commit（不要用 reset --hard 改写历史）
git checkout main
git revert <bad-commit-hash>
git push origin main
# → 走正常审批 + 部署流程，1 分钟回滚
```

⚠️ **数据库迁移没有自动回滚**。如果新版本加了破坏性 schema（比如删了列），代码回滚后旧版可能跑不起来。这种情况要么准备 down migration，要么从备份恢复 DB。预防：避免破坏性 migration、保留向后兼容。

## 6. 一次性搭建过程（按时间顺序记录）

### 6.1 准备阶段（git 整理）

服务器上之前是 rsync 同步的，**不是 git repo**。GitHub 上代码是几个月前的版本，本地有大量未提交改动。先理清：

1. 加固 `.gitignore`：屏蔽 `*.pem`、`.env*`、`node_modules`、`*.png`、临时脚本等
2. 把根目录 40 份打卡 md（`TASK_*_COMPLETE.md`、`*_FIXED.md`、`FINAL_STATUS_*.md` 等）归档到 `docs/archive/`
3. 把 `.kiro/specs/` 和 `.kiro/steering/` **加入** git（团队协作必需）
4. 4 次大提交分别推上 main：
   - `chore: harden gitignore and archive obsolete docs`
   - `feat: implement contract enhancements + revision + AI improvements`
   - `docs: add CLAUDE.md, project steering, and three specs`
   - `infra: dual-environment setup (test + prod)`

### 6.2 服务器侧搭建 prod（一次性，已完成）

完整 SOP 见 `docs/PROD_DEPLOYMENT_SOP.md`。摘要：

```bash
# 1. 共享层准备 prod DB / bucket
sudo docker exec contract_review_postgres psql -U postgres -c "CREATE DATABASE contract_review_prod ..."
sudo docker exec contract_review_minio mc mb local/contract-attachments-prod

# 2. clone prod 仓库
cd /home/ubuntu
git clone https://github.com/cmfl3483-art/contract-review.git contract-review-prod

# 3. 填 .env.prod（用 openssl rand -base64 32 生成 SECRET_KEY，与 test 不同）
cd contract-review-prod
cp .env.prod.example .env.prod
vim .env.prod

# 4. 钉钉控制台配 prod 应用回调 URL（手动）
#    https://chenmin0922.online/api/auth/dingtalk/callback

# 5. 启动 prod 栈 + 跑 alembic
docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod exec backend alembic upgrade head

# 6. 配宿主 Nginx
sudo cp nginx/chenmin0922.online.conf /etc/nginx/sites-available/chenmin0922.online
sudo ln -sf /etc/nginx/sites-available/chenmin0922.online /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 6.3 把现有 test 目录变成 git repo

服务器上 `/home/ubuntu/contract-review/` 之前是 rsync 同步的、**不是 git repo**。CI/CD 需要 `git pull`，所以要补上 `.git`：

```bash
cd /home/ubuntu/contract-review
cp .env .env.bak.$(date +%s)  # 备份
cp docker-compose.yml docker-compose.yml.bak.$(date +%s)

# 用 clone 一份新的，把它的 .git 嫁接到现有目录
cd /home/ubuntu
git clone --branch develop --depth 1 https://github.com/cmfl3483-art/contract-review.git /tmp/cr_clone
mv /tmp/cr_clone/.git /home/ubuntu/contract-review/.git
cd /home/ubuntu/contract-review
git fetch origin
git reset --hard origin/develop
rm -rf /tmp/cr_clone
```

`.env` 因为在 `.gitignore` 里所以会保留。

### 6.4 配 GitHub Actions

1. 仓库 Settings → Secrets and variables → Actions：加 3 个 secret
   - `SERVER_HOST` = `124.222.219.177`
   - `SERVER_USER` = `ubuntu`
   - `SSH_PRIVATE_KEY` = `kaifa.pem` 全部内容（含 BEGIN/END 行）
2. 仓库 Settings → Environments → 配 `production`：
   - **Required reviewers**：加自己
   - **取消勾选** "Allow administrators to bypass configured protection rules"（否则审批门槛形同虚设）
   - **Deployment branches**: Selected branches → 加规则 `Branch: main`
3. 创建 develop 分支并推上 GitHub：
   ```bash
   git checkout -b develop
   git push -u origin develop
   ```

### 6.5 端到端验证

- `git push origin develop` → 1 分钟后 test 容器重建 ✓
- `git push origin main` → GitHub Actions 等审批 → 点 Approve → 1 分钟后 prod 容器重建 ✓

## 7. 踩坑全记录（按重要性）

### 坑 1：服务器侧热修没回流到 git（**踩了 3 次**）

**症状**：本地 Dockerfile / docker-compose.yml 是旧版，服务器上是手动改过的优化版。每次 CI/CD 重 build 走的是 git 上的旧版。

**具体案例**：
- `backend/Dockerfile`：服务器上有腾讯镜像源加速（`mirrors.tencent.com`），git 上没有。导致 prod 首次 build 时 apt-get install 卡 30+ 分钟
- `docker-compose.yml`（test 用）：服务器上多 4 项配置（钉钉回调 / CORS / celery healthcheck / frontend healthcheck + `127.0.0.1:8080`），git 上没有

**根因**：之前部署都是 SSH 上去 `vim` 改完 `docker compose restart`，从来没回流 git。

**教训**：**所有服务器侧改动当天回流 git**。已写进 steering #17。

### 坑 2：腾讯云 SSH 长命令会被切（**踩了 5 次**）

**症状**：`ssh user@server 'docker compose build'` 类长命令跑 5 分钟左右被服务器主动切断。第二次重连 docker build 还在跑（孤儿进程）。

**根因**：腾讯云 SSH 网关对 idle / 长时无 stdout flush 的连接会切。可能也跟 fail2ban 类反暴力破解策略有关，频繁短连接也会触发。

**对策**：
- 短命令直接 SSH 跑
- 长命令在服务器上写脚本，用 `nohup setsid ... < /dev/null > /tmp/log 2>&1 & disown` 三重保险后台执行
- 然后用独立的短 SSH 命令轮询 `/tmp/log`

实例脚本：

```bash
#!/bin/bash
set -e
LOG=/tmp/build_prod.log
echo "[$(date)] start" >> $LOG
cd /home/ubuntu/contract-review-prod
docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod up -d --build >> $LOG 2>&1
echo "[$(date)] done" >> $LOG
```

启动：
```bash
nohup setsid /tmp/build.sh < /dev/null > /tmp/wrapper.log 2>&1 & disown
```

后续轮询：
```bash
tail -5 /tmp/build_prod.log
```

已写进 steering #18。

### 坑 3：钉钉权限分三层

prod 钉钉应用 `dingwbwrz9jazgvxzeyh` 第一次登录失败。三个权限要全开才行：

| 权限名 | 用途 | 错误码 |
|---|---|---|
| `Contact.User.Read` | 新版 OAuth 登录拿用户信息 | 401 / `AccessTokenPermissionDenied` |
| `qyapi_get_department_info` | 老版 API 拿部门信息 | `errcode=50004` |
| `qyapi_get_department_member` | 老版 API 拿部门成员 | `errcode=88` |

外加 **应用信息 → 通讯录权限范围**：必须设为 "全部员工" 或包含目标部门，否则即使权限开了也拉不到人。

**对照法**：直接对照 test 应用 `dingkyxfjd5bhgtr78rc` 已开权限一一勾上 prod 应用就稳。

### 坑 4：钉钉 API 错误结果会被缓存

**症状**：在钉钉控制台开了 `qyapi_get_department_member` 权限，过了好几分钟，但前端选审批人弹窗还是空的。

**根因**：`dingtalk_contact_service` 把 `corp_access_token` 和 `contacts_full` 缓存到 Redis（TTL 7200s 和较短）。**之前权限不足时返回的空数据被缓存了**。

**修复**：清缓存
```bash
docker exec contract_review_redis redis-cli -n 3 DEL dingtalk:corp_access_token dingtalk:contacts_full  # prod
docker exec contract_review_redis redis-cli -n 0 DEL dingtalk:corp_access_token dingtalk:contacts_full  # test
```

已写进 steering #19。

### 坑 5：JWT SECRET_KEY 要独立

test 的 SECRET_KEY 与 prod **必须不同**。原因：JWT 签发用的密钥决定了 token 有效性。如果共用一个密钥，从 test 拿的 token 能登 prod，反之亦然 — 这违背了环境隔离。

prod 用 `openssl rand -base64 32` 重新生成，存进 `.env.prod`。

### 坑 6：本地 DNS 污染（虚惊一场）

**症状**：本地 `dig +short chenmin0922.online` 返回 `198.18.0.226`（RFC 测试网段）。我误以为是阿里云 ICP 拦截。

**真相**：本地网络（公司网/路由器）有 DNS 重写或代理拦截，把这些域名重定向到内网测试 IP。从公网（服务器、手机 4G）解析正常。

**教训**：诊断 DNS 类问题时**必须从干净的网络验证**，不能只看本地结果。

### 坑 7：GitHub Actions environment 自动创建

**现象**：你还没去网页上配 `production` environment，但推 main 后 GitHub 上已经有这个名字了。

**原因**：`deploy-prod.yml` 文件里的 `environment: production` 字段被 GitHub 检测到，自动创建了一个空 environment。空 environment 意味着**没有任何保护规则** — 推 main 会直接部署，不停下来等审批！

**正确做法**：推 main 之前先在 GitHub 网页上配好 environment 的 protection rules。或者推 main 后立即去配（在没有人推 main 的间隙里）。

### 坑 8：Antd nginx alpine 镜像没装 wget

`docker-compose.prod.yml` 里 frontend healthcheck 用 `wget --quiet --tries=1 --spider`，但 nginx:alpine 镜像没装 wget。导致 prod_frontend 一直 "unhealthy"（功能正常，只是健康检查失败）。

**修复**：换成 `curl`（alpine 也没装但容易装；或者用 nginx 的 stub_status 模块）。本项目改用 `["CMD", "curl", "-f", "http://localhost/"]` — 实测 alpine nginx 镜像里有 curl。

## 8. 网址与凭据汇总

| 项 | 值 |
|---|---|
| GitHub repo | https://github.com/cmfl3483-art/contract-review |
| 服务器 IP | 124.222.219.177 |
| SSH key | `kaifa.pem`（本地保管，不进 git）|
| test 域名 | https://chenmin.yunumall.com |
| prod 域名 | https://chenmin0922.online |
| test 钉钉 AppKey | `dingkyxfjd5bhgtr78rc` |
| prod 钉钉 AppKey | `dingwbwrz9jazgvxzeyh` |
| MinIO Console | http://124.222.219.177:9001（minioadmin / minioadmin）|
| Portainer | http://124.222.219.177:18000（容器管理 UI）|
| GitHub Actions | https://github.com/cmfl3483-art/contract-review/actions |

## 9. 给后续维护者的 7 条建议

1. **不要直接在服务器 vim 改代码就部署**。所有改动通过 git 流转，否则又会重蹈坑 1。
2. **prod 不要瞎改**。`.env.prod` / `nginx config` 改之前先在本地或 test 验证。
3. **改 alembic 迁移要谨慎**。破坏性 schema 改动（删列、改类型）必须有 down migration 且在 test 充分验证。
4. **共享基础设施有连带风险**。test 跑大查询 / 大压测会拖累 prod postgres。日常工作避免，要做时去其它机器或临时建独立 stack。
5. **JWT SECRET_KEY 不要在两个环境间复制**。它是环境隔离的最后一道防线。
6. **Docker bind mount 别注释**。`./backend:/app` 注释掉就回到了"镜像内代码 vs git pull 不一致"的死循环。
7. **改钉钉权限后清 Redis 缓存**：`dingtalk:corp_access_token` + `dingtalk:contacts_full`（坑 4）

## 10. 给 AI 编码助手的额外提示

- 项目级 steering 在 `.kiro/steering/project-overview.md`，含 19 条关键约定（每会话自动加载）
- 三个 spec 在 `.kiro/specs/`，是功能规范权威源
- 改任何 server 端的东西时，**先记得**回流到 git（坑 1 的根源）
- SSH 连服务器跑长命令前**先想想会不会被切**（坑 2）
- 任何"权限/缓存类"问题诊断时考虑**Redis 缓存可能存了空结果**（坑 4）
- 用 `kaifa.pem` 连服务器：`ssh -i kaifa.pem ubuntu@124.222.219.177`

## 11. 内存占用现状（验证后）

```
total       used       free     shared   buff/cache  available
Mem:    3659M      ~1.6G     ~900M       22M        ~1.4G       ~2.0G
Swap:   1987M         0M
```

- 基础设施：postgres 65M / redis 14M / minio 142M ≈ 220M
- test 应用栈：backend 119M / celery 280M / frontend 7M ≈ 406M
- prod 应用栈：backend 128M / celery 273M / frontend 10M ≈ 411M
- portainer：85M
- 系统 + Docker daemon：~500M
- **合计 ~1.6G，剩 2G 余量，swap 未启用 = 健康**

如果将来内存紧张，第一个考虑去掉的是 portainer（用 `docker ps` / Kiro 的 Docker MCP 都能替代）。

---

**完成日期**：2026-05-27
**操作人**：陈敏 + Kiro AI assistant
**总耗时**：约半个工作日（含两次 docker build / 网络等待 / 多次 SSH 重连）
