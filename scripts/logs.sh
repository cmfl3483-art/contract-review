#!/bin/bash

# 合同预审看板系统 - 日志查看脚本
# Contract Review System - Logs Script

set -e

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

# 确定使用的 compose 文件
if [ -f "docker/docker-compose.prod.yml" ]; then
    COMPOSE_FILE="docker/docker-compose.prod.yml"
elif [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
else
    echo -e "${RED}❌ 错误: 未找到 docker-compose 配置文件${NC}"
    exit 1
fi

# 显示帮助信息
show_help() {
    echo "📋 日志查看脚本使用说明"
    echo ""
    echo "用法:"
    echo "  ./scripts/logs.sh [service-name] [options]"
    echo ""
    echo "服务名称:"
    echo "  backend     - 后端 API 服务"
    echo "  frontend    - 前端 Web 服务"
    echo "  postgres    - PostgreSQL 数据库"
    echo "  redis       - Redis 缓存"
    echo "  minio       - MinIO 对象存储"
    echo "  nginx       - Nginx 反向代理"
    echo "  (不指定服务名则显示所有服务日志)"
    echo ""
    echo "选项:"
    echo "  -f, --follow    实时跟踪日志 (默认)"
    echo "  -n, --tail N    显示最后 N 行日志"
    echo "  -h, --help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./scripts/logs.sh                    # 查看所有服务日志"
    echo "  ./scripts/logs.sh backend            # 查看后端服务日志"
    echo "  ./scripts/logs.sh backend -n 100     # 查看后端最后 100 行日志"
    echo "  ./scripts/logs.sh frontend --follow  # 实时跟踪前端日志"
}

# 解析参数
SERVICE=""
FOLLOW="-f"
TAIL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--follow)
            FOLLOW="-f"
            shift
            ;;
        -n|--tail)
            TAIL="--tail $2"
            shift 2
            ;;
        backend|frontend|postgres|redis|minio|nginx)
            SERVICE="$1"
            shift
            ;;
        *)
            echo -e "${RED}❌ 未知参数: $1${NC}"
            echo "使用 -h 或 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 显示日志
echo -e "${GREEN}📋 查看日志...${NC}"
echo ""

if [ -z "$SERVICE" ]; then
    echo -e "${YELLOW}显示所有服务日志 (按 Ctrl+C 退出)${NC}"
    echo ""
    docker compose -f "$COMPOSE_FILE" logs $FOLLOW $TAIL
else
    echo -e "${YELLOW}显示 $SERVICE 服务日志 (按 Ctrl+C 退出)${NC}"
    echo ""
    docker compose -f "$COMPOSE_FILE" logs $FOLLOW $TAIL "$SERVICE"
fi
