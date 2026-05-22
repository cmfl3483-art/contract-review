"""
验证数据库模型脚本
Verify database models script
"""

import asyncio
from sqlalchemy import inspect, text
from app.core.database import engine


async def verify_database_models():
    """验证数据库模型是否正确创建"""
    
    print("=" * 60)
    print("数据库模型验证 / Database Models Verification")
    print("=" * 60)
    
    async with engine.begin() as conn:
        # 获取所有表名
        result = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        tables = sorted(result)
        
        print(f"\n✓ 数据库中的表 ({len(tables)} 个):")
        for table in tables:
            print(f"  - {table}")
        
        # 验证每个表的结构
        print("\n" + "=" * 60)
        print("表结构验证 / Table Structure Verification")
        print("=" * 60)
        
        expected_tables = {
            'users': [
                'id', 'dingtalk_user_id', 'dingtalk_union_id', 'name', 
                'role', 'email', 'mobile', 'avatar', 'department',
                'created_at', 'updated_at'
            ],
            'contracts': [
                'id', 'name', 'description', 'status', 'initiator_id',
                'cc_users', 'version', 'created_at', 'updated_at'
            ],
            'reviews': [
                'id', 'contract_id', 'reviewer_id', 'role', 'step',
                'opinion', 'status', 'likes', 'liked_by',
                'created_at', 'updated_at'
            ],
            'comments': [
                'id', 'contract_id', 'review_id', 'parent_comment_id',
                'author_id', 'content', 'likes', 'liked_by',
                'created_at', 'updated_at'
            ],
            'attachments': [
                'id', 'contract_id', 'file_name', 'version', 'file_size',
                'mime_type', 'storage_key', 'uploader_id', 'created_at'
            ],
            'ai_summaries': [
                'id', 'contract_id', 'approval_status', 'completed_count',
                'total_count', 'review_count', 'key_issues',
                'created_at', 'updated_at'
            ]
        }
        
        all_passed = True
        
        for table_name, expected_columns in expected_tables.items():
            if table_name not in tables:
                print(f"\n✗ 表 '{table_name}' 不存在!")
                all_passed = False
                continue
            
            # 获取表的列信息
            columns = await conn.run_sync(
                lambda sync_conn: [
                    col['name'] 
                    for col in inspect(sync_conn).get_columns(table_name)
                ]
            )
            
            print(f"\n表: {table_name}")
            print(f"  预期列数: {len(expected_columns)}")
            print(f"  实际列数: {len(columns)}")
            
            # 检查缺失的列
            missing_columns = set(expected_columns) - set(columns)
            if missing_columns:
                print(f"  ✗ 缺失的列: {', '.join(missing_columns)}")
                all_passed = False
            
            # 检查额外的列
            extra_columns = set(columns) - set(expected_columns)
            if extra_columns:
                print(f"  ⚠ 额外的列: {', '.join(extra_columns)}")
            
            if not missing_columns and not extra_columns:
                print(f"  ✓ 所有列都正确")
            
            # 获取索引信息
            indexes = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_indexes(table_name)
            )
            print(f"  索引数量: {len(indexes)}")
            
            # 获取外键信息
            foreign_keys = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_foreign_keys(table_name)
            )
            if foreign_keys:
                print(f"  外键数量: {len(foreign_keys)}")
        
        print("\n" + "=" * 60)
        print("索引验证 / Index Verification")
        print("=" * 60)
        
        # 验证关键索引
        for table_name in expected_tables.keys():
            if table_name not in tables:
                continue
                
            indexes = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_indexes(table_name)
            )
            
            print(f"\n表 {table_name} 的索引:")
            for idx in indexes:
                columns_str = ', '.join(idx['column_names'])
                unique_str = " (UNIQUE)" if idx.get('unique') else ""
                print(f"  - {idx['name']}: [{columns_str}]{unique_str}")
        
        print("\n" + "=" * 60)
        print("外键约束验证 / Foreign Key Verification")
        print("=" * 60)
        
        # 验证外键约束
        for table_name in expected_tables.keys():
            if table_name not in tables:
                continue
                
            foreign_keys = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_foreign_keys(table_name)
            )
            
            if foreign_keys:
                print(f"\n表 {table_name} 的外键:")
                for fk in foreign_keys:
                    print(f"  - {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        
        print("\n" + "=" * 60)
        if all_passed:
            print("✓ 所有数据库模型验证通过!")
        else:
            print("✗ 数据库模型验证失败,请检查上述错误")
        print("=" * 60)
        
        return all_passed


if __name__ == "__main__":
    result = asyncio.run(verify_database_models())
    exit(0 if result else 1)
