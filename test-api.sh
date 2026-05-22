#!/bin/bash

# 合同预审看板系统 - API测试脚本

echo "🧪 测试合同预审看板系统API..."
echo ""

BASE_URL="http://localhost:8000"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_api() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    
    echo -n "测试 $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url")
    fi
    
    if [ "$response" = "200" ] || [ "$response" = "401" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $response)"
    else
        echo -e "${RED}✗${NC} (HTTP $response)"
    fi
}

# 1. 健康检查
echo "📊 基础检查"
echo "─────────────────────────────────────"
test_api "健康检查" "$BASE_URL/health"
test_api "根路径" "$BASE_URL/"
echo ""

# 2. 认证API
echo "🔐 认证API"
echo "─────────────────────────────────────"
test_api "获取钉钉授权URL" "$BASE_URL/api/auth/dingtalk/login"
test_api "获取当前用户信息" "$BASE_URL/api/auth/me"
echo ""

# 3. 合同API (需要认证,预期401)
echo "📝 合同API"
echo "─────────────────────────────────────"
test_api "获取合同列表" "$BASE_URL/api/contracts"
test_api "创建合同" "$BASE_URL/api/contracts" "POST"
echo ""

# 4. API文档
echo "📚 API文档"
echo "─────────────────────────────────────"
test_api "Swagger UI" "$BASE_URL/api/docs"
test_api "ReDoc" "$BASE_URL/api/redoc"
test_api "OpenAPI JSON" "$BASE_URL/api/openapi.json"
echo ""

# 5. 检查Docker服务
echo "🐳 Docker服务"
echo "─────────────────────────────────────"

if docker ps | grep -q postgres; then
    echo -e "${GREEN}✓${NC} PostgreSQL 运行中"
else
    echo -e "${RED}✗${NC} PostgreSQL 未运行"
fi

if docker ps | grep -q redis; then
    echo -e "${GREEN}✓${NC} Redis 运行中"
else
    echo -e "${RED}✗${NC} Redis 未运行"
fi

if docker ps | grep -q minio; then
    echo -e "${GREEN}✓${NC} MinIO 运行中"
else
    echo -e "${RED}✗${NC} MinIO 未运行"
fi

echo ""
echo "─────────────────────────────────────"
echo "测试完成!"
echo ""
echo "💡 提示:"
echo "  - 访问 API 文档: $BASE_URL/api/docs"
echo "  - 访问 MinIO 控制台: http://localhost:9001"
echo "  - 大部分API需要JWT Token认证"
echo ""
