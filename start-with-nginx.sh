#!/bin/bash

# 合同预审看板系统 - 使用 Nginx 启动脚本
# Contract Pre-Review System - Start with Nginx

set -e

echo "🚀 启动合同预审看板系统 (使用 Nginx 反向代理)..."
echo ""

# 检查 Docker 服务是否运行
echo "📦 检查 Docker 服务..."
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker 未运行,请先启动 Docker"
    exit 1
fi
echo "✅ Docker 运行正常"
echo ""

# 选择启动模式
echo "请选择启动模式:"
echo "1) 开发模式 - 使用 docker-compose.dev.yml (包含 Nginx + 本地前后端)"
echo "2) 生产模式 - 使用 docker-compose.yml (完整 Docker 部署)"
echo "3) 仅启动基础服务 + Nginx (手动运行前后端)"
echo ""
read -p "请输入选择 (1-3): " mode

case $mode in
    1)
        echo ""
        echo "🔧 启动开发模式..."
        echo ""
        
        # 启动 Docker 服务
        echo "🐳 启动 Docker Compose 服务..."
        docker-compose -f docker-compose.dev.yml up -d
        
        echo ""
        echo "⏳ 等待服务启动..."
        sleep 5
        
        echo ""
        echo "📊 服务状态:"
        docker-compose -f docker-compose.dev.yml ps
        
        echo ""
        echo "✅ 开发环境启动完成!"
        echo ""
        echo "📍 访问地址:"
        echo "   - 应用入口 (Nginx): http://localhost"
        echo "   - 前端 (Vite): http://localhost:5173"
        echo "   - 后端 API: http://localhost:8000"
        echo "   - API 文档: http://localhost:8000/api/docs"
        echo "   - MinIO 控制台: http://localhost:9001"
        echo ""
        echo "💡 提示:"
        echo "   - 前后端代码修改会自动热重载"
        echo "   - 查看日志: docker-compose -f docker-compose.dev.yml logs -f"
        echo "   - 停止服务: docker-compose -f docker-compose.dev.yml down"
        ;;
        
    2)
        echo ""
        echo "🚀 启动生产模式..."
        echo ""
        
        # 检查前端是否已构建
        if [ ! -d "frontend/dist" ]; then
            echo "⚠️  前端未构建,正在构建..."
            cd frontend
            npm install
            npm run build
            cd ..
            echo "✅ 前端构建完成"
        fi
        
        # 启动 Docker 服务
        echo ""
        echo "🐳 启动 Docker Compose 服务..."
        docker-compose up -d
        
        echo ""
        echo "⏳ 等待服务启动..."
        sleep 10
        
        echo ""
        echo "📊 服务状态:"
        docker-compose ps
        
        echo ""
        echo "✅ 生产环境启动完成!"
        echo ""
        echo "📍 访问地址:"
        echo "   - 应用入口: http://localhost"
        echo "   - API 文档: http://localhost:8000/api/docs"
        echo "   - MinIO 控制台: http://localhost:9001"
        echo ""
        echo "💡 提示:"
        echo "   - 查看日志: docker-compose logs -f"
        echo "   - 停止服务: docker-compose down"
        ;;
        
    3)
        echo ""
        echo "🔧 启动基础服务 + Nginx..."
        echo ""
        
        # 启动基础服务
        echo "🐳 启动基础服务 (PostgreSQL, Redis, MinIO)..."
        docker-compose up -d postgres redis minio
        
        echo ""
        echo "⏳ 等待基础服务启动..."
        sleep 5
        
        # 启动 Nginx
        echo ""
        echo "🌐 启动 Nginx..."
        docker-compose -f docker-compose.dev.yml up -d nginx
        
        echo ""
        echo "📊 服务状态:"
        docker-compose ps
        
        echo ""
        echo "✅ 基础服务和 Nginx 启动完成!"
        echo ""
        echo "⚠️  请手动启动前后端服务:"
        echo ""
        echo "   # 启动后端 (新终端)"
        echo "   ./start-backend.sh"
        echo ""
        echo "   # 启动前端 (新终端)"
        echo "   ./start-frontend.sh"
        echo ""
        echo "📍 启动后访问地址:"
        echo "   - 应用入口 (Nginx): http://localhost"
        echo "   - 前端 (Vite): http://localhost:5173"
        echo "   - 后端 API: http://localhost:8000"
        echo ""
        ;;
        
    *)
        echo "❌ 无效的选择"
        exit 1
        ;;
esac

echo ""
echo "🎉 启动完成!"
echo ""
echo "按 Ctrl+C 停止查看日志"
echo ""

# 显示日志
if [ "$mode" = "1" ]; then
    docker-compose -f docker-compose.dev.yml logs -f
elif [ "$mode" = "2" ]; then
    docker-compose logs -f
else
    echo "查看 Nginx 日志: docker logs -f contract_review_nginx"
fi
