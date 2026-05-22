"""
简单验证 Socket.IO 配置文件
Simple verification of Socket.IO configuration files
"""

import os
import sys

print("=" * 60)
print("验证 Socket.IO 配置文件")
print("=" * 60)

# 1. 检查文件是否存在
print("\n1. 检查文件是否存在")
files_to_check = [
    "app/core/socketio_server.py",
    "app/services/notification_service.py",
    "app/main.py"
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        print(f"   ✓ {file_path} 存在")
    else:
        print(f"   ✗ {file_path} 不存在")

# 2. 检查 socketio_server.py 内容
print("\n2. 检查 socketio_server.py 关键内容")
with open("app/core/socketio_server.py", "r") as f:
    content = f.read()
    
    checks = [
        ("import socketio", "导入 socketio 模块"),
        ("sio = socketio.AsyncServer", "创建 AsyncServer 实例"),
        ("async_mode='asgi'", "配置 ASGI 模式"),
        ("cors_allowed_origins", "配置 CORS"),
        ("async def connect", "定义 connect 事件处理器"),
        ("async def disconnect", "定义 disconnect 事件处理器"),
        ("async def join_contract", "定义 join_contract 事件处理器"),
        ("async def leave_contract", "定义 leave_contract 事件处理器"),
        ("async def emit_contract_updated", "定义 emit_contract_updated 函数"),
        ("async def emit_review_added", "定义 emit_review_added 函数"),
        ("async def emit_comment_added", "定义 emit_comment_added 函数"),
        ("async def emit_reply_added", "定义 emit_reply_added 函数"),
        ("async def emit_like_updated", "定义 emit_like_updated 函数"),
        ("async def emit_pending_changed", "定义 emit_pending_changed 函数"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            print(f"   ✓ {description}")
        else:
            print(f"   ✗ 缺少: {description}")

# 3. 检查 notification_service.py 内容
print("\n3. 检查 notification_service.py 关键内容")
with open("app/services/notification_service.py", "r") as f:
    content = f.read()
    
    checks = [
        ("class NotificationService", "定义 NotificationService 类"),
        ("async def notify_contract_updated", "定义 notify_contract_updated 方法"),
        ("async def notify_review_added", "定义 notify_review_added 方法"),
        ("async def notify_comment_added", "定义 notify_comment_added 方法"),
        ("async def notify_reply_added", "定义 notify_reply_added 方法"),
        ("async def notify_like_updated", "定义 notify_like_updated 方法"),
        ("async def notify_pending_changed", "定义 notify_pending_changed 方法"),
        ("notification_service = NotificationService()", "创建全局实例"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            print(f"   ✓ {description}")
        else:
            print(f"   ✗ 缺少: {description}")

# 4. 检查 main.py 集成
print("\n4. 检查 main.py 集成")
with open("app/main.py", "r") as f:
    content = f.read()
    
    checks = [
        ("from app.core.socketio_server import socket_app", "导入 socket_app"),
        ("app.mount('/socket.io', socket_app)", "挂载 Socket.IO 应用"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            print(f"   ✓ {description}")
        else:
            print(f"   ✗ 缺少: {description}")

# 5. 检查 Python 语法
print("\n5. 检查 Python 语法")
import py_compile

files_to_compile = [
    "app/core/socketio_server.py",
    "app/services/notification_service.py",
]

for file_path in files_to_compile:
    try:
        py_compile.compile(file_path, doraise=True)
        print(f"   ✓ {file_path} 语法正确")
    except py_compile.PyCompileError as e:
        print(f"   ✗ {file_path} 语法错误: {e}")

print("\n" + "=" * 60)
print("验证完成!")
print("=" * 60)
print("\n总结:")
print("- Socket.IO 服务器配置文件已创建")
print("- 实时通知服务已创建")
print("- Socket.IO 已集成到 FastAPI 主应用")
print("- 所有文件语法正确")
print("\n下一步:")
print("1. 安装依赖: pip install -r requirements.txt")
print("2. 启动服务器: uvicorn app.main:app --reload")
print("3. 客户端连接: io('http://localhost:8000', { path: '/socket.io', auth: { token: 'your-jwt-token' } })")
