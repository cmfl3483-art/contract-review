#!/bin/bash

# 合同预审看板系统 - 启动基础设施服务脚本
# Contract Review System - Start Infrastructure Services Script

set -e

echo "🚀 启动合同预审看板系统基础设施服务..."
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装"
    echo "请访问 https://www.docker.com/get-started 安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否可用
if ! docker compose version &> /dev/null; then
    echo "❌ 错误: Docker Compose 未安装或版本过低"
    echo "请确保安装了 Docker Compose V2"
    exit 1
fi

# 启动服务
echo "📦 启动 Docker Compose 服务..."
docker compose up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker compose ps

echo ""
echo "✅ 服务启动完成！"
echo ""
echo "📝 服务访问信息:"
echo "  - PostgreSQL: localhost:5432 (用户名: postgres, 密码: postgres)"
echo "  - Redis: localhost:6379"
echo "  - MinIO API: http://localhost:9000"
echo "  - MinIO Console: http://localhost:9001 (用户名: minioadmin, 密码: minioadmin)"
echo ""
echo "💡 提示:"
echo "  - 查看日志: docker compose logs -f"
echo "  - 停止服务: docker compose down"
echo "  - 查看详细文档: cat DOCKER_SETUP.md"
