#!/bin/bash

# 合同预审看板系统 - 数据恢复脚本
# Contract Review System - Restore Script

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}♻️  合同预审看板系统数据恢复${NC}"
echo ""

# 检查参数
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ 错误: 请指定备份文件${NC}"
    echo ""
    echo "用法: ./scripts/restore.sh <backup-file.tar.gz>"
    echo ""
    echo "示例: ./scripts/restore.sh backups/20250101_120000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"

# 检查备份文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ 错误: 备份文件不存在: $BACKUP_FILE${NC}"
    exit 1
fi

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker 未安装${NC}"
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

echo -e "${YELLOW}📁 备份文件: $BACKUP_FILE${NC}"
echo -e "${YELLOW}📦 文件大小: $(du -h "$BACKUP_FILE" | cut -f1)${NC}"
echo ""

# 警告提示
echo -e "${RED}⚠️  警告: 恢复操作将覆盖当前所有数据！${NC}"
echo ""
read -p "确认要继续吗? [y/N]: " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 0
fi

echo ""

# 创建临时目录
TEMP_DIR="$PROJECT_ROOT/temp_restore_$$"
mkdir -p "$TEMP_DIR"

echo -e "${GREEN}📦 解压备份文件...${NC}"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# 查找解压后的目录
BACKUP_DIR=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)

if [ -z "$BACKUP_DIR" ]; then
    echo -e "${RED}❌ 错误: 无法找到备份目录${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo -e "${GREEN}✅ 备份文件解压成功${NC}"
echo ""

# 显示备份信息
if [ -f "$BACKUP_DIR/backup_info.txt" ]; then
    echo -e "${BLUE}📋 备份信息:${NC}"
    cat "$BACKUP_DIR/backup_info.txt"
    echo ""
fi

# 检查服务是否运行
echo -e "${GREEN}🔍 检查服务状态...${NC}"
SERVICES_RUNNING=$(docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | wc -l)

if [ "$SERVICES_RUNNING" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  服务未运行，正在启动...${NC}"
    docker compose -f "$COMPOSE_FILE" up -d
    sleep 10
fi

echo ""

# 恢复 PostgreSQL 数据库
if [ -f "$BACKUP_DIR/postgres_backup.sql" ]; then
    echo -e "${GREEN}🗄️  恢复 PostgreSQL 数据库...${NC}"
    
    # 停止后端服务以避免连接冲突
    docker compose -f "$COMPOSE_FILE" stop backend
    
    # 删除现有数据库并重新创建
    docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS contract_review;"
    docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres -c "CREATE DATABASE contract_review;"
    
    # 恢复数据
    docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres contract_review < "$BACKUP_DIR/postgres_backup.sql"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PostgreSQL 恢复成功${NC}"
    else
        echo -e "${RED}❌ PostgreSQL 恢复失败${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # 重启后端服务
    docker compose -f "$COMPOSE_FILE" start backend
else
    echo -e "${YELLOW}⚠️  未找到 PostgreSQL 备份文件${NC}"
fi

echo ""

# 恢复 Redis 数据
if [ -f "$BACKUP_DIR/redis_backup.rdb" ]; then
    echo -e "${GREEN}💾 恢复 Redis 数据...${NC}"
    
    # 停止 Redis
    docker compose -f "$COMPOSE_FILE" stop redis
    
    # 复制备份文件
    REDIS_CONTAINER=$(docker compose -f "$COMPOSE_FILE" ps -q redis)
    docker cp "$BACKUP_DIR/redis_backup.rdb" "$REDIS_CONTAINER:/data/dump.rdb"
    
    # 启动 Redis
    docker compose -f "$COMPOSE_FILE" start redis
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Redis 恢复成功${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis 恢复失败${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  未找到 Redis 备份文件${NC}"
fi

echo ""

# 恢复 MinIO 数据
if [ -d "$BACKUP_DIR/minio_backup/data" ]; then
    echo -e "${GREEN}📦 恢复 MinIO 数据...${NC}"
    
    # 停止 MinIO
    docker compose -f "$COMPOSE_FILE" stop minio
    
    # 复制备份数据
    MINIO_CONTAINER=$(docker compose -f "$COMPOSE_FILE" ps -q minio)
    docker cp "$BACKUP_DIR/minio_backup/data/." "$MINIO_CONTAINER:/data/"
    
    # 启动 MinIO
    docker compose -f "$COMPOSE_FILE" start minio
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ MinIO 恢复成功${NC}"
    else
        echo -e "${YELLOW}⚠️  MinIO 恢复失败${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  未找到 MinIO 备份目录${NC}"
fi

echo ""

# 恢复环境变量文件
if [ -f "$BACKUP_DIR/.env.backup" ]; then
    echo -e "${GREEN}⚙️  恢复环境变量文件...${NC}"
    
    # 备份当前的 .env 文件
    if [ -f "$PROJECT_ROOT/.env" ]; then
        cp "$PROJECT_ROOT/.env" "$PROJECT_ROOT/.env.old"
        echo -e "${YELLOW}   当前 .env 已备份为 .env.old${NC}"
    fi
    
    cp "$BACKUP_DIR/.env.backup" "$PROJECT_ROOT/.env"
    echo -e "${GREEN}✅ 环境变量文件恢复成功${NC}"
else
    echo -e "${YELLOW}⚠️  未找到环境变量备份文件${NC}"
fi

echo ""

# 清理临时目录
echo -e "${GREEN}🧹 清理临时文件...${NC}"
rm -rf "$TEMP_DIR"
echo -e "${GREEN}✅ 清理完成${NC}"

echo ""

# 重启所有服务
echo -e "${GREEN}🔄 重启所有服务...${NC}"
docker compose -f "$COMPOSE_FILE" restart

echo ""
echo -e "${GREEN}🎉 数据恢复完成！${NC}"
echo ""
echo "💡 建议:"
echo "  1. 检查服务状态: ./scripts/status.sh"
echo "  2. 查看服务日志: ./scripts/logs.sh"
echo "  3. 访问应用验证数据: http://localhost"
echo ""
echo "⚠️  注意: 如果恢复后出现问题，可以使用 .env.old 恢复之前的配置"
