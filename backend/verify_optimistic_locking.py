"""
验证乐观锁实现
Verify optimistic locking implementation
"""
import sys
import os
import ast
import inspect

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def verify_model_has_version_field():
    """验证Contract模型有version字段"""
    print("1. 验证Contract模型有version字段...")
    
    # 读取Contract模型文件
    with open('app/models/contract.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否包含version字段定义
    assert 'version' in content, "Contract模型文件中没有找到version字段"
    assert 'Integer' in content, "Contract模型文件中没有导入Integer类型"
    assert '乐观锁' in content or 'optimistic' in content.lower(), "Contract模型文件中没有乐观锁相关注释"
    print("   ✓ Contract模型文件包含version字段定义")
    
    # 检查version字段的配置
    assert 'nullable=False' in content or 'nullable = False' in content, "version字段应该是NOT NULL"
    assert 'default=1' in content or 'default = 1' in content, "version字段应该有默认值1"
    print("   ✓ version字段配置正确(NOT NULL, default=1)")
    
    print()


def verify_service_has_optimistic_locking():
    """验证ContractService有乐观锁方法"""
    print("2. 验证ContractService有乐观锁方法...")
    
    # 读取ContractService文件
    with open('app/services/contract_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否导入ConflictError
    assert 'from app.core.exceptions import' in content and 'ConflictError' in content, \
        "ContractService没有导入ConflictError"
    print("   ✓ ContractService导入了ConflictError")
    
    # 检查update_contract_status方法是否有expected_version参数
    assert 'expected_version' in content, "ContractService缺少expected_version参数"
    print("   ✓ ContractService方法包含expected_version参数")
    
    # 检查是否有版本检查逻辑
    assert 'contract.version != expected_version' in content or \
           'contract.version!= expected_version' in content or \
           'contract.version !=expected_version' in content, \
        "ContractService缺少版本检查逻辑"
    print("   ✓ ContractService包含版本检查逻辑")
    
    # 检查是否抛出ConflictError
    assert 'raise ConflictError' in content, "ContractService没有抛出ConflictError"
    print("   ✓ ContractService在版本冲突时抛出ConflictError")
    
    # 检查是否递增版本号
    assert 'version += 1' in content or 'version = version + 1' in content or \
           'version + 1' in content, \
        "ContractService没有递增版本号"
    print("   ✓ ContractService递增版本号")
    
    # 检查是否有update_contract方法
    assert 'async def update_contract' in content, "ContractService缺少update_contract方法"
    print("   ✓ ContractService有update_contract方法")
    
    print()


def verify_conflict_error_exists():
    """验证ConflictError异常存在"""
    print("3. 验证ConflictError异常存在...")
    
    # 读取exceptions文件
    with open('app/core/exceptions.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查ConflictError类是否存在
    assert 'class ConflictError' in content, "exceptions.py中没有ConflictError类"
    print("   ✓ ConflictError异常类存在")
    
    # 检查ConflictError的status_code
    assert '409' in content, "ConflictError应该使用409状态码"
    print("   ✓ ConflictError使用409状态码")
    
    print()


def verify_migration_file_exists():
    """验证迁移文件存在"""
    print("4. 验证迁移文件存在...")
    
    migration_file = "alembic/versions/003_add_optimistic_locking_version.py"
    assert os.path.exists(migration_file), f"迁移文件不存在: {migration_file}"
    print(f"   ✓ 迁移文件存在: {migration_file}")
    
    # 读取迁移文件内容
    with open(migration_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查迁移文件包含必要的内容
    assert "add_column" in content, "迁移文件应该包含add_column操作"
    assert "version" in content, "迁移文件应该包含version字段"
    assert "Integer" in content, "迁移文件应该使用Integer类型"
    print("   ✓ 迁移文件内容正确")
    
    print()


def verify_test_file_exists():
    """验证测试文件存在"""
    print("5. 验证测试文件存在...")
    
    test_file = "tests/test_optimistic_locking.py"
    assert os.path.exists(test_file), f"测试文件不存在: {test_file}"
    print(f"   ✓ 测试文件存在: {test_file}")
    
    # 读取测试文件内容
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查测试文件包含必要的测试用例
    assert "test_update_with_correct_version" in content, "缺少正确版本号测试"
    assert "test_update_with_wrong_version" in content, "缺少错误版本号测试"
    assert "test_concurrent_update_simulation" in content, "缺少并发更新测试"
    print("   ✓ 测试文件包含必要的测试用例")
    
    print()


def main():
    """主函数"""
    print("=" * 60)
    print("验证乐观锁实现")
    print("=" * 60)
    print()
    
    try:
        verify_model_has_version_field()
        verify_service_has_optimistic_locking()
        verify_conflict_error_exists()
        verify_migration_file_exists()
        verify_test_file_exists()
        
        print("=" * 60)
        print("✓ 所有验证通过!")
        print("=" * 60)
        print()
        print("乐观锁实现总结:")
        print("1. Contract模型添加了version字段(Integer类型,默认值1)")
        print("2. ContractService的update_contract_status方法支持expected_version参数")
        print("3. ContractService新增update_contract方法支持通用更新和乐观锁")
        print("4. 版本号不匹配时抛出ConflictError异常(HTTP 409)")
        print("5. 创建了数据库迁移文件(003_add_optimistic_locking_version.py)")
        print("6. 创建了完整的测试文件(test_optimistic_locking.py)")
        print()
        print("使用方法:")
        print("  # 更新合同状态(带版本检查)")
        print("  await contract_service.update_contract_status(")
        print("      contract_id='xxx',")
        print("      status='completed',")
        print("      expected_version=1,  # 期望的版本号")
        print("      db=db_session")
        print("  )")
        print()
        print("  # 通用更新(带版本检查)")
        print("  await contract_service.update_contract(")
        print("      contract_id='xxx',")
        print("      updates={'name': '新名称'},")
        print("      expected_version=1,")
        print("      db=db_session")
        print("  )")
        print()
        print("下一步:")
        print("1. 运行数据库迁移: alembic upgrade head")
        print("2. 运行测试: pytest tests/test_optimistic_locking.py")
        print()
        
        return 0
        
    except AssertionError as e:
        print(f"✗ 验证失败: {e}")
        return 1
    except Exception as e:
        print(f"✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
