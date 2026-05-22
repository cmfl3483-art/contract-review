#!/bin/bash

# 合同预审看板系统 - 数据备份脚本
# Contract Review System - Backup Script

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}💾 合同预审看板系统数据备份${NC}"
echo ""

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

# 创建备份目录
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"

mkdir -p "$BACKUP_PATH"

echo -e "${YELLOW}📁 备份目录: $BACKUP_PATH${NC}"
echo ""

# 备份 PostgreSQL 数据库
echo -e "${GREEN}🗄️  备份 PostgreSQL 数据库...${NC}"
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U postgres contract_review > "$BACKUP_PATH/postgres_backup.sql"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PostgreSQL 备份成功${NC}"
    echo "   文件: $BACKUP_PATH/postgres_backup.sql"
    echo "   大小: $(du -h "$BACKUP_PATH/postgres_backup.sql" | cut -f1)"
else
    echo -e "${RED}❌ PostgreSQL 备份失败${NC}"
    exit 1
fi

echo ""

# 备份 Redis 数据
echo -e "${GREEN}💾 备份 Redis 数据...${NC}"
docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli --rdb /data/dump.rdb SAVE > /dev/null 2>&1
docker cp $(docker compose -f "$COMPOSE_FILE" ps -q redis):/data/dump.rdb "$BACKUP_PATH/redis_backup.rdb"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Redis 备份成功${NC}"
    echo "   文件: $BACKUP_PATH/redis_backup.rdb"
    echo "   大小: $(du -h "$BACKUP_PATH/redis_backup.rdb" | cut -f1)"
else
    echo -e "${YELLOW}⚠️  Redis 备份失败 (可能没有数据)${NC}"
fi

echo ""

# 备份 MinIO 数据
echo -e "${GREEN}📦 备份 MinIO 数据...${NC}"
MINIO_BACKUP_DIR="$BACKUP_PATH/minio_backup"
mkdir -p "$MINIO_BACKUP_DIR"

# 使用 docker cp 复制 MinIO 数据
MINIO_CONTAINER=$(docker compose -f "$COMPOSE_FILE" ps -q minio)
if [ -n "$MINIO_CONTAINER" ]; then
    docker cp "$MINIO_CONTAINER:/data" "$MINIO_BACKUP_DIR/"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ MinIO 备份成功${NC}"
        echo "   目录: $MINIO_BACKUP_DIR"
        echo "   大小: $(du -sh "$MINIO_BACKUP_DIR" | cut -f1)"
    else
        echo -e "${YELLOW}⚠️  MinIO 备份失败${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  MinIO 容器未运行，跳过备份${NC}"
fi

echo ""

# 备份环境变量文件
echo -e "${GREEN}⚙️  备份配置文件...${NC}"
if [ -f "$PROJECT_ROOT/.env" ]; then
    cp "$PROJECT_ROOT/.env" "$BACKUP_PATH/.env.backup"
    echo -e "${GREEN}✅ 环境变量文件备份成功${NC}"
else
    echo -e "${YELLOW}⚠️  未找到 .env 文件${NC}"
fi

echo ""

# 创建备份信息文件
echo -e "${GREEN}📝 创建备份信息文件...${NC}"
cat > "$BACKUP_PATH/backup_info.txt" << EOF
备份时间: $(date +"%Y-%m-%d %H:%M:%S")
备份目录: $BACKUP_PATH
系统版本: $(cat "$PROJECT_ROOT/VERSION" 2>/dev/null || echo "未知")

备份内容:
- PostgreSQL 数据库
- Redis 缓存数据
- MinIO 对象存储
- 环境变量配置

备份文件:
$(ls -lh "$BACKUP_PATH")

总大小: $(du -sh "$BACKUP_PATH" | cut -f1)
EOF

echo -e "${GREEN}✅ 备份信息文件创建成功${NC}"

echo ""

# 压缩备份
echo -e "${GREEN}🗜️  压缩备份文件...${NC}"
cd "$BACKUP_DIR"
tar -czf "${TIMESTAMP}.tar.gz" "$TIMESTAMP"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 备份压缩成功${NC}"
    echo "   文件: $BACKUP_DIR/${TIMESTAMP}.tar.gz"
    echo "   大小: $(du -h "$BACKUP_DIR/${TIMESTAMP}.tar.gz" | cut -f1)"
    
    # 删除未压缩的备份目录
    rm -rf "$BACKUP_PATH"
    echo -e "${GREEN}✅ 清理临时文件完成${NC}"
else
    echo -e "${RED}❌ 备份压缩失败${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 备份完成！${NC}"
echo ""
echo "📋 备份信息:"
echo "  - 备份文件: $BACKUP_DIR/${TIMESTAMP}.tar.gz"
echo "  - 备份时间: $(date +"%Y-%m-%d %H:%M:%S")"
echo "  - 文件大小: $(du -h "$BACKUP_DIR/${TIMESTAMP}.tar.gz" | cut -f1)"
echo ""
echo "💡 恢复备份:"
echo "  ./scripts/restore.sh $BACKUP_DIR/${TIMESTAMP}.tar.gz"
echo ""
echo "🗑️  清理旧备份:"
echo "  find $BACKUP_DIR -name '*.tar.gz' -mtime +30 -delete"
