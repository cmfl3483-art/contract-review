"""
测试错误处理功能
Test error handling functionality
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_custom_exceptions():
    """测试自定义异常类"""
    print("\n" + "="*60)
    print("测试 1: 自定义异常类")
    print("="*60)
    
    try:
        from app.core.exceptions import (
            ValidationError,
            UnauthorizedError,
            ForbiddenError,
            NotFoundError,
            ConflictError,
            PayloadTooLargeError,
            DatabaseError,
            AIServiceError,
            MinIOServiceError,
            ServiceUnavailableError
        )
        
        # 测试各种异常
        exceptions_to_test = [
            (ValidationError("字段验证失败", field="name"), 400, "VALIDATION_ERROR"),
            (UnauthorizedError(), 401, "UNAUTHORIZED"),
            (ForbiddenError(), 403, "FORBIDDEN"),
            (NotFoundError("资源不存在", resource="contract"), 404, "NOT_FOUND"),
            (ConflictError("数据冲突"), 409, "CONFLICT"),
            (PayloadTooLargeError(max_size=20*1024*1024), 413, "PAYLOAD_TOO_LARGE"),
            (DatabaseError(), 500, "DATABASE_ERROR"),
            (AIServiceError(), 502, "EXTERNAL_SERVICE_ERROR"),
            (MinIOServiceError(), 502, "EXTERNAL_SERVICE_ERROR"),
            (ServiceUnavailableError(), 503, "SERVICE_UNAVAILABLE"),
        ]
        
        all_passed = True
        for exc, expected_status, expected_code in exceptions_to_test:
            if exc.status_code != expected_status:
                print(f"  ✗ {exc.__class__.__name__}: 状态码错误 (期望 {expected_status}, 实际 {exc.status_code})")
                all_passed = False
            elif exc.code != expected_code:
                print(f"  ✗ {exc.__class__.__name__}: 错误码错误 (期望 {expected_code}, 实际 {exc.code})")
                all_passed = False
            else:
                print(f"  ✓ {exc.__class__.__name__}: 状态码={exc.status_code}, 错误码={exc.code}")
        
        if all_passed:
            print("\n✅ 所有自定义异常类测试通过")
            return True
        else:
            print("\n❌ 部分自定义异常类测试失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handler_module():
    """测试错误处理模块"""
    print("\n" + "="*60)
    print("测试 2: 错误处理模块")
    print("="*60)
    
    try:
        from app.core.error_handler import (
            app_exception_handler,
            http_exception_handler,
            validation_exception_handler,
            database_exception_handler,
            general_exception_handler,
            register_exception_handlers
        )
        
        print("  ✓ app_exception_handler 导入成功")
        print("  ✓ http_exception_handler 导入成功")
        print("  ✓ validation_exception_handler 导入成功")
        print("  ✓ database_exception_handler 导入成功")
        print("  ✓ general_exception_handler 导入成功")
        print("  ✓ register_exception_handlers 导入成功")
        
        print("\n✅ 错误处理模块导入成功")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_db_error_handler():
    """测试数据库错误处理工具"""
    print("\n" + "="*60)
    print("测试 3: 数据库错误处理工具")
    print("="*60)
    
    try:
        from app.utils.db_error_handler import (
            handle_db_error,
            safe_db_operation
        )
        
        print("  ✓ handle_db_error 导入成功")
        print("  ✓ safe_db_operation 导入成功")
        
        # 测试错误处理逻辑
        from sqlalchemy.exc import NoResultFound, IntegrityError
        from app.core.exceptions import NotFoundError, ConflictError
        
        # 测试 NoResultFound
        try:
            handle_db_error(NoResultFound(), "查询操作")
        except NotFoundError as e:
            print(f"  ✓ NoResultFound 正确转换为 NotFoundError: {e.message}")
        except Exception as e:
            print(f"  ✗ NoResultFound 转换失败: {type(e).__name__}")
            return False
        
        print("\n✅ 数据库错误处理工具测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_external_service_handler():
    """测试外部服务错误处理工具"""
    print("\n" + "="*60)
    print("测试 4: 外部服务错误处理工具")
    print("="*60)
    
    try:
        from app.utils.external_service_handler import (
            handle_ai_service_call,
            handle_minio_operation,
            with_retry,
            CircuitBreaker
        )
        
        print("  ✓ handle_ai_service_call 导入成功")
        print("  ✓ handle_minio_operation 导入成功")
        print("  ✓ with_retry 装饰器导入成功")
        print("  ✓ CircuitBreaker 类导入成功")
        
        # 测试熔断器初始化
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0
        )
        
        print(f"  ✓ 熔断器初始化成功: state={breaker.state}, threshold={breaker.failure_threshold}")
        
        print("\n✅ 外部服务错误处理工具测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_main_app_integration():
    """测试主应用集成"""
    print("\n" + "="*60)
    print("测试 5: 主应用集成")
    print("="*60)
    
    try:
        # 检查 main.py 是否导入了错误处理器
        with open("app/main.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        checks = [
            ("导入错误处理器", "from app.core.error_handler import register_exception_handlers"),
            ("注册错误处理器", "register_exception_handlers(app)"),
        ]
        
        all_passed = True
        for check_name, check_string in checks:
            if check_string in content:
                print(f"  ✓ {check_name}: 已集成")
            else:
                print(f"  ✗ {check_name}: 未找到")
                all_passed = False
        
        if all_passed:
            print("\n✅ 主应用集成测试通过")
            return True
        else:
            print("\n❌ 主应用集成测试失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_error_response_format():
    """测试错误响应格式"""
    print("\n" + "="*60)
    print("测试 6: 错误响应格式")
    print("="*60)
    
    try:
        from app.core.exceptions import ValidationError, NotFoundError
        
        # 测试错误响应包含必要字段
        validation_error = ValidationError("测试错误", field="test_field")
        
        required_fields = ["message", "code", "status_code"]
        all_passed = True
        
        for field in required_fields:
            if hasattr(validation_error, field):
                value = getattr(validation_error, field)
                print(f"  ✓ {field}: {value}")
            else:
                print(f"  ✗ 缺少字段: {field}")
                all_passed = False
        
        # 测试 details 字段
        if validation_error.details and "field" in validation_error.details:
            print(f"  ✓ details.field: {validation_error.details['field']}")
        else:
            print(f"  ✗ details 字段格式错误")
            all_passed = False
        
        if all_passed:
            print("\n✅ 错误响应格式测试通过")
            return True
        else:
            print("\n❌ 错误响应格式测试失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试后端错误处理功能")
    print("="*60)
    
    tests = [
        ("自定义异常类", test_custom_exceptions),
        ("错误处理模块", test_error_handler_module),
        ("数据库错误处理", test_db_error_handler),
        ("外部服务错误处理", test_external_service_handler),
        ("主应用集成", test_main_app_integration),
        ("错误响应格式", test_error_response_format),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 执行失败: {str(e)}")
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
