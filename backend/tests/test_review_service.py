"""
评审服务单元测试
Tests for ReviewService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from app.services.review_service import ReviewService
from app.models.review import Review, ReviewStatus
from app.models.comment import Comment
from app.models.user import User
from app.models.ai_summary import AISummary, ApprovalStatus


@pytest.fixture
def review_service():
    """创建ReviewService实例"""
    return ReviewService()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    return AsyncMock()


@pytest.fixture
def sample_user():
    """创建示例用户"""
    user = User(
        id=uuid.uuid4(),
        dingtalk_user_id="test_user_123",
        name="测试用户",
        role="法务"
    )
    return user


@pytest.fixture
def sample_review(sample_user):
    """创建示例评审记录"""
    review = Review(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        reviewer_id=sample_user.id,
        role="法务",
        step="法务初审",
        opinion="同意并通过",
        status=ReviewStatus.APPROVED,
        likes=0,
        liked_by=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    review.reviewer = sample_user
    review.comments = []
    return review


@pytest.fixture
def sample_comment(sample_user):
    """创建示例评论"""
    comment = Comment(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        author_id=sample_user.id,
        content="这是一条评论",
        likes=0,
        liked_by=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    comment.author = sample_user
    return comment


@pytest.fixture
def sample_ai_summary():
    """创建示例AI总结"""
    summary = AISummary(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        approval_status=ApprovalStatus.IN_PROGRESS,
        completed_count=2,
        total_count=5,
        review_count=3,
        key_issues=[
            {
                "issue": "需要补充合同条款",
                "reviewer": "法务",
                "solution": "已补充相关条款"
            }
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return summary


class TestGetContractReviews:
    """测试获取合同评审记录"""
    
    @pytest.mark.asyncio
    async def test_get_reviews_with_valid_opinion(
        self, 
        review_service, 
        mock_db, 
        sample_review
    ):
        """应该返回有有效意见的评审记录"""
        # 设置模拟返回
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_review]
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 调用方法
        reviews = await review_service.get_contract_reviews(
            str(sample_review.contract_id),
            mock_db
        )
        
        # 验证结果
        assert len(reviews) == 1
        assert reviews[0].opinion == "同意并通过"
    
    @pytest.mark.asyncio
    async def test_filter_placeholder_opinions(
        self, 
        review_service, 
        mock_db, 
        sample_review
    ):
        """应该过滤占位文本的评审记录"""
        # 创建带占位文本的评审
        sample_review.opinion = "待评审"
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_review]
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 调用方法
        reviews = await review_service.get_contract_reviews(
            str(sample_review.contract_id),
            mock_db
        )
        
        # 验证结果 - 应该被过滤掉
        assert len(reviews) == 0
    
    @pytest.mark.asyncio
    async def test_keep_review_with_comments(
        self, 
        review_service, 
        mock_db, 
        sample_review,
        sample_comment
    ):
        """应该保留没有意见但有回复的评审记录"""
        # 设置评审没有意见但有评论
        sample_review.opinion = None
        sample_review.comments = [sample_comment]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_review]
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 调用方法
        reviews = await review_service.get_contract_reviews(
            str(sample_review.contract_id),
            mock_db
        )
        
        # 验证结果 - 应该保留
        assert len(reviews) == 1


class TestApproveReview:
    """测试同意评审"""
    
    @pytest.mark.asyncio
    async def test_approve_review_success(
        self, 
        review_service, 
        mock_db, 
        sample_review,
        sample_user
    ):
        """应该成功同意评审"""
        # 设置评审为待处理状态
        sample_review.status = ReviewStatus.PENDING
        
        # 模拟数据库查询
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_review
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Mock缓存清除和状态检查
        with patch.object(review_service, '_check_and_update_contract_status', new=AsyncMock()):
            with patch.object(review_service, '_clear_review_cache', new=AsyncMock()):
                with patch.object(review_service, '_clear_pending_count_cache', new=AsyncMock()):
                    # 调用方法
                    result = await review_service.approve_review(
                        str(sample_review.id),
                        str(sample_user.id),
                        "同意并通过",
                        mock_db
                    )
        
        # 验证结果
        assert result.status == ReviewStatus.APPROVED
        assert result.opinion == "同意并通过"
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_review_not_found(
        self, 
        review_service, 
        mock_db
    ):
        """当评审不存在时应该抛出异常"""
        # 模拟评审不存在
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 调用方法并验证异常
        with pytest.raises(ValueError, match="评审记录不存在"):
            await review_service.approve_review(
                str(uuid.uuid4()),
                str(uuid.uuid4()),
                "同意",
                mock_db
            )
    
    @pytest.mark.asyncio
    async def test_approve_review_permission_denied(
        self, 
        review_service, 
        mock_db, 
        sample_review
    ):
        """当用户不是评审人时应该抛出异常"""
        # 模拟数据库查询
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_review
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 使用不同的用户ID
        wrong_user_id = uuid.uuid4()
        
        # 调用方法并验证异常
        with pytest.raises(ValueError, match="您没有权限审批此评审项"):
            await review_service.approve_review(
                str(sample_review.id),
                str(wrong_user_id),
                "同意",
                mock_db
            )


class TestLikeReview:
    """测试点赞评审"""
    
    @pytest.mark.asyncio
    async def test_like_review(
        self, 
        review_service, 
        mock_db, 
        sample_review
    ):
        """应该成功点赞评审"""
        user_id = str(uuid.uuid4())
        
        # 模拟数据库查询
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_review
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 调用方法
        result = await review_service.like_review(
            str(sample_review.id),
            user_id,
            mock_db
        )
        
        # 验证结果
        assert result.likes == 1
        assert user_id in result.liked_by
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unlike_review(
        self, 
        review_service, 
        mock_db, 
        sample_review
    ):
        """应该成功取消点赞"""
        user_id = str(uuid.uuid4())
        
        # 设置已点赞状态
        sample_review.likes = 1
        sample_review.liked_by = [user_id]
        
        # 模拟数据库查询
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_review
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 调用方法
        result = await review_service.like_review(
            str(sample_review.id),
            user_id,
            mock_db
        )
        
        # 验证结果
        assert result.likes == 0
        assert user_id not in result.liked_by


class TestAddComment:
    """测试添加评论"""
    
    @pytest.mark.asyncio
    async def test_add_comment_to_review(
        self, 
        review_service, 
        mock_db
    ):
        """应该成功添加评论到评审"""
        contract_id = str(uuid.uuid4())
        author_id = str(uuid.uuid4())
        review_id = str(uuid.uuid4())
        content = "这是一条评论"
        
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        with patch.object(review_service, '_clear_review_cache', new=AsyncMock()):
            # 调用方法
            result = await review_service.add_comment(
                contract_id,
                author_id,
                content,
                review_id=review_id,
                db=mock_db
            )
        
        # 验证结果
        assert result.content == content
        assert str(result.contract_id) == contract_id
        assert str(result.review_id) == review_id
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_nested_reply(
        self, 
        review_service, 
        mock_db
    ):
        """应该成功添加嵌套回复"""
        contract_id = str(uuid.uuid4())
        author_id = str(uuid.uuid4())
        parent_comment_id = str(uuid.uuid4())
        content = "这是一条回复"
        
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        with patch.object(review_service, '_clear_review_cache', new=AsyncMock()):
            # 调用方法
            result = await review_service.add_comment(
                contract_id,
                author_id,
                content,
                parent_comment_id=parent_comment_id,
                db=mock_db
            )
        
        # 验证结果
        assert result.content == content
        assert str(result.parent_comment_id) == parent_comment_id


class TestLikeComment:
    """测试点赞评论"""
    
    @pytest.mark.asyncio
    async def test_like_comment(
        self, 
        review_service, 
        mock_db, 
        sample_comment
    ):
        """应该成功点赞评论"""
        user_id = str(uuid.uuid4())
        
        # 模拟数据库查询
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_comment
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 调用方法
        result = await review_service.like_comment(
            str(sample_comment.id),
            user_id,
            mock_db
        )
        
        # 验证结果
        assert result.likes == 1
        assert user_id in result.liked_by
    
    @pytest.mark.asyncio
    async def test_unlike_comment(
        self, 
        review_service, 
        mock_db, 
        sample_comment
    ):
        """应该成功取消点赞评论"""
        user_id = str(uuid.uuid4())
        
        # 设置已点赞状态
        sample_comment.likes = 1
        sample_comment.liked_by = [user_id]
        
        # 模拟数据库查询
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_comment
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 调用方法
        result = await review_service.like_comment(
            str(sample_comment.id),
            user_id,
            mock_db
        )
        
        # 验证结果
        assert result.likes == 0
        assert user_id not in result.liked_by
    
    @pytest.mark.asyncio
    async def test_like_comment_not_found(
        self, 
        review_service, 
        mock_db
    ):
        """当评论不存在时应该抛出异常"""
        # 模拟评论不存在
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 调用方法并验证异常
        with pytest.raises(ValueError, match="评论不存在"):
            await review_service.like_comment(
                str(uuid.uuid4()),
                str(uuid.uuid4()),
                mock_db
            )



class TestGetAISummary:
    """测试获取AI智能总结"""
    
    @pytest.mark.asyncio
    async def test_get_ai_summary_exists(
        self, 
        review_service, 
        mock_db, 
        sample_ai_summary
    ):
        """应该返回存在的AI总结"""
        # 模拟数据库查询
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_ai_summary
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 调用方法
        result = await review_service.get_ai_summary(
            str(sample_ai_summary.contract_id),
            mock_db
        )
        
        # 验证结果
        assert result is not None
        assert result["approvalStatus"] == "in_progress"
        assert result["completedCount"] == 2
        assert result["totalCount"] == 5
        assert result["reviewCount"] == 3
        assert len(result["keyIssues"]) == 1
        assert result["keyIssues"][0]["issue"] == "需要补充合同条款"
    
    @pytest.mark.asyncio
    async def test_get_ai_summary_not_exists(
        self, 
        review_service, 
        mock_db
    ):
        """当AI总结不存在时应该返回None"""
        # 模拟AI总结不存在
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 调用方法
        result = await review_service.get_ai_summary(
            str(uuid.uuid4()),
            mock_db
        )
        
        # 验证结果
        assert result is None
