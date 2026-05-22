"""
测试评论模型
Test Comment model
"""

import pytest
import uuid
from datetime import datetime
from app.models.comment import Comment


class TestCommentModel:
    """测试评论模型的基本功能"""
    
    def test_comment_creation(self):
        """测试创建评论实例"""
        comment_id = uuid.uuid4()
        contract_id = uuid.uuid4()
        author_id = uuid.uuid4()
        
        comment = Comment(
            id=comment_id,
            contract_id=contract_id,
            author_id=author_id,
            content="这是一条测试评论",
            likes=0,
            liked_by=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert comment.id == comment_id
        assert comment.contract_id == contract_id
        assert comment.author_id == author_id
        assert comment.content == "这是一条测试评论"
        assert comment.likes == 0
        assert comment.liked_by == []
        assert comment.review_id is None
        assert comment.parent_comment_id is None
    
    def test_comment_with_review(self):
        """测试关联评审记录的评论"""
        comment_id = uuid.uuid4()
        contract_id = uuid.uuid4()
        review_id = uuid.uuid4()
        author_id = uuid.uuid4()
        
        comment = Comment(
            id=comment_id,
            contract_id=contract_id,
            review_id=review_id,
            author_id=author_id,
            content="回复评审意见",
            likes=0,
            liked_by=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert comment.review_id == review_id
        assert comment.parent_comment_id is None
    
    def test_nested_reply(self):
        """测试嵌套回复"""
        comment_id = uuid.uuid4()
        contract_id = uuid.uuid4()
        parent_comment_id = uuid.uuid4()
        author_id = uuid.uuid4()
        
        reply = Comment(
            id=comment_id,
            contract_id=contract_id,
            parent_comment_id=parent_comment_id,
            author_id=author_id,
            content="这是一条嵌套回复",
            likes=0,
            liked_by=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert reply.parent_comment_id == parent_comment_id
        assert reply.review_id is None
    
    def test_comment_likes(self):
        """测试评论点赞功能"""
        comment_id = uuid.uuid4()
        contract_id = uuid.uuid4()
        author_id = uuid.uuid4()
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        comment = Comment(
            id=comment_id,
            contract_id=contract_id,
            author_id=author_id,
            content="测试点赞",
            likes=2,
            liked_by=[user1_id, user2_id],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert comment.likes == 2
        assert len(comment.liked_by) == 2
        assert user1_id in comment.liked_by
        assert user2_id in comment.liked_by
    
    def test_comment_repr(self):
        """测试评论的字符串表示"""
        comment_id = uuid.uuid4()
        contract_id = uuid.uuid4()
        author_id = uuid.uuid4()
        
        comment = Comment(
            id=comment_id,
            contract_id=contract_id,
            author_id=author_id,
            content="测试repr",
            likes=0,
            liked_by=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        repr_str = repr(comment)
        assert "Comment" in repr_str
        assert str(comment_id) in repr_str
        assert str(contract_id) in repr_str
        assert str(author_id) in repr_str
    
    def test_comment_table_name(self):
        """测试表名"""
        assert Comment.__tablename__ == "comments"
    
    def test_comment_default_values(self):
        """测试默认值"""
        comment_id = uuid.uuid4()
        contract_id = uuid.uuid4()
        author_id = uuid.uuid4()
        
        comment = Comment(
            id=comment_id,
            contract_id=contract_id,
            author_id=author_id,
            content="测试默认值"
        )
        
        # 默认值应该在数据库层面设置,这里只测试模型定义
        assert hasattr(comment, 'likes')
        assert hasattr(comment, 'liked_by')
        assert hasattr(comment, 'created_at')
        assert hasattr(comment, 'updated_at')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
