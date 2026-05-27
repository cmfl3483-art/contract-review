# 生产环境部署 SOP

本文档记录从零到一搭建 prod 环境的步骤。一次性执行，之后日常部署由 GitHub Actions 自动完成。

## 整体架构

```
                    宿主 Nginx (80/443)
                          │
        ┌─────────────────┴──────────────────┐
        │                                    │
chenmin.yunumall.com → :8080         chenmin0922.online → :8090
   (test 前端)                         (prod 前端)
chenmin.yunumall.com/api → :8000     chenmin0922.online/api → :8001
   (test 后端)                         (prod 后端)
        │                                    │
   ┌────┴─────────────┐              ┌──────┴────────┐
   │  test 应用栈     │              │  prod 应用栈   │
   │  (现有，不动)    │              │  (新搭)        │
   │  - frontend:8080 │              │  - frontend:8090│
   │  - backend:8000  │              │  - backend:8001 │
   │  - celery        │              │  - celery       │
   └──────┬───────────┘              └───────┬────────┘
          │                                  │
          └──────────────┬───────────────────┘
                         │ 共享网络
        ┌────────────────┴─────────────────────┐
        │  共享基础设施层（test 已部署）          │
        │  postgres :5432                       │
        │    ├─ contract_review (test 现状)     │
        │    └─ contract_review_prod (新建空)   │
        │  redis :6379                          │
        │    ├─ db 0/1/2 (test 现状)            │
        │    └─ db 3/4/5 (prod 用)              │
        │  minio :9000                          │
        │    ├─ contract-attachments (test 现状)│
        │    └─ contract-attachments-prod (新建)│
        └───────────────────────────────────────┘
```

## 域名与凭据

| 项 | test | prod |
|---|---|---|
| 域名 | chenmin.yunumall.com | chenmin0922.online |
| 后端端口 | 8000 | 8001 |
| 前端端口 | 8080 | 8090 |
| 数据库 | contract_review | contract_review_prod |
| Redis db | 0/1/2 | 3/4/5 |
| MinIO bucket | contract-attachments | contract-attachments-prod |
| 钉钉 AppKey | dingkyxfjd5bhgtr78rc | dingwbwrz9jazgvxzeyh |
| Git 分支 | develop | main |
| 服务器目录 | /home/ubuntu/contract-review | /home/ubuntu/contract-review-prod |

## 阶段 1：创建 prod 数据库与 bucket（共享层准备）

```bash
# SSH 上服务器
ssh -i kaifa.pem ubuntu@124.222.219.177

# 创建 prod 数据库
sudo docker exec -it contract_review_postgres psql -U postgres -c "CREATE DATABASE contract_review_prod WITH ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;"

# 验证两个 DB 都在
sudo docker exec -it contract_review_postgres psql -U postgres -c "\l"

# 创建 prod bucket
sudo docker exec -it contract_review_minio mc alias set local http://localhost:9000 minioadmin minioadmin
sudo docker exec -it contract_review_minio mc mb local/contract-attachments-prod

# 验证 bucket
sudo docker exec -it contract_review_minio mc ls local/
```

## 阶段 2：克隆 prod 仓库目录

```bash
cd /home/ubuntu

# 从 GitHub clone（与 test 共用一个 GitHub repo，但本地两份独立目录）
git clone https://github.com/cmfl3483-art/contract-review.git contract-review-prod
cd contract-review-prod

# 默认在 main 分支
git branch
```

## 阶段 3：填充 .env.prod

```bash
cd /home/ubuntu/contract-review-prod
cp .env.prod.example .env.prod

# 生成强 SECRET_KEY
openssl rand -base64 32
# 把生成的 key 填到 .env.prod 的 SECRET_KEY=

# 编辑 .env.prod，把 __YOUR_DEEPSEEK_API_KEY__ 换成实际 key（与 test 用同一个）
vim .env.prod

# 验证不包含占位符
grep -E '__|change-in' .env.prod || echo "all values filled in"
```

## 阶段 4：钉钉控制台配回调 URL

⚠️ **必须先做这一步，否则登录会 redirect_uri_mismatch**

到钉钉开放平台 → 找到生产应用（AppKey: dingwbwrz9jazgvxzeyh）→ 安全设置 → 重定向 URL

填入：
```
https://chenmin0922.online/api/auth/dingtalk/callback
```

保存后等 1-2 分钟生效。如果保存后报错，**删除该记录 → 保存 → 重新添加 → 保存**（钉钉控制台有缓存）。

## 阶段 5：启动 prod 应用栈

```bash
cd /home/ubuntu/contract-review-prod

# 首次启动（会拉镜像 + 构建，5-10 分钟）
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod up -d --build

# 等容器起来后跑 alembic 迁移（建表）
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod exec backend alembic upgrade head

# 检查状态
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod ps

# 应该看到三个容器都是 running/healthy：
#   prod_backend
#   prod_celery_worker
#   prod_frontend

# 健康检查
curl http://127.0.0.1:8001/health
# 期望响应: {"status":"healthy",...}

curl -I http://127.0.0.1:8090/
# 期望响应: HTTP/1.1 200 OK
```

