#!/bin/bash

# AI 顾问问答 API 测试脚本
# 测试 POST /api/ai/advisor 端点

echo "=========================================="
echo "AI 顾问问答 API 测试"
echo "=========================================="
echo ""

# 配置
API_BASE="http://localhost:8000"
TOKEN="YOUR_JWT_TOKEN_HERE"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_advisor() {
    local question=$1
    local contract_id=${2:-"test-contract-id"}
    
    echo -e "${YELLOW}问题:${NC} $question"
    echo ""
    
    response=$(curl -s -X POST "$API_BASE/api/ai/advisor" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{
            \"contract_id\": \"$contract_id\",
            \"question\": \"$question\"
        }")
    
    # 检查响应
    if echo "$response" | grep -q '"success": true'; then
        echo -e "${GREEN}✅ 请求成功${NC}"
        echo ""
        echo "回答:"
        echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['answer'])"
    else
        echo -e "${RED}❌ 请求失败${NC}"
        echo "$response"
    fi
    
    echo ""
    echo "------------------------------------------"
    echo ""
}

# 检查服务是否运行
echo "检查服务状态..."
if curl -s "$API_BASE/health" > /dev/null; then
    echo -e "${GREEN}✅ 服务正在运行${NC}"
    echo ""
else
    echo -e "${RED}❌ 服务未运行,请先启动后端服务${NC}"
    echo ""
    echo "启动命令:"
    echo "  cd backend"
    echo "  uvicorn app.main:app --reload"
    echo ""
    exit 1
fi

# 提示用户配置 Token
if [ "$TOKEN" = "YOUR_JWT_TOKEN_HERE" ]; then
    echo -e "${YELLOW}⚠️  请先配置 JWT Token${NC}"
    echo ""
    echo "获取 Token 的方法:"
    echo "1. 登录系统获取 Token"
    echo "2. 或者修改此脚本,将 TOKEN 变量设置为实际的 JWT Token"
    echo ""
    echo "示例:"
    echo "  TOKEN=\"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\""
    echo ""
    exit 1
fi

# 运行测试
echo "开始测试..."
echo ""

# 测试 1: 法务意见查询
test_advisor "法务意见是什么?"

# 测试 2: 风险项查询
test_advisor "有哪些风险项?"

# 测试 3: 待办任务查询
test_advisor "待我处理的任务有哪些?"

# 测试 4: 默认回复
test_advisor "这个合同怎么样?"

echo "=========================================="
echo "测试完成"
echo "=========================================="
