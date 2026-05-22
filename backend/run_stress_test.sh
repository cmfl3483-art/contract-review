#!/bin/bash

# 压力测试快速启动脚本
# Quick Start Script for Stress Testing

set -e

echo "=========================================="
echo "合同预审看板系统 - 压力测试"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查依赖
check_dependencies() {
    echo -e "\n${YELLOW}检查依赖...${NC}"
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python 3 已安装${NC}"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}创建虚拟环境...${NC}"
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    echo -e "${YELLOW}安装依赖...${NC}"
    pip install -q -r requirements.txt
    pip install -q -r requirements-stress-test.txt
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
}

# 检查服务状态
check_services() {
    echo -e "\n${YELLOW}检查服务状态...${NC}"
    
    # 检查后端服务
    if ! curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${RED}❌ 后端服务未运行${NC}"
        echo -e "${YELLOW}请先启动后端服务:${NC}"
        echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000"
        exit 1
    fi
    echo -e "${GREEN}✅ 后端服务正常${NC}"
    
    # 检查数据库
    if ! docker ps | grep -q postgres; then
        echo -e "${RED}❌ PostgreSQL 未运行${NC}"
        echo -e "${YELLOW}请先启动数据库:${NC}"
        echo "  docker-compose up -d postgres"
        exit 1
    fi
    echo -e "${GREEN}✅ PostgreSQL 正常${NC}"
    
    # 检查 Redis
    if ! docker ps | grep -q redis; then
        echo -e "${RED}❌ Redis 未运行${NC}"
        echo -e "${YELLOW}请先启动 Redis:${NC}"
        echo "  docker-compose up -d redis"
        exit 1
    fi
    echo -e "${GREEN}✅ Redis 正常${NC}"
}

# 生成测试数据
generate_test_data() {
    echo -e "\n${YELLOW}是否需要生成测试数据? (y/n)${NC}"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}生成测试数据...${NC}"
        python scripts/create_stress_test_data.py --action generate \
            --users 50 \
            --contracts 1000 \
            --reviews 5 \
            --comments 2
        echo -e "${GREEN}✅ 测试数据生成完成${NC}"
    fi
}

# 运行 Locust 压力测试
run_locust_test() {
    echo -e "\n${YELLOW}启动 Locust 压力测试...${NC}"
    echo -e "${GREEN}Web UI 地址: http://localhost:8089${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止测试${NC}\n"
    
    locust -f tests/stress_test.py --host=http://localhost:8000
}

# 运行简单压力测试
run_simple_test() {
    echo -e "\n${YELLOW}运行简单压力测试...${NC}"
    python tests/simple_stress_test.py
}

# 清理测试数据
cleanup_test_data() {
    echo -e "\n${YELLOW}清理测试数据...${NC}"
    python scripts/create_stress_test_data.py --action cleanup
    echo -e "${GREEN}✅ 测试数据清理完成${NC}"
}

# 主菜单
show_menu() {
    echo -e "\n${YELLOW}请选择测试类型:${NC}"
    echo "1) Locust 压力测试 (Web UI)"
    echo "2) 简单压力测试 (命令行)"
    echo "3) 生成测试数据"
    echo "4) 清理测试数据"
    echo "5) 退出"
    echo -n "请输入选项 (1-5): "
}

# 主函数
main() {
    # 检查依赖
    check_dependencies
    
    # 检查服务
    check_services
    
    # 显示菜单
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1)
                run_locust_test
                ;;
            2)
                run_simple_test
                ;;
            3)
                generate_test_data
                ;;
            4)
                cleanup_test_data
                ;;
            5)
                echo -e "\n${GREEN}再见!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}无效选项,请重新选择${NC}"
                ;;
        esac
    done
}

# 运行主函数
main
