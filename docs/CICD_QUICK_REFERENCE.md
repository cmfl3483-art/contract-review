# CI/CD 速查卡片

> 已经熟悉架构？只想查命令？看这一页就够。完整设计文档见 [DUAL_ENV_DEPLOYMENT.md](./DUAL_ENV_DEPLOYMENT.md)。

## 🌳 分支策略

| 分支 | 触发什么 | 域名 |
|---|---|---|
| `feature/*` | 不部署，本地开发 | — |
| `develop` | 自动部署 test | https://chenmin.yunumall.com |
| `main` | 部署 prod（**等审批**） | https://chenmin0922.online |

## 🚀 日常操作

### 部署到 test（自动）
```bash
git checkout develop
git merge feature/xxx     # 或直接在 develop 上改
git push origin develop
# 1 分钟后访问 https://chenmin.yunumall.com 验证
```

### 部署到 prod（要审批）
```bash
git checkout main
git merge develop
git push origin main
# 1. 收到 GitHub 邮件
# 2. 打开 https://github.com/cmfl3483-art/contract-review/actions
# 3. 点最新 Deploy to Production 那条
# 4. 黄色 "Review pending deployments" → Approve and deploy
# 5. 1 分钟后访问 https://chenmin0922.online 验证
```

### 紧急回滚 prod
```bash
git checkout main
git log --oneline -5            # 找到上一个稳定 commit hash
git revert <bad-commit-hash>    # 不要用 reset --hard
git push origin main
# 走正常审批流程，1 分钟回滚
```

### 手动触发部署（不必修改代码）
GitHub Actions 页面 → 选 workflow → 右上 `Run workflow` 按钮 → 选分支 → Run

## 🔑 服务器 SSH

```bash
ssh -i kaifa.pem ubuntu@124.222.219.177
```

⚠️ `kaifa.pem` 在本地保管，从未进 git。**不要发给任何人，不要截图，不要传到云盘**。

## 📁 服务器关键目录

| 目录 | 用途 | 对应分支 |
|---|---|---|
| `/home/ubuntu/contract-review/` | test 应用栈 | develop |
| `/home/ubuntu/contract-review-prod/` | prod 应用栈 | main |
| `/etc/nginx/sites-enabled/` | 宿主 Nginx 站点 | — |
| `/etc/letsencrypt/live/` | SSL 证书 | — |

每个仓库目录都是**独立 git repo**，互不影响。

## 🐳 docker compose 命令速查

### test（在 `/home/ubuntu/contract-review/`）
```bash
docker compose ps
docker compose logs -f backend
docker compose restart backend
docker compose up -d --build              # 重建 + 启动
docker compose exec backend alembic upgrade head
```

### prod（在 `/home/ubuntu/contract-review-prod/`）
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod ps
docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod logs -f backend
docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod restart backend
docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod exec backend alembic upgrade head
```

省事别名（追加到 `~/.bashrc`）：
```bash
alias dc-test='docker compose'
alias dc-prod='docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod'
```
之后就能 `dc-prod ps`、`dc-prod logs -f backend` 这样用。

## 🔍 排错速查

### 看日志
```bash
# test
docker logs contract_review_backend --tail 100 -f
docker logs contract_review_celery_worker --tail 100 -f

# prod
docker logs prod_backend --tail 100 -f
docker logs prod_celery_worker --tail 100 -f

# 宿主 Nginx
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

### 看资源
```bash
free -m                          # 内存
docker stats --no-stream         # 每容器内存/CPU
df -h                            # 磁盘
```

### 健康检查
```bash
curl http://127.0.0.1:8000/health   # test
curl http://127.0.0.1:8001/health   # prod
curl https://chenmin.yunumall.com/health
curl https://chenmin0922.online/health
```

### 数据库连接
```bash
# test 库
docker exec -it contract_review_postgres psql -U postgres -d contract_review

# prod 库
docker exec -it contract_review_postgres psql -U postgres -d contract_review_prod
```

### 清 Redis 缓存（钉钉权限改完别忘了）
```bash
# prod
docker exec contract_review_redis redis-cli -n 3 DEL dingtalk:corp_access_token dingtalk:contacts_full

# test
docker exec contract_review_redis redis-cli -n 0 DEL dingtalk:corp_access_token dingtalk:contacts_full
```

## 🌐 钉钉控制台

