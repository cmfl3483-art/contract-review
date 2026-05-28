# 部署踩坑实录 - 2026-05-27

> 把双环境部署 + CI/CD 接入这一天踩的坑按时间线讲一遍。
> 分散的约定汇总在 `.kiro/steering/project-overview.md` #17~#22；
> 完整架构与决策在 `docs/DUAL_ENV_DEPLOYMENT.md`。
> 这份文档目的：让你（或者接手的人）能从一个"刚出问题"的视角，看清当时为什么踩、怎么发现的、最终怎么解的。

## 0. 一图概览

```
开始              结束               进展
──────────────────────────────────────────────────────────
git 整理   ──►   3 提交 push 到 main
                                    ▼
                                试搭 prod 应用栈
docker build 卡 30 分钟  ◄─────  apt 走默认源极慢
                                    ▼
                                 修 Dockerfile（腾讯镜像源）
                                    ▼
                                 prod 跑通 ✓ 但钉钉登录失败
                                    ▼
                              开 Contact.User.Read 权限
                                    ▼
                              选审批人弹窗空，缺 2 个钉钉权限
                                    ▼
                              开权限 + 清 Redis 缓存（关键！）
                                    ▼
                              prod 钉钉登录 + 选人通了 ✓
                                    ▼
                                 配 GitHub Actions
                                    ▼
                              首次推 develop，CI/CD 跑通
                                    ▼
                              端到端验证 OK，文档归档
                                    ▼
                              发现 socket.io 报错"通信失败"
                                    ▼
                              修 AuthMiddleware（放行 socket.io）
                                    ▼
                              CI/CD 又挂（git fetch 卡）
                                    ▼
                              手动 scp 文件部署
                                    ▼
                              还是 401 → 发现 nginx 缺 /socket.io/ 块
                                    ▼
                              改 nginx 配置 reload
                                    ▼
                              ✓ 全流程通畅
──────────────────────────────────────────────────────────
```

## 1. 坑列表（按踩坑顺序）

### 坑 1：服务器侧 Dockerfile 没回流到 git，新搭 prod 用了未优化版本

**现象**：搭 prod 应用栈时 `docker compose build` 卡在 `apt-get install` 长达 30 分钟，最后 SSH 还断了。

**第一次诊断（错的）**：以为是腾讯云 SSH 会话超时，把命令丢后台跑。但即使后台跑也是慢得离谱。

**真因**：本地（git 上的）`backend/Dockerfile` 是早期版本，用 Debian 默认源；服务器上 test 那份是优化过的（`mirrors.tencent.com` + `--no-install-recommends`），但**这份优化从来没有 commit 回 git**。

**怎么发现的**：服务器跑 `docker history contract-review-backend:latest` 看 layer 命令——发现有 `sed -i 's|deb.debian.org|mirrors.tencent.com|...'` 那一行，对照本地 Dockerfile 才明白。

**修复**：服务器上 cat 出优化版本，覆盖本地 Dockerfile，commit + push。

**沉淀位置**：steering #17（服务器侧热修必须回流到 git）。**这一天总共踩了 4 次同类坑**。

---

### 坑 2：腾讯云 SSH 长命令会被切（多次踩到）

**现象**：`ssh ubuntu@server 'docker compose up -d --build'` 跑到 5 分钟左右被服务器主动切断。重连看，docker build 还在跑（孤儿进程）。

**真因**：腾讯云 SSH 网关对 idle 或长时无 stdout flush 的连接会切。多次短连接太频繁也会触发 fail2ban 类反爬保护。

**绕开方案**：服务器侧写 shell 脚本，用 **三重保险**后台跑，脱离 SSH 会话：

```bash
nohup setsid /tmp/build.sh < /dev/null > /tmp/log 2>&1 & disown
```

后续用独立的短 SSH 命令轮询日志：`tail /tmp/log`。

**沉淀位置**：steering #18（长 SSH 命令在腾讯云会被踢）。

---

### 坑 3：钉钉应用要开 3 个权限（且范围要全员）

**现象**：prod 钉钉登录第一次失败，报 `Forbidden.AccessDenied.AccessTokenPermissionDenied`，需要 `Contact.User.Read`。

去钉钉控制台开了，登录通了。但**选审批人弹窗里全公司员工拉不出来**——又两个错：
- `errcode=50004 部门id不在授权范围内`
- `errcode=88, qyapi_get_department_member`

**真因**：钉钉权限分老版（`oapi.dingtalk.com`）和新版（`api.dingtalk.com/v1.0`）两套：
- 新版 API（拿登录用户）：`Contact.User.Read`
- 老版 API（拉部门/成员）：`qyapi_get_department_info` + `qyapi_get_department_member`
- 还有"应用信息 → 通讯录权限范围"必须设为"全部员工"

prod 应用全部都是默认关闭，要逐项申请。

**沉淀位置**：steering #19（含完整权限清单）。

---

### 坑 4：钉钉 API 错误结果被缓存（**今天最阴险的坑**）

