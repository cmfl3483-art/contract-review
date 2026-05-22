#!/bin/bash

# 合同预审看板系统 - 状态检查脚本
# Contract Review System - Status Check Script

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 合同预审看板系统状态检查${NC}"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 确定使用的 compose 文件
if [ -f "docker/docker-compose.prod.yml" ]; then
    COMPOSE_FILE="docker/docker-compose.prod.yml"
elif [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
else
    echo -e "${RED}❌ 未找到 docker-compose 配置文件${NC}"
    exit 1
fi

# 显示容器状态
echo -e "${GREEN}🐳 Docker 容器状态:${NC}"
docker compose -f "$COMPOSE_FILE" ps
echo ""

# 检查各服务健康状态
echo -e "${GREEN}🏥 服务健康检查:${NC}"
echo ""

# 检查 PostgreSQL
echo -n "PostgreSQL: "
if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康${NC}"
else
    echo -e "${RED}❌ 不健康${NC}"
fi

# 检查 Redis
echo -n "Redis: "
if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康${NC}"
else
    echo -e "${RED}❌ 不健康${NC}"
fi

# 检查 MinIO
echo -n "MinIO: "
if curl -f -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康${NC}"
else
    echo -e "${RED}❌ 不健康${NC}"
fi

# 检查后端 API
echo -n "后端 API: "
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康${NC}"
    # 获取 API 版本信息
    API_INFO=$(curl -s http://localhost:8000/health | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$API_INFO" ]; then
        echo "  版本: $API_INFO"
    fi
else
    echo -e "${RED}❌ 不健康${NC}"
fi

# 检查前端
echo -n "前端应用: "
if curl -f -s http://localhost:80 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康${NC}"
else
    echo -e "${RED}❌ 不健康${NC}"
fi

echo ""

# 显示资源使用情况
echo -e "${GREEN}💾 资源使用情况:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $(docker compose -f "$COMPOSE_FILE" ps -q)

echo ""

# 显示磁盘使用情况
echo -e "${GREEN}💿 数据卷使用情况:${NC}"
docker volume ls --filter "name=contract" --format "table {{.Name}}\t{{.Driver}}\t{{.Mountpoint}}"

echo ""

# 显示访问地址
echo -e "${GREEN}🌐 服务访问地址:${NC}"
echo "  - 前端应用: http://localhost"
echo "  - 后端 API: http://localhost:8000"
echo "  - API 文档: http://localhost:8000/api/docs"
echo "  - MinIO Console: http://localhost:9001"

echo ""
echo "💡 提示:"
echo "  - 查看日志: ./scripts/logs.sh"
echo "  - 重启服务: ./scripts/restart.sh"
echo "  - 停止服务: ./scripts/stop.sh"
