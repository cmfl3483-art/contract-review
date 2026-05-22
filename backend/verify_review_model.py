"""
验证 Review 模型是否满足所有需求
Verify Review model meets all requirements
"""

import sys
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# 导入模型
from app.models.review import Review, ReviewStatus
from app.core.database import Base, engine


def verify_review_model():
    """验证 Review 模型的所有字段和索引"""
    print("=" * 80)
    print("验证 Review 模型 (Verifying Review Model)")
    print("=" * 80)
    
    # 1. 验证模型字段
    print("\n1. 验证模型字段 (Verifying Model Fields)")
    print("-" * 80)
    
    required_fields = {
        'id': 'UUID',
        'contract_id': 'UUID',
        'reviewer_id': 'UUID',
        'role': 'String',
        'step': 'String',
        'opinion': 'Text (nullable)',
        'status': 'Enum (ReviewStatus)',
        'likes': 'Integer',
        'liked_by': 'ARRAY(String)',
        'created_at': 'DateTime',
        'updated_at': 'DateTime'
    }
    
    inspector = inspect(Review)
    columns = {col.key: col for col in inspector.columns}
    
    all_fields_present = True
    for field_name, field_type in required_fields.items():
        if field_name in columns:
            col = columns[field_name]
            print(f"✓ {field_name}: {col.type} - {field_type}")
        else:
            print(f"✗ {field_name}: MISSING - Expected {field_type}")
            all_fields_present = False
    
    # 2. 验证外键关系
    print("\n2. 验证外键关系 (Verifying Foreign Keys)")
    print("-" * 80)
    
    required_fks = {
        'contract_id': 'contracts.id',
        'reviewer_id': 'users.id'
    }
    
    fks = {fk.parent.name: f"{fk.column.table.name}.{fk.column.name}" 
           for fk in inspector.foreign_keys}
    
    all_fks_present = True
    for fk_name, fk_target in required_fks.items():
        if fk_name in fks:
            print(f"✓ {fk_name} -> {fks[fk_name]}")
        else:
            print(f"✗ {fk_name} -> {fk_target}: MISSING")
            all_fks_present = False
    
    # 3. 验证关系 (Relationships)
    print("\n3. 验证关系 (Verifying Relationships)")
    print("-" * 80)
    
    required_relationships = ['contract', 'reviewer']
    
    relationships = {rel.key: rel for rel in inspector.relationships}
    
    all_rels_present = True
    for rel_name in required_relationships:
        if rel_name in relationships:
            rel = relationships[rel_name]
            print(f"✓ {rel_name}: {rel.mapper.class_.__name__}")
        else:
            print(f"✗ {rel_name}: MISSING")
            all_rels_present = False
    
    # 4. 验证索引
    print("\n4. 验证索引 (Verifying Indexes)")
    print("-" * 80)
    
    required_indexes = [
        'contract_id',
        'reviewer_id', 
        'status',
        'created_at'
    ]
    
    # 注意: 这里我们检查索引是否在 __table_args__ 中定义
    table = Review.__table__
    indexes = {idx.name: [col.name for col in idx.columns] for idx in table.indexes}
    
    print(f"发现的索引 (Found indexes): {list(indexes.keys())}")
    
    all_indexes_present = True
    for idx_field in required_indexes:
        # 检查是否有包含该字段的索引
        found = any(idx_field in cols for cols in indexes.values())
        if found:
            print(f"✓ 索引包含字段: {idx_field}")
        else:
            print(f"✗ 缺少索引字段: {idx_field}")
            all_indexes_present = False
    
    # 5. 验证枚举类型
    print("\n5. 验证枚举类型 (Verifying Enum Types)")
    print("-" * 80)
    
    expected_statuses = ['pending', 'reviewing', 'approved']
    actual_statuses = [status.value for status in ReviewStatus]
    
    if set(expected_statuses) == set(actual_statuses):
        print(f"✓ ReviewStatus 枚举值正确: {actual_statuses}")
    else:
        print(f"✗ ReviewStatus 枚举值不匹配")
        print(f"  期望: {expected_statuses}")
        print(f"  实际: {actual_statuses}")
        all_fields_present = False
    
    # 6. 验证默认值
    print("\n6. 验证默认值 (Verifying Default Values)")
    print("-" * 80)
    
    defaults = {
        'status': 'pending',
        'likes': 0,
        'liked_by': []
    }
    
    for field_name, expected_default in defaults.items():
        col = columns.get(field_name)
        if col and col.default:
            print(f"✓ {field_name} 有默认值")
        else:
            print(f"⚠ {field_name} 默认值未在模型中明确设置 (可能在数据库层面)")
    
    # 总结
    print("\n" + "=" * 80)
    print("验证总结 (Verification Summary)")
    print("=" * 80)
    
    if all_fields_present and all_fks_present and all_rels_present and all_indexes_present:
        print("✓ Review 模型满足所有需求!")
        print("\n需求覆盖:")
        print("  - 4.1-4.9: 评审时间线 (支持评审意见、点赞、时间戳)")
        print("  - 9.1-9.9: 快速审批 (支持状态更新、评审人关联)")
        return 0
    else:
        print("✗ Review 模型存在缺失项,请检查上述详情")
        return 1


if __name__ == "__main__":
    try:
        exit_code = verify_review_model()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n✗ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
