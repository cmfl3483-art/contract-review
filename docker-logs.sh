#!/bin/bash

# Docker 日志查看脚本
# 用于查看服务日志

# 检查参数
if [ $# -eq 0 ]; then
    echo "查看所有服务日志..."
    docker-compose logs -f
elif [ "$1" == "backend" ]; then
    echo "查看后端日志..."
    docker-compose logs -f backend
elif [ "$1" == "frontend" ]; then
    echo "查看前端日志..."
    docker-compose logs -f frontend
elif [ "$1" == "celery" ]; then
    echo "查看 Celery Worker 日志..."
    docker-compose logs -f celery_worker
elif [ "$1" == "postgres" ]; then
    echo "查看 PostgreSQL 日志..."
    docker-compose logs -f postgres
elif [ "$1" == "redis" ]; then
    echo "查看 Redis 日志..."
    docker-compose logs -f redis
elif [ "$1" == "minio" ]; then
    echo "查看 MinIO 日志..."
    docker-compose logs -f minio
else
    echo "用法: $0 [service]"
    echo ""
    echo "可用服务:"
    echo "  backend   - 后端服务"
    echo "  frontend  - 前端服务"
    echo "  celery    - Celery Worker"
    echo "  postgres  - PostgreSQL 数据库"
    echo "  redis     - Redis 缓存"
    echo "  minio     - MinIO 对象存储"
    echo ""
    echo "不指定服务则查看所有日志"
    exit 1
fi
