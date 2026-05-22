#!/bin/bash

# Docker 启动脚本
# 用于启动所有服务

set -e

echo "======================================"
echo "启动合同预审看板系统..."
echo "======================================"

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行,请先启动 Docker"
    exit 1
fi

# 检查环境变量文件
if [ ! -f .env.production ]; then
    echo "警告: .env.production 文件不存在"
    echo "将使用 docker-compose.yml 中的默认配置"
    echo "建议复制 .env.production.example 为 .env.production 并填写实际值"
    echo ""
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 加载环境变量
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# 启动服务
echo ""
echo "启动所有服务..."
docker-compose up -d

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "======================================"
echo "服务状态:"
echo "======================================"
docker-compose ps

# 运行数据库迁移
echo ""
echo "======================================"
echo "运行数据库迁移..."
echo "======================================"
docker-compose exec backend alembic upgrade head

# 初始化 MinIO bucket
echo ""
echo "======================================"
echo "初始化 MinIO bucket..."
echo "======================================"
docker-compose exec backend python -c "
from app.core.minio_client import init_minio_bucket
import asyncio
asyncio.run(init_minio_bucket())
print('MinIO bucket 初始化完成')
"

echo ""
echo "======================================"
echo "系统启动完成!"
echo "======================================"
echo ""
echo "访问地址:"
echo "  前端: http://localhost"
echo "  后端 API: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo "  MinIO 控制台: http://localhost:9001"
echo ""
echo "查看日志:"
echo "  所有服务: docker-compose logs -f"
echo "  后端: docker-compose logs -f backend"
echo "  前端: docker-compose logs -f frontend"
echo "  Celery: docker-compose logs -f celery_worker"
echo ""
