# 数据库初始化成功 ✅

## 问题解决

之前遇到的 "relation 'users' does not exist" 错误已经解决。问题原因是数据库表没有被创建。

### 解决步骤

1. **修复了 Alembic 迁移脚本**
   - 文件: `backend/alembic/versions/001_create_initial_database_models.py`
   - 问题: 枚举类型创建时 `create_type=True` 导致重复创建
   - 修复: 改为 `create_type=False`

2. **重新创建数据库**
   ```bash
   docker exec contract_review_postgres psql -U postgres -c "DROP DATABASE IF EXISTS contract_review;"
   docker exec contract_review_postgres psql -U postgres -c "CREATE DATABASE contract_review WITH ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;"
   ```

3. **运行数据库迁移**
   ```bash
   docker exec contract_review_backend alembic upgrade head
   ```

4. **验证表创建成功**
   ```bash
   docker exec contract_review_postgres psql -U postgres -d contract_review -c "\dt"
   ```
   
   结果:
   ```
   public | ai_summaries    | table | postgres
   public | alembic_version | table | postgres
   public | attachments     | table | postgres
   public | comments        | table | postgres
   public | contracts       | table | postgres
   public | reviews         | table | postgres
   public | users           | table | postgres
   ```

## 当前系统状态

### 所有服务运行正常 ✅

- ✅ PostgreSQL 数据库 (端口 5432)
- ✅ Redis 缓存 (端口 6379)
- ✅ MinIO 对象存储 (端口 9000, 9001)
- ✅ 后端服务 (端口 8000)
- ✅ Celery Worker (异步任务)
- ✅ 前端服务 (端口 80)
- ✅ ngrok 隧道: `https://underfed-isolating-prolonged.ngrok-free.dev`

### 数据库表已创建 ✅

所有 7 个表已成功创建:
1. `users` - 用户表
2. `contracts` - 合同表
3. `reviews` - 评审记录表
4. `comments` - 评论表
5. `attachments` - 附件表
6. `ai_summaries` - AI总结表
7. `alembic_version` - 迁移版本表

## 如何访问系统

### 方式一: 通过 ngrok 公网地址 (推荐)

访问地址: **https://underfed-isolating-prolonged.ngrok-free.dev**

这个地址可以:
- ✅ 从任何地方访问
- ✅ 支持钉钉 OAuth 回调
- ✅ 已在钉钉开发者平台配置

### 方式二: 本地访问

访问地址: **http://localhost**

注意: 本地访问无法使用钉钉登录,因为钉钉回调需要公网地址。

## 登录流程

1. 打开浏览器访问: `https://underfed-isolating-prolonged.ngrok-free.dev`
2. 系统会自动检测未登录状态
3. 自动跳转到钉钉登录页面
4. 选择你的钉钉账号登录
5. 授权后自动跳转回系统首页
6. 登录成功,可以看到合同列表

## 配置信息

### 钉钉应用配置
- AppKey: `dingkyxfjd5bhgtr78rc`
- AppSecret: `PiNGAGUjtoh4byvBgNS-ZISS97COd7y4QftrFhGC8_ynuBS7N3B5aOeyMEhST2ag`
- 回调地址: `https://underfed-isolating-prolonged.ngrok-free.dev/api/auth/dingtalk/callback`

### DeepSeek AI 配置
- API Key: `sk-50b210fd06654e228bf4c85278174b95`
- 模型: `deepseek-v4-flash`

## 下一步

现在可以:
1. ✅ 访问系统并登录
2. ✅ 创建合同
3. ✅ 上传附件
4. ✅ 发起评审
5. ✅ 查看 AI 总结

## 故障排查

如果遇到问题:

### 1. 检查所有服务状态
```bash
docker ps
```

### 2. 查看后端日志
```bash
docker logs contract_review_backend --tail 50
```

### 3. 查看前端日志
```bash
docker logs contract_review_frontend --tail 50
```

### 4. 重启服务
```bash
docker-compose restart
```

### 5. 完全重启
```bash
docker-compose down
docker-compose up -d
```

## 重要提示

⚠️ **ngrok 地址会变化**: 如果重启 ngrok,地址会改变,需要:
1. 更新 `backend/.env` 中的 `DINGTALK_REDIRECT_URI`
2. 在钉钉开发者平台更新回调地址
3. 重启后端服务

⚠️ **数据持久化**: 数据库、Redis、MinIO 的数据都保存在 Docker volumes 中,即使重启容器也不会丢失。

## 成功! 🎉

系统已经完全配置好并运行,可以开始使用了!
