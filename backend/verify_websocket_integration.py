"""
验证 WebSocket 集成到业务逻辑
Verify WebSocket Integration into Business Logic
"""
import ast
import sys
from pathlib import Path


def check_file_imports(file_path: str, required_import: str) -> bool:
    """检查文件是否导入了必需的模块"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and required_import in node.module:
                    return True
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if required_import in alias.name:
                        return True
        return False
    except Exception as e:
        print(f"❌ 读取文件失败 {file_path}: {e}")
        return False


def check_function_calls(file_path: str, function_name: str) -> list:
    """检查文件中是否调用了指定函数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
        
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == function_name:
                        # 获取行号
                        calls.append(node.lineno)
        return calls
    except Exception as e:
        print(f"❌ 解析文件失败 {file_path}: {e}")
        return []


def main():
    print("=" * 60)
    print("验证 WebSocket 集成到业务逻辑")
    print("=" * 60)
    print()
    
    # 检查文件是否存在
    files_to_check = {
        "comment_service": "app/services/comment_service.py",
        "review_service": "app/services/review_service.py",
        "contract_service": "app/services/contract_service.py"
    }
    
    all_files_exist = True
    for name, path in files_to_check.items():
        if not Path(path).exists():
            print(f"❌ 文件不存在: {path}")
            all_files_exist = False
        else:
            print(f"✅ 文件存在: {path}")
    
    if not all_files_exist:
        print("\n❌ 部分文件缺失!")
        return False
    
    print()
    print("-" * 60)
    print("检查导入 notification_service")
    print("-" * 60)
    
    # 检查是否导入了 notification_service
    import_checks = {
        "comment_service.py": check_file_imports(
            files_to_check["comment_service"],
            "notification_service"
        ),
        "review_service.py": check_file_imports(
            files_to_check["review_service"],
            "notification_service"
        ),
        "contract_service.py": check_file_imports(
            files_to_check["contract_service"],
            "notification_service"
        )
    }
    
    for file, imported in import_checks.items():
        if imported:
            print(f"✅ {file} 已导入 notification_service")
        else:
            print(f"❌ {file} 未导入 notification_service")
    
    print()
    print("-" * 60)
    print("检查 WebSocket 通知调用")
    print("-" * 60)
    
    # 检查各个服务中的通知调用
    checks = [
        {
            "file": files_to_check["comment_service"],
            "name": "CommentService",
            "notifications": [
                ("notify_comment_added", "添加评论时发送通知"),
                ("notify_reply_added", "添加回复时发送通知"),
                ("notify_like_updated", "点赞评论时发送通知")
            ]
        },
        {
            "file": files_to_check["review_service"],
            "name": "ReviewService",
            "notifications": [
                ("notify_review_added", "同意评审时发送通知"),
                ("notify_pending_changed", "待办数量变化时发送通知"),
                ("notify_like_updated", "点赞评审时发送通知"),
                ("notify_contract_updated", "合同状态变更时发送通知")
            ]
        },
        {
            "file": files_to_check["contract_service"],
            "name": "ContractService",
            "notifications": [
                ("notify_contract_updated", "更新合同状态时发送通知")
            ]
        }
    ]
    
    all_notifications_integrated = True
    
    for check in checks:
        print(f"\n{check['name']}:")
        for func_name, description in check["notifications"]:
            calls = check_function_calls(check["file"], func_name)
            if calls:
                print(f"  ✅ {description} ({func_name}) - 第 {calls} 行")
            else:
                print(f"  ❌ {description} ({func_name}) - 未找到调用")
                all_notifications_integrated = False
    
    print()
    print("-" * 60)
    print("集成检查总结")
    print("-" * 60)
    
    if all(import_checks.values()) and all_notifications_integrated:
        print("✅ WebSocket 通知已成功集成到业务逻辑!")
        print()
        print("集成的功能:")
        print("  1. ✅ 创建评论时发送 comment:added 事件")
        print("  2. ✅ 创建回复时发送 reply:added 事件")
        print("  3. ✅ 同意评审时发送 review:added 事件")
        print("  4. ✅ 同意评审时发送 pending:changed 事件")
        print("  5. ✅ 点赞评审时发送 like:updated 事件")
        print("  6. ✅ 点赞评论时发送 like:updated 事件")
        print("  7. ✅ 合同状态变更时发送 contract:updated 事件")
        print()
        print("所有必需的 WebSocket 通知都已集成!")
        return True
    else:
        print("❌ WebSocket 通知集成不完整!")
        if not all(import_checks.values()):
            print("  - 部分文件未导入 notification_service")
        if not all_notifications_integrated:
            print("  - 部分通知调用未实现")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
