#!/bin/bash

# Docker 构建脚本
# 用于构建所有 Docker 镜像

set -e

echo "======================================"
echo "开始构建 Docker 镜像..."
echo "======================================"

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行,请先启动 Docker"
    exit 1
fi

# 构建后端镜像
echo ""
echo "构建后端镜像..."
docker build -t contract-review-backend:latest ./backend

# 构建前端镜像
echo ""
echo "构建前端镜像..."
docker build -t contract-review-frontend:latest ./frontend

echo ""
echo "======================================"
echo "所有镜像构建完成!"
echo "======================================"
echo ""
echo "可用镜像:"
docker images | grep contract-review
