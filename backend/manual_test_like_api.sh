#!/bin/bash

# 点赞 API 手动测试脚本
# 使用方法: ./manual_test_like_api.sh

echo "========================================="
echo "点赞 API 手动测试"
echo "========================================="
echo ""

# 配置
API_BASE_URL="http://localhost:8000"
TOKEN="your_jwt_token_here"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}注意: 请先启动后端服务并替换 TOKEN 变量${NC}"
echo ""

# 测试 1: 点赞评审意见
echo "========================================="
echo "测试 1: 点赞评审意见"
echo "========================================="
REVIEW_ID="test-review-id"
echo "POST ${API_BASE_URL}/api/reviews/${REVIEW_ID}/like"
echo ""

curl -X POST "${API_BASE_URL}/api/reviews/${REVIEW_ID}/like" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'

echo ""
echo ""

# 测试 2: 取消点赞评审意见
echo "========================================="
echo "测试 2: 取消点赞评审意见 (再次调用)"
echo "========================================="
echo "POST ${API_BASE_URL}/api/reviews/${REVIEW_ID}/like"
echo ""

curl -X POST "${API_BASE_URL}/api/reviews/${REVIEW_ID}/like" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'

echo ""
echo ""

# 测试 3: 点赞评论
echo "========================================="
echo "测试 3: 点赞评论"
echo "========================================="
COMMENT_ID="test-comment-id"
echo "POST ${API_BASE_URL}/api/comments/${COMMENT_ID}/like"
echo ""

curl -X POST "${API_BASE_URL}/api/comments/${COMMENT_ID}/like" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'

echo ""
echo ""

# 测试 4: 取消点赞评论
echo "========================================="
echo "测试 4: 取消点赞评论 (再次调用)"
echo "========================================="
echo "POST ${API_BASE_URL}/api/comments/${COMMENT_ID}/like"
echo ""

curl -X POST "${API_BASE_URL}/api/comments/${COMMENT_ID}/like" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'

echo ""
echo ""

# 测试 5: 未授权访问
echo "========================================="
echo "测试 5: 未授权访问 (无 Token)"
echo "========================================="
echo "POST ${API_BASE_URL}/api/reviews/${REVIEW_ID}/like"
echo ""

curl -X POST "${API_BASE_URL}/api/reviews/${REVIEW_ID}/like" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'

echo ""
echo ""

# 测试 6: 不存在的评审ID
echo "========================================="
echo "测试 6: 不存在的评审ID"
echo "========================================="
FAKE_REVIEW_ID="00000000-0000-0000-0000-000000000000"
echo "POST ${API_BASE_URL}/api/reviews/${FAKE_REVIEW_ID}/like"
echo ""

curl -X POST "${API_BASE_URL}/api/reviews/${FAKE_REVIEW_ID}/like" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'

echo ""
echo ""

echo "========================================="
echo "测试完成"
echo "========================================="
echo ""
echo -e "${GREEN}预期结果:${NC}"
echo "  - 测试 1: 返回 200, likes 增加"
echo "  - 测试 2: 返回 200, likes 减少"
echo "  - 测试 3: 返回 200, likes 增加"
echo "  - 测试 4: 返回 200, likes 减少"
echo "  - 测试 5: 返回 401 (未授权)"
echo "  - 测试 6: 返回 404 (不存在)"
echo ""
