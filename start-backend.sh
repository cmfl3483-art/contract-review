#!/bin/bash

# 合同预审看板系统 - 后端启动脚本

echo "🚀 启动合同预审看板系统后端..."
echo ""

# 检查Docker服务是否运行
echo "📦 检查Docker服务..."
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker未运行,请先启动Docker"
    exit 1
fi

# 启动Docker Compose服务
echo "🐳 启动Docker Compose服务 (PostgreSQL, Redis, MinIO)..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker-compose ps

# 进入后端目录
cd backend

# 检查数据库迁移
echo ""
echo "🗄️  检查数据库迁移..."
if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
    echo "⚠️  未找到迁移文件,跳过迁移"
else
    echo "📝 运行数据库迁移..."
    alembic upgrade head
fi

# 启动后端服务
echo ""
echo "🎯 启动FastAPI服务..."
echo "📍 API文档: http://localhost:8000/api/docs"
echo "📍 健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
