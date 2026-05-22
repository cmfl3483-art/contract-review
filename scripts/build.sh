#!/bin/bash

# 合同预审看板系统 - 构建脚本
# Contract Review System - Build Script

set -e

echo "🔨 开始构建合同预审看板系统..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker 未安装${NC}"
    echo "请访问 https://www.docker.com/get-started 安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否可用
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker Compose 未安装或版本过低${NC}"
    echo "请确保安装了 Docker Compose V2"
    exit 1
fi

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}📦 项目根目录: $PROJECT_ROOT${NC}"
echo ""

# 构建前端
echo -e "${GREEN}🎨 构建前端应用...${NC}"
cd frontend

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "📥 安装前端依赖..."
    npm install
fi

# 构建前端
echo "🔨 执行前端构建..."
npm run build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 前端构建成功${NC}"
else
    echo -e "${RED}❌ 前端构建失败${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"
echo ""

# 构建后端
echo -e "${GREEN}🐍 准备后端应用...${NC}"
cd backend

# 检查 requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ 错误: requirements.txt 不存在${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 后端依赖文件检查通过${NC}"

cd "$PROJECT_ROOT"
echo ""

# 构建 Docker 镜像
echo -e "${GREEN}🐳 构建 Docker 镜像...${NC}"
echo ""

# 构建后端镜像
echo "📦 构建后端镜像..."
docker build -t contract-review-backend:latest -f docker/backend/Dockerfile .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 后端镜像构建成功${NC}"
else
    echo -e "${RED}❌ 后端镜像构建失败${NC}"
    exit 1
fi

echo ""

# 构建前端镜像
echo "📦 构建前端镜像..."
docker build -t contract-review-frontend:latest -f docker/frontend/Dockerfile .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 前端镜像构建成功${NC}"
else
    echo -e "${RED}❌ 前端镜像构建失败${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 所有镜像构建完成！${NC}"
echo ""
echo "📋 构建的镜像:"
docker images | grep contract-review

echo ""
echo -e "${GREEN}✅ 构建完成！${NC}"
echo ""
echo "💡 下一步:"
echo "  - 启动服务: ./scripts/start.sh"
echo "  - 查看日志: ./scripts/logs.sh"
echo "  - 停止服务: ./scripts/stop.sh"
