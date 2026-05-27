# 生产环境 Docker Bind Mount 失效问题排查记录

## 问题现象

合同编辑（PATCH）和附件上传（POST）接口持续返回 **500 Internal Server Error**，错误类型为 `DBAPIError`。

## 排查过程（耗时大量时间）

### 第一阶段：怀疑代码逻辑问题

1. **增加了 `contract_number` 字段** — 模型、路由、服务、前端全部修改
2. **改进了错误日志** — `error_handler.py` 加入 `str(exc)`、`repr(exc)`、`exc.__traceback__` 等详细输出
3. **路由层添加 try-except** — `contracts.py` 和 `files.py` 的 PATCH/POST 路由加入 `traceback.print_exc()`
4. **修改了 `db.commit()` → `db.flush()`** — 在 `file_service.py` 中避免事务不一致

### 第二阶段：怀疑日志本身有问题

- `traceback.format_exc()` 在 FastAPI 异常处理器中返回空字符串
- `sys.stderr.write()` 的 `[DB ERROR]` 标记也不出现在 Docker 日志中
- 改为使用 `exc.__traceback__` 手动构建 traceback

### 第三阶段：发现真相

进入容器内部检查发现：

```bash
# 容器内的文件日期是旧的！
$ sudo docker exec contract_review_backend ls -la /app/app/core/error_handler.py
-rw-r--r-- 1 appuser appuser 7435 May 19 00:01 /app/app/core/error_handler.py

# 主机的文件日期是最新的（刚 rsync 过来的）
$ ls -la /home/ubuntu/contract-review/backend/app/core/error_handler.py
-rw-r--r-- 1 ubuntu ubuntu 7893 May 26 16:50 /app/app/core/error_handler.py
```

**文件大小不同、日期不同** — bind mount 根本没生效！

## 根因

`docker-compose.yml` 中 backend 服务的 `volumes` 配置被**注释掉了**：

```yaml
volumes:
  # - ./backend:/app  # 生产环境使用镜像内代码  ← 被注释了！
  - backend_logs:/app/logs
```

导致：
- 通过 `rsync` / `scp` 同步到主机 `/home/ubuntu/contract-review/backend/` 下的所有代码修改
- **容器内看到的仍然是构建镜像时打包的旧代码**
- 所有修复看似"已部署"，实则从未生效
- 日志错误信息始终是旧版代码的输出

## 修复

```bash
# 1. 取消 bind mount 的注释
sudo sed -i 's|# - ./backend:/app  # 生产环境使用镜像内代码|  - ./backend:/app|' docker-compose.yml

# 2. 注意 YAML 缩进一致性
# volumes: 下的每行必须保持相同缩进层级

# 3. 重建容器使新配置生效
sudo docker compose down backend
sudo docker compose up -d backend
```

## 经验教训

### 判断 bind mount 是否生效的方法

```bash
# 方法1：检查容器内文件日期是否与主机一致
sudo docker exec <container> ls -la /app/app/core/error_handler.py
ls -la backend/app/core/error_handler.py

# 方法2：检查容器的 Mounts 配置
sudo docker inspect <container> --format='{{json .Mounts}}' | python3 -m json.tool
# 如果只有 named volume（如 backend_logs）而没有 bind mount（./backend → /app），说明 bind mount 未生效

# 方法3：修改一个文件后，在容器内验证
echo "# test" >> backend/app/core/test_deploy.py
sudo docker exec <container> cat /app/app/core/test_deploy.py
# 如果能读到内容，说明 bind mount 生效
```

### Docker 部署代码更新方式对比

| 方式 | 适用场景 | 生效方式 |
|------|---------|---------|
| **bind mount** (`- ./backend:/app`) | 开发/调试阶段 | 文件修改即刻生效，重启容器即可 |
| **镜像构建** (`docker compose build`) | 生产部署 | 需重新 build + up，适合 CI/CD |
| **docker cp** | 临时测试 | 不推荐，容器重建后丢失 |

### 排查 500 错误的正确思路

1. **先确认代码是否真的在运行** — 验证文件版本、内容、日期
2. **不要假设 rsync/scp 成功=部署成功** — 容器可能使用镜像内代码而非 bind mount
3. **进入容器内部验证** — `docker exec <container> cat <file>` 是最直接的核查手段
4. **查看容器的 Mounts 配置** — `docker inspect` 确认 bind mount 是否存在
