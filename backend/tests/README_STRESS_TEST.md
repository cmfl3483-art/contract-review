# 压力测试快速开始
# Stress Testing Quick Start

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements-stress-test.txt
```

### 2. 启动服务

确保以下服务正在运行:

```bash
# 启动数据库和 Redis
docker-compose up -d postgres redis minio

# 启动后端服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 生成测试数据 (可选)

```bash
python scripts/create_stress_test_data.py --action generate
```

### 4. 运行压力测试

#### 方法 1: 使用快速启动脚本 (推荐)

```bash
./run_stress_test.sh
```

#### 方法 2: 使用 Locust

```bash
# Web UI 模式
locust -f tests/stress_test.py --host=http://localhost:8000

# 打开浏览器访问 http://localhost:8089
```

#### 方法 3: 使用简单脚本

```bash
python tests/simple_stress_test.py
```

## 测试场景

1. **并发用户访问** - 测试 50-100 个并发用户
2. **大量数据加载** - 测试 1000+ 合同的加载性能
3. **文件上传性能** - 测试不同大小文件的上传
4. **WebSocket 连接** - 测试 100-500 个并发连接

## 详细文档

查看 [STRESS_TEST_GUIDE.md](../STRESS_TEST_GUIDE.md) 获取完整的压力测试指南。

## 清理测试数据

```bash
python scripts/create_stress_test_data.py --action cleanup
```

## 性能目标

- 成功率: ≥ 95%
- 平均响应时间: < 500ms
- RPS: ≥ 100
- 并发用户数: ≥ 100

## 问题反馈

如遇到问题,请查看 [STRESS_TEST_GUIDE.md](../STRESS_TEST_GUIDE.md) 中的常见问题部分。
