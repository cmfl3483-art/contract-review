"""
验证 AI 智能总结 API 代码结构
Verify AI Summary API Code Structure (without imports)
"""
import os
import re


def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} 不存在: {filepath}")
        return False


def check_code_contains(filepath, patterns, description):
    """检查代码是否包含特定模式"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        results = []
        for pattern_name, pattern in patterns:
            if re.search(pattern, content, re.MULTILINE):
                print(f"   ✅ {pattern_name}")
                results.append(True)
            else:
                print(f"   ❌ {pattern_name}")
                results.append(False)
        
        return all(results)
    except Exception as e:
        print(f"   ❌ 读取文件失败: {str(e)}")
        return False


def test_route_file():
    """测试 1: 验证路由文件"""
    print("\n" + "=" * 60)
    print("测试 1: 验证路由文件")
    print("=" * 60)
    
    filepath = "app/routes/ai.py"
    if not check_file_exists(filepath, "AI 路由文件"):
        return False
    
    patterns = [
        ("POST /summary/{contract_id} 端点", r'@router\.post\("/summary/\{contract_id\}"\)'),
        ("GET /summary/task/{task_id} 端点", r'@router\.get\("/summary/task/\{task_id\}"\)'),
        ("force_regenerate 参数", r'force_regenerate.*Query'),
        ("缓存检查逻辑", r'redis_client\.get\(cache_key\)'),
        ("异步任务创建", r'generate_ai_summary_task\.apply_async'),
        ("降级处理", r'except Exception as task_error'),
        ("同步生成", r'ai_service\.generate_summary'),
        ("友好提示", r'AI服务暂时不可用'),
    ]
    
    return check_code_contains(filepath, patterns, "路由实现")


def test_service_file():
    """测试 2: 验证服务文件"""
    print("\n" + "=" * 60)
    print("测试 2: 验证服务文件")
    print("=" * 60)
    
    filepath = "app/services/ai_service.py"
    if not check_file_exists(filepath, "AI 服务文件"):
        return False
    
    patterns = [
        ("generate_summary 方法", r'async def generate_summary'),
        ("_extract_key_issues 方法", r'async def _extract_key_issues'),
        ("answer_question 方法", r'async def answer_question'),
        ("缓存检查", r'redis_client\.get'),
        ("缓存设置", r'redis_client\.set.*expire'),
        ("关键词提取", r'keywords = \[.*建议.*需要.*问题.*风险.*隐患'),
        ("最多3个关键问题", r'len\(key_issues\) >= 3'),
        ("审批状态计算", r'approval_status.*completed.*in_progress'),
    ]
    
    return check_code_contains(filepath, patterns, "服务实现")


def test_task_file():
    """测试 3: 验证任务文件"""
    print("\n" + "=" * 60)
    print("测试 3: 验证任务文件")
    print("=" * 60)
    
    filepath = "app/tasks/ai_tasks.py"
    if not check_file_exists(filepath, "AI 任务文件"):
        return False
    
    patterns = [
        ("generate_ai_summary_task 任务", r'@celery_app\.task'),
        ("任务名称", r'name="app\.tasks\.ai_tasks\.generate_ai_summary_task"'),
        ("最大重试次数", r'max_retries=3'),
        ("重试延迟", r'default_retry_delay=60'),
        ("软超时限制", r'soft_time_limit=300'),
        ("硬超时限制", r'time_limit=360'),
        ("异步任务基类", r'class AsyncTask\(Task\)'),
        ("重试逻辑", r'raise self\.retry'),
        ("指数退避", r'retry_delay.*\*.*\*\*.*retries'),
    ]
    
    return check_code_contains(filepath, patterns, "任务实现")


def test_celery_config():
    """测试 4: 验证 Celery 配置"""
    print("\n" + "=" * 60)
    print("测试 4: 验证 Celery 配置")
    print("=" * 60)
    
    filepath = "app/celery_app.py"
    if not check_file_exists(filepath, "Celery 配置文件"):
        return False
    
    patterns = [
        ("Celery 应用创建", r'celery_app = Celery'),
        ("Broker URL", r'broker=settings\.CELERY_BROKER_URL'),
        ("Result Backend", r'backend=settings\.CELERY_RESULT_BACKEND'),
        ("任务序列化", r'task_serializer.*json'),
        ("时区配置", r'timezone.*Asia/Shanghai'),
        ("任务超时", r'task_time_limit.*30.*60'),
        ("自动发现任务", r'autodiscover_tasks'),
    ]
    
    return check_code_contains(filepath, patterns, "Celery 配置")


def test_config_file():
    """测试 5: 验证配置文件"""
    print("\n" + "=" * 60)
    print("测试 5: 验证配置文件")
    print("=" * 60)
    
    filepath = "app/core/config.py"
    if not check_file_exists(filepath, "配置文件"):
        return False
    
    patterns = [
        ("Celery Broker URL", r'CELERY_BROKER_URL.*redis'),
        ("Celery Result Backend", r'CELERY_RESULT_BACKEND.*redis'),
        ("AI Provider", r'AI_PROVIDER.*str'),
        ("AI API Base", r'AI_API_BASE.*str'),
        ("AI Model", r'AI_MODEL.*str'),
        ("AI Timeout", r'AI_TIMEOUT.*int'),
    ]
    
    return check_code_contains(filepath, patterns, "配置")


def test_main_app():
    """测试 6: 验证主应用"""
    print("\n" + "=" * 60)
    print("测试 6: 验证主应用")
    print("=" * 60)
    
    filepath = "app/main.py"
    if not check_file_exists(filepath, "主应用文件"):
        return False
    
    patterns = [
        ("AI 路由导入", r'from app\.routes import.*ai'),
        ("AI 路由注册", r'app\.include_router\(ai\.router\)'),
    ]
    
    return check_code_contains(filepath, patterns, "主应用")


def test_documentation():
    """测试 7: 验证文档"""
    print("\n" + "=" * 60)
    print("测试 7: 验证文档")
    print("=" * 60)
    
    filepath = "TASK_15.1_COMPLETE.md"
    if not check_file_exists(filepath, "任务完成文档"):
        return False
    
    patterns = [
        ("任务概述", r'## 任务概述'),
        ("API 端点", r'POST /api/ai/summary'),
        ("异步任务", r'generate_ai_summary_task'),
        ("降级处理", r'降级处理'),
        ("测试说明", r'## 测试'),
        ("验收标准", r'## 验收标准'),
    ]
    
    return check_code_contains(filepath, patterns, "文档")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("AI 智能总结 API 代码结构验证")
    print("=" * 60)
    
    # 切换到项目目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        test_route_file,
        test_service_file,
        test_task_file,
        test_celery_config,
        test_config_file,
        test_main_app,
        test_documentation,
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
        print("\n✅ 所有代码结构检查通过! API 实现完成。")
        print("\n📝 注意:")
        print("   - 需要启动 Redis 服务")
        print("   - 需要启动 Celery Worker: celery -A app.celery_app worker --loglevel=info")
        print("   - 需要配置 AI API Key 在 .env 文件中")
        return 0
    else:
        print(f"\n❌ {total - passed} 个检查失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
