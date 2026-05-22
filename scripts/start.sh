#!/bin/bash

# 合同预审看板系统 - 启动脚本
# Contract Review System - Start Script

set -e

echo "🚀 启动合同预审看板系统..."
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

# 检查环境变量文件
if [ ! -f "docker/docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ 错误: docker-compose.prod.yml 不存在${NC}"
    echo "请先运行构建脚本: ./scripts/build.sh"
    exit 1
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  警告: .env 文件不存在${NC}"
    echo "使用默认配置启动..."
    if [ -f ".env.example" ]; then
        echo "💡 提示: 可以复制 .env.example 为 .env 并修改配置"
    fi
fi

# 启动服务
echo -e "${GREEN}🐳 启动 Docker Compose 服务...${NC}"
docker compose -f docker/docker-compose.prod.yml up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo ""
echo -e "${GREEN}📊 服务状态:${NC}"
docker compose -f docker/docker-compose.prod.yml ps

echo ""

# 检查服务健康状态
echo -e "${GREEN}🏥 检查服务健康状态...${NC}"
echo ""

# 检查 PostgreSQL
if docker compose -f docker/docker-compose.prod.yml exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL: 健康${NC}"
else
    echo -e "${RED}❌ PostgreSQL: 不健康${NC}"
fi

# 检查 Redis
if docker compose -f docker/docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis: 健康${NC}"
else
    echo -e "${RED}❌ Redis: 不健康${NC}"
fi

# 检查 MinIO
if curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MinIO: 健康${NC}"
else
    echo -e "${YELLOW}⚠️  MinIO: 检查失败 (可能正在启动)${NC}"
fi

# 检查后端
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端 API: 健康${NC}"
else
    echo -e "${YELLOW}⚠️  后端 API: 检查失败 (可能正在启动)${NC}"
fi

# 检查前端
if curl -f http://localhost:80 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 前端: 健康${NC}"
else
    echo -e "${YELLOW}⚠️  前端: 检查失败 (可能正在启动)${NC}"
fi

echo ""
echo -e "${GREEN}✅ 服务启动完成！${NC}"
echo ""
echo "📝 服务访问信息:"
echo "  - 前端应用: http://localhost"
echo "  - 后端 API: http://localhost:8000"
echo "  - API 文档: http://localhost:8000/api/docs"
echo "  - MinIO Console: http://localhost:9001 (用户名: minioadmin, 密码: minioadmin)"
echo ""
echo "💡 常用命令:"
echo "  - 查看日志: ./scripts/logs.sh"
echo "  - 查看特定服务日志: ./scripts/logs.sh [service-name]"
echo "  - 停止服务: ./scripts/stop.sh"
echo "  - 重启服务: ./scripts/restart.sh"
echo ""
echo "📚 更多信息请查看文档: cat README.md"
