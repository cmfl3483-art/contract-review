"""
测试数据库模型导入和基本功能
Test database models import and basic functionality
"""

import sys
from datetime import datetime
import uuid

def test_model_imports():
    """测试所有模型是否可以正确导入"""
    print("=" * 60)
    print("测试模型导入 / Testing Model Imports")
    print("=" * 60)
    
    try:
        from app.models.user import User
        print("✓ User 模型导入成功")
    except Exception as e:
        print(f"✗ User 模型导入失败: {e}")
        return False
    
    try:
        from app.models.contract import Contract, ContractStatus
        print("✓ Contract 模型导入成功")
    except Exception as e:
        print(f"✗ Contract 模型导入失败: {e}")
        return False
    
    try:
        from app.models.review import Review, ReviewStatus
        print("✓ Review 模型导入成功")
    except Exception as e:
        print(f"✗ Review 模型导入失败: {e}")
        return False
    
    try:
        from app.models.comment import Comment
        print("✓ Comment 模型导入成功")
    except Exception as e:
        print(f"✗ Comment 模型导入失败: {e}")
        return False
    
    try:
        from app.models.attachment import Attachment
        print("✓ Attachment 模型导入成功")
    except Exception as e:
        print(f"✗ Attachment 模型导入失败: {e}")
        return False
    
    try:
        from app.models.ai_summary import AISummary, ApprovalStatus
        print("✓ AISummary 模型导入成功")
    except Exception as e:
        print(f"✗ AISummary 模型导入失败: {e}")
        return False
    
    return True


def test_model_instantiation():
    """测试模型实例化"""
    print("\n" + "=" * 60)
    print("测试模型实例化 / Testing Model Instantiation")
    print("=" * 60)
    
    from app.models.user import User
    from app.models.contract import Contract, ContractStatus
    from app.models.review import Review, ReviewStatus
    from app.models.comment import Comment
    from app.models.attachment import Attachment
    from app.models.ai_summary import AISummary, ApprovalStatus
    
    try:
        # 测试 User 实例化
        user = User(
            dingtalk_user_id="test_user_123",
            name="测试用户",
            role="法务"
        )
        print(f"✓ User 实例化成功: {user}")
    except Exception as e:
        print(f"✗ User 实例化失败: {e}")
        return False
    
    try:
        # 测试 Contract 实例化
        contract = Contract(
            name="测试合同",
            description="这是一个测试合同",
            status=ContractStatus.PROGRESS,
            initiator_id=uuid.uuid4(),
            cc_users=["user1", "user2"]
        )
        print(f"✓ Contract 实例化成功: {contract}")
    except Exception as e:
        print(f"✗ Contract 实例化失败: {e}")
        return False
    
    try:
        # 测试 Review 实例化
        review = Review(
            contract_id=uuid.uuid4(),
            reviewer_id=uuid.uuid4(),
            role="法务",
            step="法务初审",
            opinion="同意并通过",
            status=ReviewStatus.APPROVED
        )
        print(f"✓ Review 实例化成功: {review}")
    except Exception as e:
        print(f"✗ Review 实例化失败: {e}")
        return False
    
    try:
        # 测试 Comment 实例化
        comment = Comment(
            contract_id=uuid.uuid4(),
            author_id=uuid.uuid4(),
            content="这是一条测试评论"
        )
        print(f"✓ Comment 实例化成功: {comment}")
    except Exception as e:
        print(f"✗ Comment 实例化失败: {e}")
        return False
    
    try:
        # 测试 Attachment 实例化
        attachment = Attachment(
            contract_id=uuid.uuid4(),
            file_name="test.pdf",
            version="v1.0",
            file_size=1024000,
            mime_type="application/pdf",
            storage_key="contracts/test.pdf",
            uploader_id=uuid.uuid4()
        )
        print(f"✓ Attachment 实例化成功: {attachment}")
    except Exception as e:
        print(f"✗ Attachment 实例化失败: {e}")
        return False
    
    try:
        # 测试 AISummary 实例化
        ai_summary = AISummary(
            contract_id=uuid.uuid4(),
            approval_status=ApprovalStatus.IN_PROGRESS,
            completed_count=2,
            total_count=5,
            review_count=3,
            key_issues=[
                {"issue": "需要补充法务意见", "solution": "已联系法务部门"}
            ]
        )
        print(f"✓ AISummary 实例化成功: {ai_summary}")
    except Exception as e:
        print(f"✗ AISummary 实例化失败: {e}")
        return False
    
    return True


