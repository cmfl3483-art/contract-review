"""
测试 Socket.IO 服务器配置
Test Socket.IO Server Configuration
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.socketio_server import sio, socket_app, user_sessions


async def test_socketio_config():
    """测试 Socket.IO 配置"""
    
    print("=" * 60)
    print("测试 Socket.IO 服务器配置")
    print("=" * 60)
    
    # 1. 检查 Socket.IO 服务器实例
    print("\n1. 检查 Socket.IO 服务器实例")
    print(f"   ✓ Socket.IO 服务器类型: {type(sio)}")
    print(f"   ✓ 异步模式: {sio.async_mode}")
    print(f"   ✓ Socket.IO 服务器已创建")
    
    # 2. 检查 ASGI 应用
    print("\n2. 检查 ASGI 应用")
    print(f"   ✓ ASGI 应用类型: {type(socket_app)}")
    
    # 3. 检查事件处理器
    print("\n3. 检查事件处理器")
    handlers = sio.handlers.get('/', {})
    print(f"   ✓ 已注册的事件处理器:")
    for event_name in handlers.keys():
        print(f"      - {event_name}")
    
    # 4. 检查用户会话存储
    print("\n4. 检查用户会话存储")
    print(f"   ✓ 用户会话字典类型: {type(user_sessions)}")
    print(f"   ✓ 当前会话数量: {len(user_sessions)}")
    
    # 5. 测试导入通知服务
    print("\n5. 测试导入通知服务")
    try:
        from app.services.notification_service import notification_service
        print(f"   ✓ 通知服务导入成功: {type(notification_service)}")
        
        # 检查通知服务方法
        methods = [
            'notify_contract_updated',
            'notify_review_added',
            'notify_comment_added',
            'notify_reply_added',
            'notify_like_updated',
            'notify_pending_changed',
            'notify_user'
        ]
        print(f"   ✓ 通知服务方法:")
        for method in methods:
            if hasattr(notification_service, method):
                print(f"      - {method}")
            else:
                print(f"      ✗ 缺少方法: {method}")
    except Exception as e:
        print(f"   ✗ 通知服务导入失败: {e}")
    
    # 6. 测试主应用集成
    print("\n6. 测试主应用集成")
    try:
        from app.main import app
        print(f"   ✓ FastAPI 应用导入成功")
        
        # 检查路由
        routes = [route.path for route in app.routes]
        if '/socket.io' in routes:
            print(f"   ✓ Socket.IO 已挂载到 /socket.io")
        else:
            print(f"   ✗ Socket.IO 未挂载")
            print(f"   已注册的路由: {routes}")
    except Exception as e:
        print(f"   ✗ 主应用导入失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_socketio_config())
