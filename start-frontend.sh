#!/bin/bash

# 合同预审看板系统 - 前端启动脚本

echo "🚀 启动合同预审看板系统前端..."
echo ""

# 进入前端目录
cd frontend

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
fi

# 启动开发服务器
echo ""
echo "🎯 启动Vite开发服务器..."
echo "📍 前端地址: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动vite
npm run dev
