# 压力测试指南
# Stress Testing Guide

## 概述

本文档提供合同预审看板系统的压力测试指南,包括测试工具、测试场景、运行方法和结果分析。

## 测试目标

根据任务 38.5 的要求,压力测试需要覆盖以下方面:

1. **并发用户访问** - 测试系统在多用户同时访问时的性能
2. **大量数据加载** - 测试系统处理大量合同和评审数据的能力
3. **文件上传性能** - 测试文件上传的吞吐量和响应时间
4. **WebSocket 连接数** - 测试实时通信的并发连接能力

## 测试工具

### 方案 1: Locust (推荐)

**优点:**
- 专业的负载测试工具
- 提供 Web UI 实时监控
- 支持分布式测试
- 丰富的统计报告

**安装:**
```bash
pip install locust
```

**运行:**
```bash
# Web UI 模式 (推荐)
locust -f tests/stress_test.py --host=http://localhost:8000

# 无头模式 (自动化测试)
locust -f tests/stress_test.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 60s \
  --headless
```

**访问 Web UI:**
打开浏览器访问 `http://localhost:8089`

### 方案 2: 简单压力测试脚本

**优点:**
- 不需要额外依赖
- 使用 Python 内置库
- 适合快速测试

**安装依赖:**
```bash
pip install aiohttp
```

**运行:**
```bash
python tests/simple_stress_test.py
```

### 方案 3: 专业工具

#### Artillery (Node.js)

```bash
# 安装
npm install -g artillery

# 运行
artillery quick --count 100 --num 10 http://localhost:8000/api/contracts
```

#### k6 (Go)

```bash
# 安装 (macOS)
brew install k6

# 运行
k6 run stress_test.js
```

## 测试场景

### 场景 1: 并发用户访问

**目标:** 测试系统在多用户同时访问时的性能

**配置:**
- 并发用户数: 50-100
- 每用户请求数: 20-50
- 测试时长: 60 秒

**测试操作:**
- 获取合同列表 (权重: 10)
- 获取合同详情 (权重: 8)
- 获取评审记录 (权重: 6)
- 搜索合同 (权重: 5)
- 添加评论 (权重: 4)
- 创建合同 (权重: 3)
- 上传附件 (权重: 2)
- AI 顾问查询 (权重: 1)

**预期结果:**
- 成功率: ≥ 95%
- 平均响应时间: < 500ms
- 95% 响应时间: < 1000ms
- RPS (每秒请求数): ≥ 100

### 场景 2: 大量数据加载

**目标:** 测试系统处理大量数据的能力

**准备工作:**
1. 创建测试数据:
   - 1000+ 合同
   - 5000+ 评审记录
   - 10000+ 评论

2. 测试操作:
   - 分页加载合同列表
   - 加载包含大量评审的合同详情
   - 搜索大量数据

**预期结果:**
- 分页查询响应时间: < 200ms
- 详情页加载时间: < 500ms
- 搜索响应时间: < 300ms

### 场景 3: 文件上传性能

**目标:** 测试文件上传的吞吐量和响应时间

**测试文件大小:**
- 100KB
- 500KB
- 1MB
- 5MB
- 10MB
- 20MB (最大限制)

**并发上传:**
- 10 个并发上传
- 每个文件 1MB

**预期结果:**
- 1MB 文件上传时间: < 2 秒
- 10MB 文件上传时间: < 10 秒
- 并发上传成功率: ≥ 95%

### 场景 4: WebSocket 连接数

**目标:** 测试实时通信的并发连接能力

**测试配置:**
- 并发连接数: 100-500
- 连接保持时间: 5 分钟
- 消息推送频率: 每秒 10 条

**预期结果:**
- 连接成功率: ≥ 95%
- 消息延迟: < 100ms
- 连接稳定性: 无异常断开

## 运行步骤

### 1. 准备环境

```bash
# 启动数据库和 Redis
docker-compose up -d postgres redis minio

# 启动后端服务
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 或使用 Gunicorn (生产环境)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 2. 准备测试数据

```bash
# 运行数据库迁移
alembic upgrade head

# 创建测试用户和合同 (可选)
python scripts/create_test_data.py
```

### 3. 运行压力测试

#### 使用 Locust

```bash
# 启动 Locust Web UI
locust -f tests/stress_test.py --host=http://localhost:8000

# 打开浏览器访问 http://localhost:8089
# 设置参数:
#   - Number of users: 100
#   - Spawn rate: 10
#   - Host: http://localhost:8000
# 点击 "Start swarming" 开始测试
```

#### 使用简单脚本

```bash
# 修改配置 (可选)
# 编辑 tests/simple_stress_test.py
# 修改 StressTestConfig 类的参数

# 运行测试
python tests/simple_stress_test.py
```

### 4. 监控系统资源

在测试过程中,监控以下指标:

```bash
# CPU 和内存使用
htop

# 数据库连接数
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Redis 内存使用
redis-cli info memory

