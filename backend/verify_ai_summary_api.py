"""
验证 AI 智能总结 API 实现
Verify AI Summary API Implementation
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """测试 1: 验证所有必要的导入"""
    print("\n" + "=" * 60)
    print("测试 1: 验证导入")
    print("=" * 60)
    
    try:
        from app.routes.ai import router, generate_summary, get_task_status
        print("✅ AI 路由导入成功")
        
        from app.services.ai_service import AIService
        print("✅ AI 服务导入成功")
        
        from app.tasks.ai_tasks import generate_ai_summary_task
        print("✅ AI 异步任务导入成功")
        
        from app.celery_app import celery_app
        print("✅ Celery 应用导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        return False


def test_route_registration():
    """测试 2: 验证路由注册"""
    print("\n" + "=" * 60)
    print("测试 2: 验证路由注册")
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
        
        print(f"✅ 已注册 {len(routes)} 个路由:")
        for route in routes:
            methods_str = ', '.join(route['methods'])
            print(f"   {methods_str:10} {route['path']}")
        
        # 验证关键路由
        required_routes = [
            ('/api/ai/summary/{contract_id}', 'POST'),
            ('/api/ai/summary/task/{task_id}', 'GET'),
        ]
        
        for path, method in required_routes:
            found = any(
                route['path'] == path and method in route['methods']
                for route in routes
            )
            if found:
                print(f"✅ 找到路由: {method} {path}")
            else:
                print(f"❌ 缺少路由: {method} {path}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 路由注册验证失败: {str(e)}")
        return False


def test_celery_task_registration():
    """测试 3: 验证 Celery 任务注册"""
    print("\n" + "=" * 60)
    print("测试 3: 验证 Celery 任务注册")
    print("=" * 60)
    
    try:
        from app.celery_app import celery_app
        
        # 获取所有注册的任务
        registered_tasks = list(celery_app.tasks.keys())
        
        print(f"✅ 已注册 {len(registered_tasks)} 个 Celery 任务:")
        for task_name in registered_tasks:
            if not task_name.startswith('celery.'):
                print(f"   - {task_name}")
        
        # 验证关键任务
        required_task = "app.tasks.ai_tasks.generate_ai_summary_task"
        if required_task in registered_tasks:
            print(f"✅ 找到任务: {required_task}")
            
            # 获取任务配置
            task = celery_app.tasks[required_task]
            print(f"   配置:")
            print(f"   - max_retries: {task.max_retries}")
            print(f"   - default_retry_delay: {task.default_retry_delay}秒")
            print(f"   - soft_time_limit: {task.soft_time_limit}秒")
            print(f"   - time_limit: {task.time_limit}秒")
            
            return True
        else:
            print(f"❌ 缺少任务: {required_task}")
            return False
            
    except Exception as e:
        print(f"❌ Celery 任务注册验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_service_methods():
    """测试 4: 验证 AI 服务方法"""
    print("\n" + "=" * 60)
    print("测试 4: 验证 AI 服务方法")
    print("=" * 60)
    
    try:
        from app.services.ai_service import AIService
        import inspect
        
        ai_service = AIService()
        
        # 验证必要的方法
        required_methods = [
            'generate_summary',
            '_extract_key_issues',
            'answer_question',
        ]
        
        for method_name in required_methods:
            if hasattr(ai_service, method_name):
                method = getattr(ai_service, method_name)
                if callable(method):
                    # 获取方法签名
                    sig = inspect.signature(method)
                    params = list(sig.parameters.keys())
                    print(f"✅ 方法存在: {method_name}({', '.join(params)})")
                else:
                    print(f"❌ {method_name} 不是可调用方法")
                    return False
            else:
                print(f"❌ 缺少方法: {method_name}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ AI 服务方法验证失败: {str(e)}")
        return False


def test_endpoint_signature():
    """测试 5: 验证端点函数签名"""
    print("\n" + "=" * 60)
    print("测试 5: 验证端点函数签名")
    print("=" * 60)
    
    try:
        from app.routes.ai import generate_summary, get_task_status
        import inspect
        
        # 验证 generate_summary 签名
        sig = inspect.signature(generate_summary)
        params = list(sig.parameters.keys())
        print(f"✅ generate_summary 参数: {', '.join(params)}")
        
        # 验证必要参数
        required_params = ['contract_id', 'request', 'force_regenerate', 'db']
        for param in required_params:
            if param in params:
                print(f"   ✅ 参数存在: {param}")
            else:
                print(f"   ❌ 缺少参数: {param}")
                return False
        
        # 验证 get_task_status 签名
        sig = inspect.signature(get_task_status)
        params = list(sig.parameters.keys())
        print(f"✅ get_task_status 参数: {', '.join(params)}")
        
        required_params = ['task_id', 'request']
        for param in required_params:
            if param in params:
                print(f"   ✅ 参数存在: {param}")
            else:
                print(f"   ❌ 缺少参数: {param}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 端点函数签名验证失败: {str(e)}")
        return False


def test_config():
    """测试 6: 验证配置"""
    print("\n" + "=" * 60)
    print("测试 6: 验证配置")
    print("=" * 60)
    
    try:
        from app.core.config import settings
        
        print("✅ Celery 配置:")
        print(f"   Broker URL: {settings.CELERY_BROKER_URL}")
        print(f"   Result Backend: {settings.CELERY_RESULT_BACKEND}")
        
        print("✅ AI 配置:")
        print(f"   Provider: {settings.AI_PROVIDER}")
        print(f"   API Base: {settings.AI_API_BASE}")
        print(f"   Model: {settings.AI_MODEL}")
        print(f"   Timeout: {settings.AI_TIMEOUT}秒")
        
        return True
    except Exception as e:
        print(f"❌ 配置验证失败: {str(e)}")
        return False


def test_degradation_logic():
    """测试 7: 验证降级逻辑"""
    print("\n" + "=" * 60)
    print("测试 7: 验证降级逻辑")
    print("=" * 60)
    
    try:
        from app.routes.ai import generate_summary
        import inspect
        
        # 读取函数源代码
        source = inspect.getsource(generate_summary)
        
        # 检查关键降级逻辑
        checks = [
            ('缓存检查', 'redis_client.get'),
            ('异步任务', 'apply_async'),
            ('降级处理', 'except Exception as task_error'),
            ('同步生成', 'ai_service.generate_summary'),
            ('友好提示', 'AI服务暂时不可用'),
        ]
        
        for check_name, check_str in checks:
            if check_str in source:
                print(f"✅ {check_name}: 已实现")
            else:
                print(f"❌ {check_name}: 未找到")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 降级逻辑验证失败: {str(e)}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("AI 智能总结 API 实现验证")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_route_registration,
        test_celery_task_registration,
        test_ai_service_methods,
        test_endpoint_signature,
        test_config,
        test_degradation_logic,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 测试执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过! API 实现完成。")
        return 0
    else:
        print(f"\n❌ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
