#!/bin/bash

# 合同预审看板系统 - 停止脚本
# Contract Review System - Stop Script

set -e

echo "🛑 停止合同预审看板系统..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker 未安装${NC}"
    exit 1
fi

# 检查 Docker Compose 是否可用
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker Compose 未安装或版本过低${NC}"
    exit 1
fi

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}📦 项目根目录: $PROJECT_ROOT${NC}"
echo ""

# 检查是否有运行的服务
if [ -f "docker/docker-compose.prod.yml" ]; then
    COMPOSE_FILE="docker/docker-compose.prod.yml"
elif [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
else
    echo -e "${RED}❌ 错误: 未找到 docker-compose 配置文件${NC}"
    exit 1
fi

# 显示当前运行的服务
echo -e "${GREEN}📊 当前运行的服务:${NC}"
docker compose -f "$COMPOSE_FILE" ps
echo ""

# 询问是否删除数据卷
read -p "是否删除数据卷 (数据库、Redis、MinIO 数据)? [y/N]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️  停止服务并删除数据卷...${NC}"
    docker compose -f "$COMPOSE_FILE" down -v
    echo -e "${GREEN}✅ 服务已停止，数据卷已删除${NC}"
else
    echo -e "${YELLOW}🛑 停止服务 (保留数据卷)...${NC}"
    docker compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}✅ 服务已停止，数据卷已保留${NC}"
fi

echo ""
echo "💡 提示:"
echo "  - 重新启动服务: ./scripts/start.sh"
echo "  - 查看所有容器: docker ps -a"
echo "  - 查看所有镜像: docker images"
echo "  - 清理未使用的资源: docker system prune"