## 阶段 6：配置宿主 Nginx

```bash
# 复制 nginx 配置文件到服务器（在本地运行）
scp -i kaifa.pem nginx/chenmin0922.online.conf ubuntu@124.222.219.177:/tmp/

# 在服务器上：
sudo mv /tmp/chenmin0922.online.conf /etc/nginx/sites-available/chenmin0922.online
sudo ln -sf /etc/nginx/sites-available/chenmin0922.online /etc/nginx/sites-enabled/

# 测试配置语法
sudo nginx -t

# 应该输出：
#   nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
#   nginx: configuration file /etc/nginx/nginx.conf test is successful

# 重载 Nginx
sudo systemctl reload nginx
```

## 阶段 7：验证

### 7.1 SSL 证书

```bash
# 服务器上检查证书有效期
sudo certbot certificates | grep -A 5 chenmin0922.online
# 期望证书未过期。如果过期：
#   sudo certbot renew --cert-name chenmin0922.online
```

### 7.2 端到端访问

浏览器打开 `https://chenmin0922.online`：
- 应自动跳转钉钉登录
- 用钉钉账号登录
- 应进入合同看板（**库是空的**，列表无数据，正确）

### 7.3 资源监控

```bash
# 看内存占用
free -m

# 看每个容器内存
sudo docker stats --no-stream

# 期望：总内存使用 ~3GB 以内
```

## 阶段 8：配置 GitHub Actions

### 8.1 在 GitHub repo 加 Secrets

到 GitHub → repo → Settings → Secrets and variables → Actions → New repository secret，加这三个：

| Name | Value |
|---|---|
| `SERVER_HOST` | `124.222.219.177` |
| `SERVER_USER` | `ubuntu` |
| `SSH_PRIVATE_KEY` | `kaifa.pem` 文件的全部内容（含 `-----BEGIN ...-----` 和 `-----END ...-----`） |

### 8.2 创建 develop 分支

```bash
# 本地操作
cd /Users/cm/Documents/kiro/project

git checkout -b develop
git push -u origin develop
```

### 8.3 配置 production environment（可选但推荐）

到 GitHub → repo → Settings → Environments → New environment → 命名 `production`：
- 勾选 **Required reviewers**：加上你自己（这样 main 分支推送会要你点确认才部署）
- 勾选 **Wait timer**：1 分钟（给反悔时间）

### 8.4 测试自动部署

```bash
# 在本地随便改个无关紧要的文件（比如 README.md 加一行）
echo "" >> README.md
git add README.md
git commit -m "test: trigger deploy-test workflow"
git push origin develop

# 立即去 GitHub repo → Actions 标签页看，应有 Deploy to Test 在跑
# 跑完后 SSH 上服务器看 test 是否被重新构建
```

## 日常运维

### 看哪个环境跑着哪些容器

```bash
# test
sudo docker compose -f docker-compose.yml ps

# prod
cd /home/ubuntu/contract-review-prod
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod ps
```

### 看日志

```bash
# prod backend 日志
sudo docker logs prod_backend --tail 100 -f

# prod celery 日志
sudo docker logs prod_celery_worker --tail 100 -f

# 宿主 Nginx 日志
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

### 紧急回滚 prod

如果新版本部署后出问题，回到上一个版本：

```bash
cd /home/ubuntu/contract-review-prod

# 找到上一个 commit
git log --oneline -5

# 回到指定 commit（用 hash 替换）
git reset --hard <previous-commit-hash>

# 重启
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod up -d --build
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod exec backend alembic upgrade head
```

⚠️ 数据库迁移没有自动回滚，如果新版本加了破坏性 schema 改动（比如删了列），回滚代码后旧代码可能跑不起来。这种情况要么准备 down migration，要么从备份恢复 DB。

### 关闭 prod（保留 test）

```bash
cd /home/ubuntu/contract-review-prod
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod -p prod down
```

prod 容器停了，test 完全不受影响。

## 故障排查

### prod backend 起不来

```bash
sudo docker logs prod_backend --tail 50
```

常见错误：
- `database "contract_review_prod" does not exist` → 阶段 1 漏了创建数据库
- `bucket does not exist` → 阶段 1 漏了创建 bucket
- `redirect_uri_mismatch` → 阶段 4 钉钉回调没配
- `Authorization header missing` → 前端代码用了 `axios` 而非 `axiosInstance`（见 steering）

### prod 和 test 数据混了

不可能。三种隔离都是物理的：
- 不同 DB：`contract_review` vs `contract_review_prod`
- 不同 Redis db：0/1/2 vs 3/4/5
- 不同 bucket：`contract-attachments` vs `contract-attachments-prod`

如果真发生了，检查 `.env.prod` 是否被错误改成 test 的连接串。

### Nginx 配置错误后宿主整体崩了

```bash
sudo nginx -t  # 看语法
sudo cat /etc/nginx/sites-enabled/chenmin0922.online  # 看实际加载的
sudo rm /etc/nginx/sites-enabled/chenmin0922.online  # 临时移除回归正常
sudo systemctl reload nginx
```
