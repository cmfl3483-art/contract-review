#!/bin/bash

# Frontend Infrastructure Static Verification Script
# Task 21: Checkpoint - 验证前端基础设施
#
# This script performs static checks on the frontend infrastructure
# without requiring the servers to be running.

set -e

echo "============================================================================"
echo "Frontend Infrastructure Static Verification"
echo "Task 21: Checkpoint - 验证前端基础设施"
echo "============================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} File exists: $1"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} File missing: $1"
        ((FAILED++))
        return 1
    fi
}

check_content() {
    if grep -q "$2" "$1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Found '$2' in $1"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} Missing '$2' in $1"
        ((FAILED++))
        return 1
    fi
}

check_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# Change to frontend directory
cd "$(dirname "$0")/.."

echo "1. CHECKING AXIOS CONFIGURATION"
echo "--------------------------------"
check_file "src/config/api.ts"
check_content "src/config/api.ts" "API_BASE_URL"
check_content "src/config/api.ts" "API_ENDPOINTS"
echo ""

echo "2. CHECKING ZUSTAND STORES"
echo "--------------------------------"
check_file "src/stores/useUserStore.ts"
check_file "src/stores/useContractListStore.ts"
check_file "src/stores/useSelectedContractStore.ts"
check_content "src/stores/useUserStore.ts" "persist"
check_content "src/stores/useUserStore.ts" "user-storage"
check_content "src/stores/useContractListStore.ts" "contracts"
check_content "src/stores/useContractListStore.ts" "filter"
check_content "src/stores/useSelectedContractStore.ts" "selectedContractId"
echo ""

echo "3. CHECKING REACT QUERY CONFIGURATION"
echo "--------------------------------"
check_file "src/config/queryClient.ts"
check_content "src/config/queryClient.ts" "QueryClient"
check_content "src/config/queryClient.ts" "staleTime"
check_content "src/config/queryClient.ts" "gcTime"
check_content "src/config/queryClient.ts" "queryKeys"
echo ""

echo "4. CHECKING SOCKET.IO CONFIGURATION"
echo "--------------------------------"
check_file "src/config/socket.ts"
check_content "src/config/socket.ts" "socket.io-client"
check_content "src/config/socket.ts" "getSocket"
check_content "src/config/socket.ts" "connectSocket"
check_content "src/config/socket.ts" "onContractUpdated"
check_content "src/config/socket.ts" "onReviewAdded"
check_content "src/config/socket.ts" "onCommentAdded"
check_content "src/config/socket.ts" "reconnection"
echo ""

echo "5. CHECKING DEPENDENCIES"
echo "--------------------------------"
if [ -f "package.json" ]; then
    echo -e "${GREEN}✓${NC} package.json exists"
    ((PASSED++))
    
    # Check for required dependencies
    for dep in "axios" "zustand" "@tanstack/react-query" "socket.io-client"; do
        if grep -q "\"$dep\"" package.json; then
            echo -e "${GREEN}✓${NC} Dependency installed: $dep"
            ((PASSED++))
        else
            echo -e "${RED}✗${NC} Dependency missing: $dep"
            ((FAILED++))
        fi
    done
else
    echo -e "${RED}✗${NC} package.json not found"
    ((FAILED++))
fi
echo ""

echo "6. CHECKING TYPE DEFINITIONS"
echo "--------------------------------"
if [ -d "src/types" ]; then
    echo -e "${GREEN}✓${NC} Types directory exists"
    ((PASSED++))
else
    check_warning "Types directory not found (may be defined inline)"
fi
echo ""

echo "7. CHECKING TEST FILES"
echo "--------------------------------"
check_file "tests/infrastructure.spec.ts"
check_file "tests/verify-infrastructure.ts"
check_file "tests/infrastructure-static-check.sh"
echo ""

echo "8. CHECKING DOCUMENTATION"
echo "--------------------------------"
check_file "TASK_21_INFRASTRUCTURE_VERIFICATION.md"
echo ""

echo "============================================================================"
echo "VERIFICATION SUMMARY"
echo "============================================================================"
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${RED}Failed:${NC} $FAILED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start the backend server: cd ../backend && python main.py"
    echo "2. Start the frontend server: npm run dev"
    echo "3. Run Playwright tests: npm run test tests/infrastructure.spec.ts"
    echo "4. Open browser and run manual verification"
    exit 0
else
    echo -e "${RED}✗ SOME CHECKS FAILED${NC}"
    echo ""
    echo "Please fix the failed checks before proceeding."
    exit 1
fi
