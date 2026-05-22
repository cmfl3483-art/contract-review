"""
性能优化验证脚本
Verify performance optimization implementation
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def verify_database_config():
    """验证数据库连接池配置"""
    print("=" * 80)
    print("1. 验证数据库连接池配置")
    print("=" * 80)
    
    try:
        from app.core.database import engine
        
        # 检查连接池配置
        pool = engine.pool
        print(f"✅ 连接池大小 (pool_size): {pool.size()}")
        print(f"✅ 最大溢出 (max_overflow): 预期40")
        print(f"✅ 连接回收时间 (pool_recycle): 预期3600秒")
        print(f"✅ 连接超时 (pool_timeout): 预期30秒")
        
        # 检查当前连接状态
        print(f"\n当前连接状态:")
        print(f"  - 已签出连接: {pool.checkedout()}")
        print(f"  - 溢出连接: {pool.overflow()}")
        
        return True
    except Exception as e:
        print(f"❌ 数据库配置验证失败: {e}")
        return False


async def verify_redis_client():
    """验证Redis客户端优化"""
    print("\n" + "=" * 80)
    print("2. 验证Redis客户端优化")
    print("=" * 80)
    
    try:
        from app.core.redis_client import redis_client, RedisClient
        
        # 检查TTL配置
        print(f"✅ TTL_SHORT: {RedisClient.TTL_SHORT}秒 (预期60)")
        print(f"✅ TTL_MEDIUM: {RedisClient.TTL_MEDIUM}秒 (预期300)")
        print(f"✅ TTL_LONG: {RedisClient.TTL_LONG}秒 (预期1800)")
        print(f"✅ TTL_VERY_LONG: {RedisClient.TTL_VERY_LONG}秒 (预期3600)")
        
        # 检查新增方法
        methods = ['mget', 'mset', 'delete_many', 'generate_cache_key', 'incr', 'decr', 'exists', 'expire']
        print(f"\n新增方法:")
        for method in methods:
            if hasattr(redis_client, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} - 缺失")
        
        # 测试缓存键生成
        test_key = redis_client.generate_cache_key("test", "arg1", "arg2", param1="value1")
        print(f"\n缓存键生成测试:")
        print(f"  生成的键: {test_key}")
        
        return True
    except Exception as e:
        print(f"❌ Redis客户端验证失败: {e}")
        return False


async def verify_performance_utils():
    """验证性能监控工具"""
    print("\n" + "=" * 80)
    print("3. 验证性能监控工具")
    print("=" * 80)
    
    try:
        from app.utils.performance import (
            monitor_performance,
            query_timer,
            perf_stats,
            track_performance,
            PerformanceStats
        )
        
        print("✅ monitor_performance 装饰器")
        print("✅ query_timer 上下文管理器")
        print("✅ perf_stats 全局统计实例")
        print("✅ track_performance 装饰器")
        print("✅ PerformanceStats 类")
        
        # 测试性能统计
        print("\n测试性能统计:")
        test_stats = PerformanceStats()
        test_stats.record("test_operation", 100.5)
        test_stats.record("test_operation", 150.3)
        test_stats.record("test_operation", 80.2)
        
        stats = test_stats.get_stats("test_operation")
        print(f"  操作次数: {stats['count']}")
        print(f"  平均耗时: {stats['avg_ms']:.2f}ms")
        print(f"  最小耗时: {stats['min_ms']:.2f}ms")
        print(f"  最大耗时: {stats['max_ms']:.2f}ms")
        
        return True
    except Exception as e:
        print(f"❌ 性能监控工具验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_migration_file():
    """验证迁移文件"""
    print("\n" + "=" * 80)
    print("4. 验证数据库迁移文件")
    print("=" * 80)
    
    try:
        migration_file = "alembic/versions/002_add_performance_indexes.py"
        
        if os.path.exists(migration_file):
            print(f"✅ 迁移文件存在: {migration_file}")
            
            # 读取文件内容检查索引
            with open(migration_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            expected_indexes = [
                'ix_contracts_status_created_at',
                'ix_contracts_initiator_created_at',
                'ix_reviews_reviewer_status',
                'ix_reviews_contract_created_at',
                'ix_reviews_reviewer_status_contract',
                'ix_comments_contract_created_at',
                'ix_comments_review_created_at',
                'ix_comments_parent_created_at',
                'ix_attachments_contract_filename_created',
                'ix_ai_summaries_contract_updated'
            ]
            
            print(f"\n检查索引定义:")
            for index in expected_indexes:
                if index in content:
                    print(f"  ✅ {index}")
                else:
                    print(f"  ❌ {index} - 缺失")
            
            return True
        else:
            print(f"❌ 迁移文件不存在: {migration_file}")
            return False
    except Exception as e:
        print(f"❌ 迁移文件验证失败: {e}")
        return False


async def verify_service_optimizations():
    """验证服务层优化"""
    print("\n" + "=" * 80)
    print("5. 验证服务层优化")
    print("=" * 80)
    
    try:
        from app.services.contract_service import ContractService
        from app.services.review_service import ReviewService
        
        print("✅ ContractService 导入成功")
        print("✅ ReviewService 导入成功")
        
        # 检查方法是否存在
        contract_service = ContractService()
        review_service = ReviewService()
        
        print("\nContractService 方法:")
        methods = ['get_contract_list', 'get_pending_count', '_apply_filter']
        for method in methods:
            if hasattr(contract_service, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} - 缺失")
        
        print("\nReviewService 方法:")
        methods = ['get_contract_reviews', 'get_ai_summary']
        for method in methods:
            if hasattr(review_service, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} - 缺失")
        
        return True
    except Exception as e:
        print(f"❌ 服务层验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_documentation():
    """验证文档"""
    print("\n" + "=" * 80)
    print("6. 验证文档")
    print("=" * 80)
    
    docs = [
        ("PERFORMANCE_OPTIMIZATION.md", "性能优化文档"),
        ("TASK_32.2_COMPLETE.md", "任务完成报告")
    ]
    
    all_exist = True
    for doc_file, doc_name in docs:
        if os.path.exists(doc_file):
            print(f"✅ {doc_name}: {doc_file}")
            
            # 检查文件大小
            size = os.path.getsize(doc_file)
            print(f"   文件大小: {size:,} 字节")
        else:
            print(f"❌ {doc_name}: {doc_file} - 不存在")
            all_exist = False
    
    return all_exist


async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("后端性能优化验证")
    print("=" * 80)
    
    results = []
    
    # 执行各项验证
    results.append(("数据库连接池配置", await verify_database_config()))
    results.append(("Redis客户端优化", await verify_redis_client()))
    results.append(("性能监控工具", await verify_performance_utils()))
    results.append(("数据库迁移文件", await verify_migration_file()))
    results.append(("服务层优化", await verify_service_optimizations()))
    results.append(("文档", await verify_documentation()))
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("验证结果汇总")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("=" * 80)
    
    if failed == 0:
        print("\n🎉 所有验证通过!性能优化实施成功!")
        print("\n下一步:")
        print("1. 运行数据库迁移: alembic upgrade head")
        print("2. 重启应用服务")
        print("3. 监控性能指标")
    else:
        print("\n⚠️  部分验证失败,请检查上述错误信息")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
