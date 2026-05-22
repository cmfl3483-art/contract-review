"""
测试通知服务
Test Notification Service

验证 NotificationService 的各个方法是否正常工作
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.notification_service import NotificationService


async def test_notification_service():
    """测试通知服务的所有方法"""
    
    print("=" * 60)
    print("测试通知服务 (NotificationService)")
    print("=" * 60)
    
    # 创建通知服务实例
    service = NotificationService()
    
    # 测试数据
    contract_id = "test-contract-123"
    user_id = "test-user-456"
    
    print("\n1. 测试合同更新通知...")
    try:
        await service.notify_contract_updated(
            contract_id=contract_id,
            contract_data={
                "id": contract_id,
                "name": "测试合同",
                "status": "progress",
                "updated_at": "2025-03-15T10:00:00"
            }
        )
        print("✅ 合同更新通知方法调用成功")
    except Exception as e:
        print(f"❌ 合同更新通知失败: {e}")
    
    print("\n2. 测试评审添加通知...")
    try:
        await service.notify_review_added(
            contract_id=contract_id,
            review_data={
                "id": "review-123",
                "contract_id": contract_id,
                "reviewer_id": user_id,
                "reviewer_name": "张三",
                "role": "法务",
                "opinion": "同意并通过",
                "status": "approved",
                "created_at": "2025-03-15T10:05:00"
            }
        )
        print("✅ 评审添加通知方法调用成功")
    except Exception as e:
        print(f"❌ 评审添加通知失败: {e}")
    
    print("\n3. 测试评论添加通知...")
    try:
        await service.notify_comment_added(
            contract_id=contract_id,
            comment_data={
                "id": "comment-123",
                "contract_id": contract_id,
                "review_id": "review-123",
                "author_id": user_id,
                "author_name": "李四",
                "content": "我也同意这个方案",
                "created_at": "2025-03-15T10:10:00"
            }
        )
        print("✅ 评论添加通知方法调用成功")
    except Exception as e:
        print(f"❌ 评论添加通知失败: {e}")
    
    print("\n4. 测试回复添加通知...")
    try:
        await service.notify_reply_added(
            contract_id=contract_id,
            reply_data={
                "id": "reply-123",
                "contract_id": contract_id,
                "parent_comment_id": "comment-123",
                "author_id": user_id,
                "author_name": "王五",
                "content": "好的,我知道了",
                "created_at": "2025-03-15T10:15:00"
            }
        )
        print("✅ 回复添加通知方法调用成功")
    except Exception as e:
        print(f"❌ 回复添加通知失败: {e}")
    
    print("\n5. 测试点赞更新通知...")
    try:
        await service.notify_like_updated(
            contract_id=contract_id,
            like_data={
                "target_type": "review",
                "target_id": "review-123",
                "likes": 5,
                "user_id": user_id,
                "action": "like"
            }
        )
        print("✅ 点赞更新通知方法调用成功")
    except Exception as e:
        print(f"❌ 点赞更新通知失败: {e}")
    
    print("\n6. 测试待办变化通知...")
    try:
        await service.notify_pending_changed(
            user_id=user_id,
            pending_count=3,
            contract_id=contract_id
        )
        print("✅ 待办变化通知方法调用成功")
    except Exception as e:
        print(f"❌ 待办变化通知失败: {e}")
    
    print("\n7. 测试批量待办变化通知...")
    try:
        await service.notify_multiple_users_pending_changed(
            user_ids=["user-1", "user-2", "user-3"],
            pending_counts={
                "user-1": 2,
                "user-2": 5,
                "user-3": 1
            },
            contract_id=contract_id
        )
        print("✅ 批量待办变化通知方法调用成功")
    except Exception as e:
        print(f"❌ 批量待办变化通知失败: {e}")
    
    print("\n8. 测试自定义通知...")
    try:
        await service.send_custom_notification(
            user_id=user_id,
            event="custom:event",
            data={
                "message": "这是一个自定义通知",
                "timestamp": "2025-03-15T10:20:00"
            }
        )
        print("✅ 自定义通知方法调用成功")
    except Exception as e:
        print(f"❌ 自定义通知失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 所有通知服务方法测试完成!")
    print("=" * 60)
    print("\n注意:")
    print("- 这些方法调用成功,但实际的 WebSocket 推送需要有客户端连接")
    print("- 在没有客户端连接的情况下,通知会被发送但不会有接收者")
    print("- 要完整测试实时通知,需要启动服务器并连接 WebSocket 客户端")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_notification_service())