def test_enum_values():
    """测试枚举类型"""
    print("\n" + "=" * 60)
    print("测试枚举类型 / Testing Enum Types")
    print("=" * 60)
    
    from app.models.contract import ContractStatus
    from app.models.review import ReviewStatus
    from app.models.ai_summary import ApprovalStatus
    
    # 测试 ContractStatus
    print(f"ContractStatus.PROGRESS = {ContractStatus.PROGRESS}")
    print(f"ContractStatus.COMPLETED = {ContractStatus.COMPLETED}")
    assert ContractStatus.PROGRESS.value == "progress"
    assert ContractStatus.COMPLETED.value == "completed"
    print("✓ ContractStatus 枚举值正确")
    
    # 测试 ReviewStatus
    print(f"ReviewStatus.PENDING = {ReviewStatus.PENDING}")
    print(f"ReviewStatus.REVIEWING = {ReviewStatus.REVIEWING}")
    print(f"ReviewStatus.APPROVED = {ReviewStatus.APPROVED}")
    assert ReviewStatus.PENDING.value == "pending"
    assert ReviewStatus.REVIEWING.value == "reviewing"
    assert ReviewStatus.APPROVED.value == "approved"
    print("✓ ReviewStatus 枚举值正确")
    
    # 测试 ApprovalStatus
    print(f"ApprovalStatus.COMPLETED = {ApprovalStatus.COMPLETED}")
    print(f"ApprovalStatus.IN_PROGRESS = {ApprovalStatus.IN_PROGRESS}")
    assert ApprovalStatus.COMPLETED.value == "completed"
    assert ApprovalStatus.IN_PROGRESS.value == "in_progress"
    print("✓ ApprovalStatus 枚举值正确")
    
    return True


def test_model_fields():
    """测试模型字段"""
    print("\n" + "=" * 60)
    print("测试模型字段 / Testing Model Fields")
    print("=" * 60)
    
    from app.models.user import User
    from app.models.contract import Contract
    from app.models.review import Review
    from app.models.comment import Comment
    from app.models.attachment import Attachment
    from app.models.ai_summary import AISummary
    
    # 检查 User 字段
    user_fields = ['id', 'dingtalk_user_id', 'dingtalk_union_id', 'name', 'role', 
                   'email', 'mobile', 'avatar', 'department', 'created_at', 'updated_at']
    for field in user_fields:
        assert hasattr(User, field), f"User 缺少字段: {field}"
    print(f"✓ User 模型有 {len(user_fields)} 个字段")
    
    # 检查 Contract 字段
    contract_fields = ['id', 'name', 'description', 'status', 'initiator_id', 
                       'cc_users', 'version', 'created_at', 'updated_at']
    for field in contract_fields:
        assert hasattr(Contract, field), f"Contract 缺少字段: {field}"
    print(f"✓ Contract 模型有 {len(contract_fields)} 个字段")
    
    # 检查 Review 字段
    review_fields = ['id', 'contract_id', 'reviewer_id', 'role', 'step', 'opinion', 
                     'status', 'likes', 'liked_by', 'created_at', 'updated_at']
    for field in review_fields:
        assert hasattr(Review, field), f"Review 缺少字段: {field}"
    print(f"✓ Review 模型有 {len(review_fields)} 个字段")
    
    # 检查 Comment 字段
    comment_fields = ['id', 'contract_id', 'review_id', 'parent_comment_id', 'author_id', 
                      'content', 'likes', 'liked_by', 'created_at', 'updated_at']
    for field in comment_fields:
        assert hasattr(Comment, field), f"Comment 缺少字段: {field}"
    print(f"✓ Comment 模型有 {len(comment_fields)} 个字段")
    
    # 检查 Attachment 字段
    attachment_fields = ['id', 'contract_id', 'file_name', 'version', 'file_size', 
                         'mime_type', 'storage_key', 'uploader_id', 'created_at']
    for field in attachment_fields:
        assert hasattr(Attachment, field), f"Attachment 缺少字段: {field}"
    print(f"✓ Attachment 模型有 {len(attachment_fields)} 个字段")
    
    # 检查 AISummary 字段
    ai_summary_fields = ['id', 'contract_id', 'approval_status', 'completed_count', 
                         'total_count', 'review_count', 'key_issues', 'created_at', 'updated_at']
    for field in ai_summary_fields:
        assert hasattr(AISummary, field), f"AISummary 缺少字段: {field}"
    print(f"✓ AISummary 模型有 {len(ai_summary_fields)} 个字段")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("数据库模型验证测试")
    print("Database Models Verification Test")
    print("=" * 60 + "\n")
    
    all_passed = True
    
    # 测试模型导入
    if not test_model_imports():
        all_passed = False
        print("\n✗ 模型导入测试失败")
        return False
    
    # 测试模型实例化
    if not test_model_instantiation():
        all_passed = False
        print("\n✗ 模型实例化测试失败")
        return False
    
    # 测试枚举类型
    try:
        if not test_enum_values():
            all_passed = False
            print("\n✗ 枚举类型测试失败")
            return False
    except Exception as e:
        print(f"\n✗ 枚举类型测试失败: {e}")
        all_passed = False
        return False
    
    # 测试模型字段
    try:
        if not test_model_fields():
            all_passed = False
            print("\n✗ 模型字段测试失败")
            return False
    except Exception as e:
        print(f"\n✗ 模型字段测试失败: {e}")
        all_passed = False
        return False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过!")
        print("All tests passed!")
    else:
        print("❌ 部分测试失败")
        print("Some tests failed")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
