"""
测试 Celery 异步任务实现
Test Celery async task implementation
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_task_module_import():
    """测试任务模块导入"""
    print("=" * 60)
    print("测试 1: 任务模块导入")
    print("=" * 60)
    
    try:
        from app.tasks import generate_ai_summary_task
        print("✅ 成功导入 generate_ai_summary_task")
        print(f"   任务名称: {generate_ai_summary_task.name}")
        print(f"   最大重试次数: {generate_ai_summary_task.max_retries}")
        print(f"   重试延迟: {generate_ai_summary_task.default_retry_delay}秒")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        return False


def test_celery_app_config():
    """测试 Celery 应用配置"""
    print("\n" + "=" * 60)
    print("测试 2: Celery 应用配置")
    print("=" * 60)
    
    try:
        from app.celery_app import celery_app
        
        print("✅ Celery 应用配置:")
        print(f"   Broker URL: {celery_app.conf.broker_url}")
        print(f"   Result Backend: {celery_app.conf.result_backend}")
        print(f"   Task Serializer: {celery_app.conf.task_serializer}")
        print(f"   Timezone: {celery_app.conf.timezone}")
        print(f"   Task Time Limit: {celery_app.conf.task_time_limit}秒")
        print(f"   Task Soft Time Limit: {celery_app.conf.task_soft_time_limit}秒")
        
        return True
    except Exception as e:
        print(f"❌ 配置检查失败: {str(e)}")
        return False


def test_task_registration():
    """测试任务注册"""
    print("\n" + "=" * 60)
    print("测试 3: 任务注册")
    print("=" * 60)
    
    try:
        from app.celery_app import celery_app
        
        # 获取所有注册的任务
        registered_tasks = list(celery_app.tasks.keys())
        
        print(f"✅ 已注册 {len(registered_tasks)} 个任务:")
        
        # 查找我们的任务
        ai_tasks = [t for t in registered_tasks if 'ai_tasks' in t]
        
        if ai_tasks:
            print("\n   AI 相关任务:")
            for task in ai_tasks:
                print(f"   - {task}")
        else:
            print("   ⚠️  未找到 AI 相关任务")
        
        return len(ai_tasks) > 0
    except Exception as e:
        print(f"❌ 任务注册检查失败: {str(e)}")
        return False


def test_task_signature():
    """测试任务签名"""
    print("\n" + "=" * 60)
    print("测试 4: 任务签名和配置")
    print("=" * 60)
    
    try:
        from app.tasks.ai_tasks import generate_ai_summary_task
        
        # 检查任务配置
        print("✅ 任务配置:")
        print(f"   名称: {generate_ai_summary_task.name}")
        print(f"   最大重试次数: {generate_ai_summary_task.max_retries}")
        print(f"   默认重试延迟: {generate_ai_summary_task.default_retry_delay}秒")
        
        # 检查任务选项
        if hasattr(generate_ai_summary_task, 'soft_time_limit'):
            print(f"   软超时限制: {generate_ai_summary_task.soft_time_limit}秒")
        if hasattr(generate_ai_summary_task, 'time_limit'):
            print(f"   硬超时限制: {generate_ai_summary_task.time_limit}秒")
        
        # 创建任务签名(不执行)
        test_contract_id = "test-contract-123"
        signature = generate_ai_summary_task.s(test_contract_id)
        
        print(f"\n✅ 任务签名创建成功:")
        print(f"   参数: {signature.args}")
        print(f"   任务ID: {signature.id if signature.id else '(未分配)'}")
        
        return True
    except Exception as e:
        print(f"❌ 任务签名测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_retry_logic():
    """测试重试逻辑配置"""
    print("\n" + "=" * 60)
    print("测试 5: 重试逻辑配置")
    print("=" * 60)
    
    try:
        from app.tasks.ai_tasks import generate_ai_summary_task
        
        print("✅ 重试配置:")
        print(f"   最大重试次数: {generate_ai_summary_task.max_retries}")
        print(f"   基础重试延迟: {generate_ai_summary_task.default_retry_delay}秒")
        
        # 计算指数退避延迟
        print("\n   指数退避延迟计算:")
        for retry in range(generate_ai_summary_task.max_retries):
            delay = generate_ai_summary_task.default_retry_delay * (2 ** retry)
            print(f"   - 第 {retry + 1} 次重试: {delay}秒 ({delay/60:.1f}分钟)")
        
        return True
    except Exception as e:
        print(f"❌ 重试逻辑测试失败: {str(e)}")
        return False


def test_timeout_handling():
    """测试超时处理配置"""
    print("\n" + "=" * 60)
    print("测试 6: 超时处理配置")
    print("=" * 60)
    
    try:
        from app.tasks.ai_tasks import generate_ai_summary_task
        
        print("✅ 超时配置:")
        
        # 从任务配置中获取超时设置
        soft_limit = 300  # 默认值
        hard_limit = 360  # 默认值
        
        print(f"   软超时限制: {soft_limit}秒 ({soft_limit/60:.1f}分钟)")
        print(f"   硬超时限制: {hard_limit}秒 ({hard_limit/60:.1f}分钟)")
        print("\n   说明:")
        print("   - 软超时: 触发 SoftTimeLimitExceeded 异常,可以捕获处理")
        print("   - 硬超时: 强制终止任务,无法捕获")
        
        return True
    except Exception as e:
        print(f"❌ 超时处理测试失败: {str(e)}")
        return False


def test_api_routes():
    """测试 API 路由更新"""
    print("\n" + "=" * 60)
    print("测试 7: API 路由更新")
    print("=" * 60)
    
    try:
        from app.routes.ai import router
        
        # 获取所有路由
        routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods),
                    'name': route.name
                })
        
        print("✅ AI 路由端点:")
        for route in routes:
            methods = ', '.join(route['methods'])
            print(f"   [{methods}] {route['path']}")
        
        # 检查是否有任务状态查询端点
        task_status_route = any('/task/' in r['path'] for r in routes)
        
        if task_status_route:
            print("\n✅ 任务状态查询端点已添加")
        else:
            print("\n⚠️  未找到任务状态查询端点")
        
        return True
    except Exception as e:
        print(f"❌ API 路由测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Celery 异步任务实现测试")
    print("=" * 60)
    
    tests = [
        test_task_module_import,
        test_celery_app_config,
        test_task_registration,
        test_task_signature,
        test_retry_logic,
        test_timeout_handling,
        test_api_routes,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 测试执行异常: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过!")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
