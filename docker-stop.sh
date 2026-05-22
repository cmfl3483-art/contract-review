#!/bin/bash

# Docker 停止脚本
# 用于停止所有服务

set -e

echo "======================================"
echo "停止合同预审看板系统..."
echo "======================================"

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行"
    exit 1
fi

# 停止服务
docker-compose down

echo ""
echo "======================================"
echo "所有服务已停止"
echo "======================================"
echo ""
echo "如需删除数据卷,请运行:"
echo "  docker-compose down -v"
echo ""
