# 部署脚本快速参考

## 🚀 快速命令

### 首次部署
```bash
./scripts/build.sh      # 构建镜像
./scripts/start.sh      # 启动服务
./scripts/status.sh     # 检查状态
```

### 日常运维
```bash
./scripts/logs.sh [service]     # 查看日志
./scripts/restart.sh [service]  # 重启服务
./scripts/status.sh             # 检查状态
./scripts/stop.sh               # 停止服务
```

### 数据管理
```bash
./scripts/backup.sh                    # 备份数据
./scripts/restore.sh <backup-file>     # 恢复数据
```

---

## 📋 脚本速查表

| 命令 | 功能 | 示例 |
|------|------|------|
| `build.sh` | 构建 Docker 镜像 | `./scripts/build.sh` |
| `start.sh` | 启动所有服务 | `./scripts/start.sh` |
| `stop.sh` | 停止所有服务 | `./scripts/stop.sh` |
| `restart.sh` | 重启服务 | `./scripts/restart.sh backend` |
| `logs.sh` | 查看日志 | `./scripts/logs.sh backend -n 100` |
| `status.sh` | 检查状态 | `./scripts/status.sh` |
| `backup.sh` | 备份数据 | `./scripts/backup.sh` |
| `restore.sh` | 恢复数据 | `./scripts/restore.sh backups/xxx.tar.gz` |

---

## 🔍 常用日志命令

```bash
# 查看所有服务日志
./scripts/logs.sh

# 查看后端日志
./scripts/logs.sh backend

# 查看最后 100 行
./scripts/logs.sh backend -n 100

# 实时跟踪日志
./scripts/logs.sh backend -f

# 查看错误日志
./scripts/logs.sh backend | grep -i error
```

---

## 🔄 服务管理

```bash
# 重启所有服务
./scripts/restart.sh

# 重启后端
./scripts/restart.sh backend

# 重启前端
./scripts/restart.sh frontend

# 重启数据库
./scripts/restart.sh postgres
```

---

## 💾 备份恢复

```bash
# 创建备份
./scripts/backup.sh

# 查看备份列表
ls -lh backups/

# 恢复备份
./scripts/restore.sh backups/20250101_120000.tar.gz

# 定时备份 (添加到 crontab)
0 2 * * * /path/to/scripts/backup.sh
```

---

## 🏥 健康检查

```bash
# 完整状态检查
./scripts/status.sh

# 检查特定服务
docker compose ps backend

# 检查资源使用
docker stats

# 检查磁盘空间
df -h
```

---

## 🐛 故障排查

```bash
# 查看所有容器
docker ps -a

# 查看服务日志
./scripts/logs.sh

# 重启问题服务
./scripts/restart.sh <service>

# 完全重启
./scripts/stop.sh
./scripts/start.sh

# 清理并重启
docker system prune -f
./scripts/start.sh
```

---

## 🌐 访问地址

- **前端应用**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/docs
- **MinIO Console**: http://localhost:9001

---

## 📞 获取帮助

```bash
# 查看脚本帮助
./scripts/logs.sh -h

# 查看详细文档
cat scripts/README.md

# 查看部署指南
cat DEPLOYMENT_GUIDE.md
```

---

## ⚠️ 注意事项

1. **停止服务时**: 选择是否删除数据卷要谨慎
2. **恢复数据前**: 务必先备份当前数据
3. **生产环境**: 修改 .env 中的默认密码
4. **定期备份**: 建议每天自动备份
5. **监控日志**: 定期检查错误日志

---

## 🔐 安全提示

- 修改所有默认密码
- 使用 HTTPS (生产环境)
- 限制端口访问
- 定期更新系统和镜像
- 保护 .env 文件

---

更多详细信息请查看:
- [脚本详细说明](README.md)
- [完整部署指南](../DEPLOYMENT_GUIDE.md)
