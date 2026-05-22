"""
验证通知服务代码结构
Verify Notification Service Code Structure

检查 NotificationService 类是否正确实现了所有必需的方法
"""
import ast
import sys
from pathlib import Path


def verify_notification_service():
    """验证通知服务的代码结构"""
    
    print("=" * 60)
    print("验证通知服务 (NotificationService)")
    print("=" * 60)
    
    # 读取通知服务文件
    service_file = Path(__file__).parent / "app" / "services" / "notification_service.py"
    
    if not service_file.exists():
        print(f"❌ 文件不存在: {service_file}")
        return False
    
    with open(service_file, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # 解析 AST
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        return False
    
    # 查找 NotificationService 类
    notification_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "NotificationService":
            notification_class = node
            break
    
    if not notification_class:
        print("❌ 未找到 NotificationService 类")
        return False
    
    print("\n✅ 找到 NotificationService 类")
    
    # 检查必需的方法
    required_methods = [
        "notify_contract_updated",
        "notify_review_added",
        "notify_comment_added",
        "notify_reply_added",
        "notify_like_updated",
        "notify_pending_changed",
    ]
    
    found_methods = []
    for node in notification_class.body:
        if isinstance(node, ast.AsyncFunctionDef):
            found_methods.append(node.name)
    
    print("\n检查必需的方法:")
    all_found = True
    for method in required_methods:
        if method in found_methods:
            print(f"  ✅ {method}")
        else:
            print(f"  ❌ {method} (缺失)")
            all_found = False
    
    # 检查额外的方法
    extra_methods = [m for m in found_methods if m not in required_methods and not m.startswith('_')]
    if extra_methods:
        print("\n额外实现的方法:")
        for method in extra_methods:
            print(f"  ℹ️  {method}")
    
    # 检查导入
    print("\n检查导入:")
    imports_found = {
        "emit_contract_updated": False,
        "emit_review_added": False,
        "emit_comment_added": False,
        "emit_reply_added": False,
        "emit_like_updated": False,
        "emit_pending_changed": False,
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "app.core.socketio_server":
                for alias in node.names:
                    if alias.name in imports_found:
                        imports_found[alias.name] = True
    
    all_imports_found = True
    for import_name, found in imports_found.items():
        if found:
            print(f"  ✅ {import_name}")
        else:
            print(f"  ❌ {import_name} (缺失)")
            all_imports_found = False
    
    # 检查全局实例
    print("\n检查全局实例:")
    has_global_instance = "notification_service = NotificationService()" in code
    if has_global_instance:
        print("  ✅ notification_service 全局实例")
    else:
        print("  ❌ notification_service 全局实例 (缺失)")
    
    # 总结
    print("\n" + "=" * 60)
    if all_found and all_imports_found and has_global_instance:
        print("✅ NotificationService 实现完整!")
        print("=" * 60)
        print("\n实现的功能:")
        print("  1. ✅ 合同更新通知 (contract:updated)")
        print("  2. ✅ 评审添加通知 (review:added)")
        print("  3. ✅ 评论添加通知 (comment:added)")
        print("  4. ✅ 回复添加通知 (reply:added)")
        print("  5. ✅ 点赞更新通知 (like:updated)")
        print("  6. ✅ 待办变化通知 (pending:changed)")
        print("\n所有必需的事件类型都已实现!")
        return True
    else:
        print("❌ NotificationService 实现不完整")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = verify_notification_service()
    sys.exit(0 if success else 1)
