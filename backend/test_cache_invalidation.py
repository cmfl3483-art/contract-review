"""
测试缓存失效策略
Test Cache Invalidation Strategy
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.redis_client import redis_client
from app.utils.cache_invalidation import cache_invalidation


async def test_cache_invalidation():
    """测试缓存失效策略"""
    
    print("=" * 60)
    print("测试缓存失效策略")
    print("=" * 60)
    
    try:
        # 连接Redis
        await redis_client.connect()
        print("✓ Redis连接成功")
        
        # 测试1: 模拟合同创建的缓存失效
        print("\n测试1: 合同创建时的缓存失效")
        print("-" * 60)
        
        # 先设置一些测试缓存
        await redis_client.set("contract:list:user1:all:1:20", {"test": "data"})
        await redis_client.set("contract:pending:reviewer1", "5")
        await redis_client.set("contract:pending:reviewer2", "3")
        
        print("✓ 设置测试缓存")
        
        # 执行缓存失效
        await cache_invalidation.invalidate_contract_created(
            contract_id="contract123",
            initiator_id="user1",
            reviewer_ids=["reviewer1", "reviewer2"]
        )
        
        # 验证缓存已清除
        list_cache = await redis_client.get("contract:list:user1:all:1:20")
        pending1 = await redis_client.get("contract:pending:reviewer1")
        pending2 = await redis_client.get("contract:pending:reviewer2")
        
        assert list_cache is None, "合同列表缓存应该被清除"
        assert pending1 is None, "评审人1的待办缓存应该被清除"
        assert pending2 is None, "评审人2的待办缓存应该被清除"
        
        print("✓ 合同创建缓存失效测试通过")
        
        # 测试2: 模拟评审通过的缓存失效
        print("\n测试2: 评审通过时的缓存失效")
        print("-" * 60)
        
        # 设置测试缓存
        await redis_client.set("contract:list:user1:all:1:20", {"test": "data"})
        await redis_client.set("reviews:contract123", [{"test": "review"}])
        await redis_client.set("contract:pending:reviewer1", "5")
        await redis_client.set("ai:summary:contract123", {"test": "summary"})
        
        print("✓ 设置测试缓存")
        
        # 执行缓存失效
        await cache_invalidation.invalidate_review_approved(
            contract_id="contract123",
            reviewer_id="reviewer1",
            all_reviewer_ids=["reviewer1", "reviewer2", "reviewer3"]
        )
        
        # 验证缓存已清除
        list_cache = await redis_client.get("contract:list:user1:all:1:20")
        reviews_cache = await redis_client.get("reviews:contract123")
        pending_cache = await redis_client.get("contract:pending:reviewer1")
        ai_cache = await redis_client.get("ai:summary:contract123")
        
        assert list_cache is None, "合同列表缓存应该被清除"
        assert reviews_cache is None, "评审记录缓存应该被清除"
        assert pending_cache is None, "待办缓存应该被清除"
        assert ai_cache is None, "AI总结缓存应该被清除"
        
        print("✓ 评审通过缓存失效测试通过")
        
        # 测试3: 模拟评论添加的缓存失效
        print("\n测试3: 评论添加时的缓存失效")
        print("-" * 60)
        
        # 设置测试缓存
        await redis_client.set("reviews:contract123", [{"test": "review"}])
        await redis_client.set("ai:summary:contract123", {"test": "summary"})
        
        print("✓ 设置测试缓存")
        
        # 执行缓存失效
        await cache_invalidation.invalidate_comment_added("contract123")
        
        # 验证缓存已清除
        reviews_cache = await redis_client.get("reviews:contract123")
        ai_cache = await redis_client.get("ai:summary:contract123")
        
        assert reviews_cache is None, "评审记录缓存应该被清除"
        assert ai_cache is None, "AI总结缓存应该被清除"
        
        print("✓ 评论添加缓存失效测试通过")
        
        # 测试4: 模拟点赞更新的缓存失效
        print("\n测试4: 点赞更新时的缓存失效")
        print("-" * 60)
        
        # 设置测试缓存
        await redis_client.set("reviews:contract123", [{"test": "review"}])
        
        print("✓ 设置测试缓存")
        
        # 执行缓存失效
        await cache_invalidation.invalidate_like_updated("contract123")
        
        # 验证缓存已清除
        reviews_cache = await redis_client.get("reviews:contract123")
        
        assert reviews_cache is None, "评审记录缓存应该被清除"
        
        print("✓ 点赞更新缓存失效测试通过")
        
        # 测试5: 模拟附件上传的缓存失效
        print("\n测试5: 附件上传时的缓存失效")
        print("-" * 60)
        
        # 设置测试缓存
        await redis_client.set("contract:detail:contract123", {"test": "detail"})
        
        print("✓ 设置测试缓存")
        
        # 执行缓存失效
        await cache_invalidation.invalidate_attachment_uploaded("contract123")
        
        # 验证缓存已清除
        detail_cache = await redis_client.get("contract:detail:contract123")
        
        assert detail_cache is None, "合同详情缓存应该被清除"
        
        print("✓ 附件上传缓存失效测试通过")
        
        # 测试6: 获取缓存统计信息
        print("\n测试6: 获取缓存统计信息")
        print("-" * 60)
        
        # 设置一些测试缓存
        await redis_client.set("contract:list:user1:all:1:20", {"test": "data"})
        await redis_client.set("contract:list:user2:进行中:1:20", {"test": "data"})
        await redis_client.set("contract:detail:contract1", {"test": "detail"})
        await redis_client.set("contract:pending:user1", "5")
        await redis_client.set("reviews:contract1", [{"test": "review"}])
        await redis_client.set("ai:summary:contract1", {"test": "summary"})
        
        print("✓ 设置测试缓存")
        
        # 获取统计信息
        stats = await cache_invalidation.get_cache_stats()
        
        print(f"✓ 缓存统计信息:")
        for key, count in stats.items():
            print(f"  - {key}: {count} 个缓存键")
        
        # 测试7: 清除所有缓存
        print("\n测试7: 清除所有缓存")
        print("-" * 60)
        
        await cache_invalidation.clear_all_caches()
        
        # 验证所有缓存已清除
        stats_after = await cache_invalidation.get_cache_stats()
        
        print(f"✓ 清除后的缓存统计:")
        for key, count in stats_after.items():
            print(f"  - {key}: {count} 个缓存键")
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试数据
        await cache_invalidation.clear_all_caches()
        await redis_client.disconnect()
        print("\n✓ Redis连接已关闭")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_cache_invalidation())
    sys.exit(0 if success else 1)
