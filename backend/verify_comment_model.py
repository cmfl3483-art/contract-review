#!/usr/bin/env python3
"""
验证 Comment 模型定义
Verify Comment model definition without database connection
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def verify_comment_model():
    """验证 Comment 模型的定义"""
    print("=" * 60)
    print("验证 Comment 模型定义")
    print("=" * 60)
    
    try:
        # 导入模型(不需要数据库连接)
        from app.models.comment import Comment
        print("✅ Comment 模型导入成功")
        
        # 验证表名
        assert Comment.__tablename__ == "comments", "表名不正确"
        print(f"✅ 表名正确: {Comment.__tablename__}")
        
        # 验证字段存在
        required_fields = [
            'id', 'contract_id', 'review_id', 'parent_comment_id',
            'author_id', 'content', 'likes', 'liked_by',
            'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            assert hasattr(Comment, field), f"缺少字段: {field}"
        print(f"✅ 所有必需字段存在: {', '.join(required_fields)}")
        
        # 验证关系定义
        relationships = ['contract', 'review', 'author', 'parent_comment']
        for rel in relationships:
            assert hasattr(Comment, rel), f"缺少关系: {rel}"
        print(f"✅ 所有关系定义存在: {', '.join(relationships)}")
        
        # 验证字段类型注解
        annotations = Comment.__annotations__
        print(f"✅ 字段类型注解数量: {len(annotations)}")
        
        # 验证索引配置
        if hasattr(Comment, '__table_args__'):
            print(f"✅ 索引配置存在: {len(Comment.__table_args__)} 个索引")
        
        # 验证 repr 方法
        assert hasattr(Comment, '__repr__'), "缺少 __repr__ 方法"
        print("✅ __repr__ 方法已定义")
        
        print("\n" + "=" * 60)
        print("✅ Comment 模型验证通过!")
        print("=" * 60)
        
        # 打印模型详细信息
        print("\n模型详细信息:")
        print(f"  表名: {Comment.__tablename__}")
        print(f"  字段数量: {len(required_fields)}")
        print(f"  关系数量: {len(relationships)}")
        print(f"  支持功能:")
        print(f"    - 独立评论 (contract_id)")
        print(f"    - 评审回复 (review_id)")
        print(f"    - 嵌套回复 (parent_comment_id)")
        print(f"    - 点赞功能 (likes, liked_by)")
        print(f"    - 时间戳 (created_at, updated_at)")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("提示: 请确保已安装依赖 (poetry install 或 pip install -r requirements.txt)")
        return False
    except AssertionError as e:
        print(f"❌ 验证失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_model_export():
    """验证模型是否正确导出"""
    print("\n" + "=" * 60)
    print("验证模型导出")
    print("=" * 60)
    
    try:
        from app.models import Comment
        print("✅ Comment 从 app.models 导入成功")
        
        # 验证 __all__ 列表
        from app.models import __all__
        assert 'Comment' in __all__, "Comment 未在 __all__ 中"
        print("✅ Comment 已在 __all__ 中导出")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except AssertionError as e:
        print(f"❌ 验证失败: {e}")
        return False


def verify_migration_file():
    """验证数据库迁移文件"""
    print("\n" + "=" * 60)
    print("验证数据库迁移文件")
    print("=" * 60)
    
    migration_file = "alembic/versions/001_create_initial_database_models.py"
    
    if not os.path.exists(migration_file):
        print(f"❌ 迁移文件不存在: {migration_file}")
        return False
    
    print(f"✅ 迁移文件存在: {migration_file}")
    
    # 读取迁移文件内容
    with open(migration_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 验证 comments 表定义
    checks = [
        ("'comments'", "comments 表定义"),
        ("contract_id", "contract_id 字段"),
        ("review_id", "review_id 字段"),
        ("parent_comment_id", "parent_comment_id 字段"),
        ("author_id", "author_id 字段"),
        ("content", "content 字段"),
        ("likes", "likes 字段"),
        ("liked_by", "liked_by 字段"),
        ("ix_comments_contract_id", "contract_id 索引"),
        ("ix_comments_review_id", "review_id 索引"),
        ("ix_comments_parent_comment_id", "parent_comment_id 索引"),
        ("ix_comments_created_at_desc", "created_at 倒序索引"),
    ]
    
    all_passed = True
    for check_str, description in checks:
        if check_str in content:
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ 缺少: {description}")
            all_passed = False
    
    if all_passed:
        print("✅ 迁移文件验证通过")
    else:
        print("❌ 迁移文件验证失败")
    
    return all_passed


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Task 2.4 - Comment 模型验证")
    print("=" * 60 + "\n")
    
    results = []
    
    # 验证模型定义
    results.append(("模型定义", verify_comment_model()))
    
    # 验证模型导出
    results.append(("模型导出", verify_model_export()))
    
    # 验证迁移文件
    results.append(("迁移文件", verify_migration_file()))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有验证通过! Comment 模型已正确实现")
    else:
        print("⚠️  部分验证失败,请检查上述错误")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
