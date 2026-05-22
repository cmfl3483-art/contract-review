#!/bin/bash

# 合同预审看板系统 - 重启脚本
# Contract Review System - Restart Script

set -e

echo "🔄 重启合同预审看板系统..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 解析参数
SERVICE=""

if [ $# -gt 0 ]; then
    SERVICE="$1"
    echo -e "${YELLOW}重启服务: $SERVICE${NC}"
else
    echo -e "${YELLOW}重启所有服务${NC}"
fi

echo ""

# 确定使用的 compose 文件
if [ -f "docker/docker-compose.prod.yml" ]; then
    COMPOSE_FILE="docker/docker-compose.prod.yml"
elif [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
else
    echo -e "${RED}❌ 错误: 未找到 docker-compose 配置文件${NC}"
    exit 1
fi

# 重启服务
if [ -z "$SERVICE" ]; then
    echo -e "${GREEN}🔄 重启所有服务...${NC}"
    docker compose -f "$COMPOSE_FILE" restart
else
    echo -e "${GREEN}🔄 重启 $SERVICE 服务...${NC}"
    docker compose -f "$COMPOSE_FILE" restart "$SERVICE"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 重启完成！${NC}"
    echo ""
    echo "💡 提示:"
    echo "  - 查看日志: ./scripts/logs.sh"
    if [ -n "$SERVICE" ]; then
        echo "  - 查看 $SERVICE 日志: ./scripts/logs.sh $SERVICE"
    fi
    echo "  - 查看服务状态: docker compose -f $COMPOSE_FILE ps"
else
    echo ""
    echo -e "${RED}❌ 重启失败${NC}"
    exit 1
fi