# 网络连接数
netstat -an | grep 8000 | wc -l
```

## 结果分析

### 关键指标

1. **吞吐量 (Throughput)**
   - RPS (Requests Per Second): 每秒处理的请求数
   - 目标: ≥ 100 RPS

2. **响应时间 (Response Time)**
   - 平均响应时间: < 500ms
   - 50% 响应时间: < 300ms
   - 95% 响应时间: < 1000ms
   - 99% 响应时间: < 2000ms

3. **成功率 (Success Rate)**
   - 目标: ≥ 95%
   - 失败原因分析

4. **并发能力 (Concurrency)**
   - 最大并发用户数
   - 最大并发连接数

5. **资源使用 (Resource Usage)**
   - CPU 使用率: < 80%
   - 内存使用率: < 80%
   - 数据库连接数: < 最大连接数的 80%

### 性能瓶颈识别

#### 1. 数据库瓶颈

**症状:**
- 数据库 CPU 使用率高
- 查询响应时间长
- 连接池耗尽

**解决方案:**
- 添加数据库索引
- 优化 SQL 查询
- 增加数据库连接池大小
- 使用 Redis 缓存

#### 2. 应用服务器瓶颈

**症状:**
- 应用 CPU 使用率高
- 内存使用率高
- 响应时间随并发增加而线性增长

**解决方案:**
- 增加 Worker 进程数
- 使用异步处理
- 优化代码逻辑
- 水平扩展 (多实例)

#### 3. 网络瓶颈

**症状:**
- 网络带宽占用高
- 连接超时
- 响应时间不稳定

**解决方案:**
- 启用 Gzip 压缩
- 使用 CDN
- 优化响应数据大小
- 增加带宽

#### 4. 外部服务瓶颈

**症状:**
- AI 服务响应慢
- MinIO 上传/下载慢
- Redis 响应慢

**解决方案:**
- 增加超时时间
- 实现降级策略
- 使用异步任务队列
- 优化外部服务配置

## 优化建议

### 1. 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_contracts_created_at ON contracts(created_at DESC);
CREATE INDEX idx_reviews_contract_id ON reviews(contract_id);
CREATE INDEX idx_reviews_status ON reviews(status);

-- 分析查询性能
EXPLAIN ANALYZE SELECT * FROM contracts WHERE status = 'progress';
```

### 2. Redis 缓存优化

```python
# 缓存合同列表
cache_key = f"contract:list:{user_id}:{filter_type}"
await redis_client.setex(cache_key, 300, json.dumps(contracts))

# 缓存待办数量
cache_key = f"contract:pending:{user_id}"
await redis_client.setex(cache_key, 60, pending_count)
```

### 3. 应用代码优化

```python
# 使用批量查询
contracts = await db.execute(
    select(Contract)
    .options(selectinload(Contract.reviews))
    .filter(Contract.status == "progress")
)

# 使用异步任务
from app.tasks.ai_tasks import generate_summary_task
generate_summary_task.delay(contract_id)
```

### 4. 配置优化

```python
# config.py
DATABASE_POOL_SIZE = 20  # 增加连接池大小
DATABASE_MAX_OVERFLOW = 10
REDIS_MAX_CONNECTIONS = 50

# uvicorn 启动参数
uvicorn app.main:app --workers 4 --limit-concurrency 1000
```

## 常见问题

### Q1: 测试时出现大量 401 错误

**原因:** Token 无效或过期

**解决方案:**
1. 使用真实的 Token
2. 在测试脚本中实现 Token 刷新逻辑
3. 增加 Token 过期时间 (仅测试环境)

### Q2: 文件上传测试失败

**原因:** 
- 文件过大 (超过 20MB)
- MinIO 连接失败
- 合同 ID 不存在

**解决方案:**
1. 确保 MinIO 服务正常运行
2. 使用真实的合同 ID
3. 检查文件大小限制

### Q3: WebSocket 连接失败

**原因:**
- Socket.IO 服务未启动
- Token 认证失败
- 连接数超过限制

**解决方案:**
1. 确保 Socket.IO 服务正常运行
2. 检查 Token 认证逻辑
3. 增加最大连接数限制

### Q4: 数据库连接池耗尽

**原因:**
- 并发请求过多
- 连接未正确释放
- 连接池配置过小

**解决方案:**
1. 增加连接池大小
2. 检查代码中的连接泄漏
3. 使用连接池监控

## 测试报告模板

```markdown
# 压力测试报告

## 测试环境
- 服务器配置: 4 核 8GB
- 数据库: PostgreSQL 15
- 缓存: Redis 7
- 测试工具: Locust 2.x

## 测试场景
- 并发用户数: 100
- 测试时长: 60 秒
- 总请求数: 12000

## 测试结果

### 总体统计
- 成功率: 98.5%
- 平均响应时间: 320ms
- RPS: 200

### 各端点性能
| 端点 | 请求数 | 成功率 | 平均响应时间 | 95% 响应时间 |
|------|--------|--------|--------------|--------------|
| GET /api/contracts | 5000 | 99% | 250ms | 500ms |
| GET /api/contracts/:id | 3000 | 98% | 300ms | 600ms |
| POST /api/contracts | 500 | 95% | 800ms | 1500ms |

### 资源使用
- CPU 使用率: 65%
- 内存使用率: 45%
- 数据库连接数: 15/20

## 性能瓶颈
1. AI 服务响应较慢 (平均 2 秒)
2. 文件上传在高并发时偶尔超时

## 优化建议
1. 将 AI 服务改为异步任务
2. 增加文件上传超时时间
3. 添加更多数据库索引

## 结论
系统在 100 并发用户下表现良好,满足性能要求。
```

## 参考资料

- [Locust 官方文档](https://docs.locust.io/)
- [FastAPI 性能优化](https://fastapi.tiangolo.com/deployment/concepts/)
- [PostgreSQL 性能调优](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis 性能优化](https://redis.io/docs/management/optimization/)