**现象**：钉钉权限开通完毕，过了 5 分钟，但选审批人弹窗依然空的。

**第一反应**：以为权限还没生效，多等等。等了半小时还不行。

**真因**：`dingtalk_contact_service` 把 `corp_access_token` 和 `contacts_full` 缓存到 Redis（前者 7200 秒，后者较短）。**之前权限不足时返回的空结果被缓存了**。后续即使权限开了，应用还在用空缓存。

**怎么发现的**：去看 backend 日志，`/api/dingtalk/contacts` 耗时 `0.4ms`——明显是直接读缓存没真去调钉钉 API。

**修复**：手动清掉两个 key
```bash
docker exec contract_review_redis redis-cli -n 3 DEL dingtalk:corp_access_token dingtalk:contacts_full  # prod (db 3)
docker exec contract_review_redis redis-cli -n 0 DEL dingtalk:corp_access_token dingtalk:contacts_full  # test (db 0)
```

**沉淀位置**：steering #19。

---

### 坑 5：DNS 诊断时被本地网络误导

**现象**：本地 `dig +short htsp.yunumall.com` 返回 `198.18.0.226`（RFC 测试网段），看着像被 ICP 拦截了。

**第一次诊断（错的）**：以为是阿里云对未备案子域的 DNS 劫持。

**真因**：本地（公司网/路由器）DNS 重写或代理，把这些域名劫持到内网测试 IP。从干净的服务器解析就是 `124.222.219.177`。

**教训**：诊断 DNS 类问题要**从干净的网络验证**，不能只看本地结果。这一段我浪费了 10 分钟瞎查 ICP 备案问题，向你道歉。

---

### 坑 6：服务器 test 目录原来不是 git repo

**现象**：搭好 prod 后准备配 GitHub Actions，发现 `cd /home/ubuntu/contract-review && git status` 报 `not a git repository`。

**真因**：test 目录从一开始就是 `rsync/scp` 同步的，从来不是 `git clone` 出来的。CI/CD 跑的 `git pull` 自然也跑不了。

**修复**：在服务器上 `git clone` 一份到 /tmp，把 `.git` 嫁接到现有目录（保留 `.env` 等配置）：
```bash
cd /home/ubuntu
git clone --branch develop --depth 1 https://github.com/.../contract-review.git /tmp/cr_clone
mv /tmp/cr_clone/.git /home/ubuntu/contract-review/.git
cd /home/ubuntu/contract-review
git fetch origin && git reset --hard origin/develop
rm -rf /tmp/cr_clone
```

`.env` 因为在 `.gitignore` 里所以不会被 reset 覆盖。

---

### 坑 7：服务器侧 docker-compose.yml 也没回流（#17 二次踩）

**现象**：把 test 目录变成 git repo 后，git diff 发现服务器上的 `docker-compose.yml` 比 git 上的多 4 项配置（钉钉 redirect、CORS、celery healthcheck、frontend healthcheck + 端口绑定）。

**真因**：之前部署时 SSH 上去手动 vim 改的，没 commit。

**修复**：把服务器版本作为 canonical，覆盖本地 git，提交。

---

### 坑 8：FastAPI AuthMiddleware 拦截 /socket.io/

**现象**：部署完成后用户报"实时通信连接失败,部分功能可能受影响,系统将自动尝试重新连接"。

**第一反应**：以为是 socket.io 服务没启动。但服务是好的。

**第一次诊断（半对半错）**：服务器侧看后端日志全是 `socket.io...401 Unauthorized`，定位到 AuthMiddleware 拦截了。

**真因**：浏览器原生 WebSocket **不支持自定义 HTTP header**（如 `Authorization: Bearer xxx`）。前端只能通过 `io(url, { auth: { token } })` 传 token，但这不是 HTTP header，是 socket.io 协议自己的握手字段。AuthMiddleware 看不到这个字段，直接拦下来。

**修复**：把 `/socket.io/` 加到 AuthMiddleware 的 public_paths。安全性不下降，因为 socket.io 服务自己的 `connect` handler 会校验 token。

**沉淀位置**：steering #21。

---

### 坑 9：CI/CD 推 develop 部署卡 14 分钟没动静

**现象**：修复了坑 8 后 push develop，GitHub Actions 显示 "In progress 13:58"——比平时慢 13 倍。

**真因**：服务器到 GitHub 的 git protocol 端点间歇性不通。具体看到的是：
- `github.com` HTTPS 主页通
- `git ls-remote` 偶尔通偶尔不通
- `git fetch` 跑了发了 POST 但没拿到 packfile

加上：服务器上之前我手动跑的部署脚本和 GitHub Actions 跑的部署脚本**两个 `git fetch` 同时跑**，互相阻塞（git 仓库会对并发 fetch 加锁）。

**临时方案**：杀掉所有 git 进程，scp 直接传修改的文件到服务器，bind mount 自动生效。

**长期方案**：等腾讯云到 GitHub 网络恢复（通常几分钟到几小时），重推一个 commit 触发 CI/CD 即可。

---

