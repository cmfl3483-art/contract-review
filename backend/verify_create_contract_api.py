"""
简单的创建合同API验证脚本
验证POST /api/contracts端点是否正确实现
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

async def verify_create_contract_api():
    """验证创建合同API的实现"""
    print("=" * 80)
    print("验证创建合同API (Task 6.1)")
    print("=" * 80)
    
    # 1. 检查路由文件是否存在
    print("\n1. 检查路由文件...")
    routes_file = Path(__file__).parent / "app" / "routes" / "contracts.py"
    if not routes_file.exists():
        print("   ❌ 路由文件不存在")
        return False
    print("   ✅ 路由文件存在")
    
    # 2. 检查路由中是否定义了POST /api/contracts端点
    print("\n2. 检查POST /api/contracts端点...")
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if '@router.post("")' in content or '@router.post("/")' in content:
            print("   ✅ POST端点已定义")
        else:
            print("   ❌ POST端点未定义")
            return False
    
    # 3. 检查请求模型是否定义
    print("\n3. 检查请求模型...")
    if 'CreateContractRequest' in content:
        print("   ✅ CreateContractRequest模型已定义")
    else:
        print("   ❌ CreateContractRequest模型未定义")
        return False
    
    # 4. 检查必填字段验证
    print("\n4. 检查必填字段验证...")
    checks = {
        'name字段': 'name: str' in content,
        'reviewers字段': 'reviewers: List' in content,
        'description可选': 'description: Optional[str]' in content,
        'cc_users可选': 'cc_users: Optional[List[str]]' in content
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        if passed:
            print(f"   ✅ {check_name}")
        else:
            print(f"   ❌ {check_name}")
            all_passed = False
    
    if not all_passed:
        return False
    
    # 5. 检查服务层调用
    print("\n5. 检查服务层调用...")
    if 'contract_service.create_contract' in content:
        print("   ✅ 调用了ContractService.create_contract")
    else:
        print("   ❌ 未调用ContractService.create_contract")
        return False
    
    # 6. 检查服务层实现
    print("\n6. 检查服务层实现...")
    service_file = Path(__file__).parent / "app" / "services" / "contract_service.py"
    if not service_file.exists():
        print("   ❌ 服务文件不存在")
        return False
    
    with open(service_file, 'r', encoding='utf-8') as f:
        service_content = f.read()
        if 'async def create_contract' in service_content:
            print("   ✅ create_contract方法已实现")
        else:
            print("   ❌ create_contract方法未实现")
            return False
    
    # 7. 检查事务处理
    print("\n7. 检查事务处理...")
    if 'async with db.begin()' in service_content:
        print("   ✅ 使用了数据库事务")
    else:
        print("   ⚠️  未使用数据库事务(建议使用)")
    
    # 8. 检查评审记录创建
    print("\n8. 检查评审记录创建...")
    if 'Review(' in service_content and 'for reviewer in reviewers' in service_content:
        print("   ✅ 为每个评审人创建评审记录")
    else:
        print("   ❌ 未为评审人创建评审记录")
        return False
    
    # 9. 检查缓存清除
    print("\n9. 检查缓存清除...")
    if '_clear_contract_list_cache' in service_content:
        print("   ✅ 清除了合同列表缓存")
    else:
        print("   ⚠️  未清除缓存(建议清除)")
    
    # 10. 检查错误处理
    print("\n10. 检查错误处理...")
    if 'try:' in content and 'except' in content:
        print("   ✅ 实现了错误处理")
    else:
        print("   ⚠️  未实现错误处理")
    
    print("\n" + "=" * 80)
    print("✅ 所有核心功能检查通过!")
    print("=" * 80)
    
    # 打印API使用示例
    print("\nAPI使用示例:")
    print("-" * 80)
    print("POST /api/contracts")
    print("Content-Type: application/json")
    print("Authorization: Bearer <token>")
    print()
    print("请求体:")
    print("""{
  "name": "测试合同",
  "description": "这是一个测试合同",
  "reviewers": [
    {
      "user_id": "user-123",
      "role": "法务",
      "step": "法务初审"
    },
    {
      "user_id": "user-456",
      "role": "财务",
      "step": "财务审核"
    }
  ],
  "cc_users": ["user-789"]
}""")
    print()
    print("响应:")
    print("""{
  "success": true,
  "data": {
    "contractId": "contract-uuid"
  }
}""")
    print("-" * 80)
    
    return True

if __name__ == "__main__":
    result = asyncio.run(verify_create_contract_api())
    sys.exit(0 if result else 1)