| 应用 | AppKey | 回调 URL |
|---|---|---|
| test | `dingkyxfjd5bhgtr78rc` | `https://chenmin.yunumall.com/api/auth/dingtalk/callback` |
| prod | `dingwbwrz9jazgvxzeyh` | `https://chenmin0922.online/api/auth/dingtalk/callback` |

每个应用都需要的权限：
- `Contact.User.Read`（新版 OAuth 登录）
- `qyapi_get_department_info`（部门信息读取）
- `qyapi_get_department_member`（部门成员读取）
- 应用信息 → **通讯录权限范围** = "全部员工"

## 🤔 常见问题

**Q: 我推到 develop 但 test 没更新？**
1. 看 https://github.com/cmfl3483-art/contract-review/actions 是否触发
2. 如果触发了但 fail，点进去看是哪一步报错
3. 90% 是 SSH 连接问题或 docker build 失败 → SSH 上服务器看 `/tmp/prod_build.log` 之类

**Q: 推到 main 没看到部署？**
环境保护规则要求 reviewer 审批。打开 Actions 页面找 `Waiting` 状态的那条，手动 Approve。

**Q: 部署到一半失败了，环境是不是坏了？**
GitHub Actions 是 `script_stop: true`，失败会停在出错那步。**之前的容器还在跑、没被停**。SSH 上去看日志、修问题、重新 push。

**Q: 想改某个环境变量怎么办？**
- test：服务器 `/home/ubuntu/contract-review/.env`，改完 `docker compose restart backend celery_worker`
- prod：服务器 `/home/ubuntu/contract-review-prod/.env.prod`，改完 `docker compose ... -p prod restart backend celery_worker`
- 不要把改动提交到 git（这两个文件已经在 .gitignore 里）

**Q: 想新加一个 secret 给 GitHub Actions 用？**
仓库 Settings → Secrets and variables → Actions → New repository secret
然后在 workflow yaml 里用 `${{ secrets.NAME }}`

**Q: ngrok 还要吗？**
不要了。两个域名都正常解析、有 SSL 证书。ngrok 是早期没正式域名时的过渡方案。

## 📋 钉钉权限错误码速查

| 错误码 | 含义 | 缺哪个权限 |
|---|---|---|
| `AccessTokenPermissionDenied` | 新版 API 拿用户信息失败 | `Contact.User.Read` |
| `errcode=50004 部门id不在授权范围内` | 老版 API 拿部门 | `qyapi_get_department_info` |
| `errcode=88, qyapi_get_department_member` | 老版 API 拿部门成员 | `qyapi_get_department_member` |

每次开完权限**记得清 Redis 缓存**（见上面"清 Redis 缓存"段），否则空缓存会持续 7200 秒。

## 🔥 紧急情况手动操作

如果 GitHub Actions 完全挂了（GitHub down 或 SSH 死了），可以手动部署。

### 手动部署 test
```bash
ssh -i kaifa.pem ubuntu@124.222.219.177
cd /home/ubuntu/contract-review
git fetch origin && git reset --hard origin/develop
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

### 手动部署 prod
```bash
ssh -i kaifa.pem ubuntu@124.222.219.177
cd /home/ubuntu/contract-review-prod
git fetch origin && git reset --hard origin/main
docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod exec backend alembic upgrade head
```

### 重启某个容器（不要一上来就重建整套）
```bash
docker restart prod_backend
docker restart contract_review_backend
```

## 🎯 监控指标（值得关注）

| 指标 | 健康范围 | 异常时怎么办 |
|---|---|---|
| 内存使用 | <3GB | 重启不必要的容器（如 portainer） |
| Swap 使用 | <500MB 持续低位 | 看是否有内存泄漏 |
| 磁盘使用 | <70% | `docker system prune -af` 清旧镜像 |
| postgres 连接数 | <50 | 看是否有应用泄漏连接 |
| 容器健康状态 | 全 healthy | `docker logs <name> --tail 50` 看错误 |

## 📚 拓展阅读

- 完整架构与决策：[DUAL_ENV_DEPLOYMENT.md](./DUAL_ENV_DEPLOYMENT.md)
- 一次性 prod 搭建 SOP：[PROD_DEPLOYMENT_SOP.md](./PROD_DEPLOYMENT_SOP.md)
- 项目总览（每会话自动加载）：[../.kiro/steering/project-overview.md](../.kiro/steering/project-overview.md)
- 历史踩坑归档：[archive/](./archive/)