### 坑 10：scp 改完代码 + 重启容器，401 还在 → Nginx 缺 /socket.io/ 块

**现象**：scp 上传修改后的 auth_middleware.py，docker restart backend，**前端还是报错**。但用 curl 直接打 backend 8000 端口又是好的。

**第一次诊断（错的）**：以为浏览器缓存了旧 JS bundle，让你强制刷新。但浏览器明明已经清缓存了。

**真因**：从浏览器 → nginx → backend 的链路里，**nginx 把 socket.io 请求转给了前端容器**（不是 backend）。
- 前端容器（nginx alpine）的 80 端口跑的是静态文件 + SPA 路由
- 前端容器**不是 WebSocket 服务**
- 所以浏览器收到 "WebSocket connection failed: bad response from server"

**怎么发现的**：宿主 nginx 的 access.log 里**完全没有** chenmin.yunumall socket.io 请求的记录。这意味着请求要么被 nginx 当成普通请求转给前端了，要么没到 nginx——细看才发现 chenmin.yunumall 配置文件**完全没有 `/socket.io/` location 块**。

**修复**：补上 `/socket.io/` 块到宿主 nginx 配置：
```nginx
location /socket.io/ {
    proxy_pass http://127.0.0.1:8000/socket.io/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    # ...
}
```

**沉淀位置**：steering #22 + 仓库里 `nginx/chenmin.yunumall.com.conf`（之前 prod 那份配置是搭的时候就配对了）。

---

## 2. 共同模式

把今天 10 个坑捋出来，能看到几个反复出现的模式：

### 模式 A：服务器侧改了没回流 git（#1 #7 #10 #6）
**4 次同类问题**——这是今天的头号大坑。早期同事直接 ssh 上服务器 `vim` 改完跑的工作方式，留下大量"git 上是 A 版本，服务器跑的是 B 版本"的差异。每次重新部署或克隆都会复现。

**后续防护**：
- steering #17 写死规则
- 现在所有改动通过 git → CI/CD 才能生效，**禁止直接 SSH 改代码**

### 模式 B：缓存隐藏了真相（#4）
钉钉权限开通后看不到效果——以为是钉钉延迟，实际是 Redis 缓存了空结果。

**后续防护**：steering #19 给出明确的清缓存命令，写进文档。

### 模式 C：诊断信息不充分（#5 #8 #10）
- DNS 问题只在本地看，差点搞错备案
- socket.io 401 第一次只看到一半（修了 backend 还要修 nginx）
- 几次都需要"再多看一眼日志"才发现真因

**教训**：服务器/容器/nginx/前端，每一层都要看一眼日志再下结论。

### 模式 D：网络抖动是常态，要有兜底（#9）
腾讯云国内服务器 → GitHub 间歇性慢/不通是常态。CI/CD 不能假设网络永远好。

**后续防护**：CI/CD workflow 已经加了超时、`script_stop: true`、`concurrency` 锁。如果再挂，手动重推或 scp 兜底。

## 3. 给后续的建议（实操级别）

1. **每次会话开始**：先看 `.kiro/steering/project-overview.md` 这 22 条约定（每次自动加载）
2. **改代码后**：通过 git push → CI/CD 部署，**不要 SSH 上去手改**
3. **遇到 "怎么不生效" 类问题**：按这个顺序检查
   - git 上是什么版本？`git log --oneline -1`
   - 服务器目录是什么版本？`ssh ... 'cd ... && git log --oneline -1'`
   - 容器里跑的是什么版本？`docker exec <c> cat /app/...`
   - 浏览器看到的是什么版本？F12 → Sources → 看 JS bundle hash
4. **遇到"权限改了不生效"**：八成是 Redis 缓存了空结果。`docker exec contract_review_redis redis-cli -n <db> DEL dingtalk:corp_access_token dingtalk:contacts_full`
5. **CI/CD 卡了不动**：按 steering #18 的方法，手动 scp 修改文件作为兜底
6. **socket.io 通信报错**：四步排查
   - 浏览器 console 错误信息（401 还是 bad response？）
   - backend 日志里有没有 socket.io 401
   - nginx 配置里有没有 `/socket.io/` location 块
   - nginx access.log 里 socket.io 请求是 200/101/还是没到？

## 4. 沉淀位置索引

如果要查具体规则：
- **22 条约定**：`.kiro/steering/project-overview.md`
- **完整架构 + 8 条主要踩坑分析**：`docs/DUAL_ENV_DEPLOYMENT.md`
- **日常命令速查**：`docs/CICD_QUICK_REFERENCE.md`
- **prod 一次性搭建步骤**：`docs/PROD_DEPLOYMENT_SOP.md`
- **今天的故事（按时间线）**：本文档

如果以后又踩了新坑，**首选补到 `.kiro/steering/project-overview.md`**（自动加载）。

---

**总结**：双环境 + CI/CD 接入完成。今天踩了 10 个坑，6 个是技术原因，4 个是"服务器侧改没回流 git"的同源问题。22 条约定都已固化到自动加载的 steering 文件，下次新会话或新人接手都能避开。
