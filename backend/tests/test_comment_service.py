"""
评论服务单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from app.services.comment_service import CommentService
from app.models.comment import Comment
from app.models.contract import Contract
from app.models.user import User


@pytest.fixture
def comment_service():
    """创建评论服务实例"""
    return CommentService()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    return AsyncMock()


@pytest.fixture
def mock_contract():
    """创建模拟合同对象"""
    contract = MagicMock(spec=Contract)
    contract.id = uuid.uuid4()
    contract.name = "测试合同"
    contract.status = "progress"
    return contract


@pytest.fixture
def mock_user():
    """创建模拟用户对象"""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.name = "张三"
    user.role = "法务"
    return user


@pytest.fixture
def mock_comment(mock_user, mock_contract):
    """创建模拟评论对象"""
    comment = MagicMock(spec=Comment)
    comment.id = uuid.uuid4()
    comment.contract_id = mock_contract.id
    comment.author_id = mock_user.id
    comment.content = "这是一条测试评论"
    comment.likes = 0
    comment.liked_by = []
    comment.review_id = None
    comment.parent_comment_id = None
    comment.created_at = datetime.utcnow()
    comment.updated_at = datetime.utcnow()
    comment.author = mock_user
    return comment


class TestCommentService:
    """评论服务测试类"""
    
    @pytest.mark.asyncio
    async def test_create_comment_success(
        self,
        comment_service,
        mock_db,
        mock_contract,
        mock_user
    ):
        """测试成功创建评论"""
        # 模拟数据库查询返回合同
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_contract
        mock_db.execute.return_value = mock_result
        
        # 模拟数据库操作
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 模拟Redis缓存清除
        with patch.object(comment_service, '_clear_review_cache', new=AsyncMock()):
            # 调用创建评论方法
            comment = await comment_service.create_comment(
                contract_id=str(mock_contract.id),
                author_id=str(mock_user.id),
                content="测试评论内容",
                db=mock_db
            )
            
            # 验证数据库操作被调用
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
            
            # 验证评论对象
            assert isinstance(comment, Comment)
            assert comment.content == "测试评论内容"
    
    @pytest.mark.asyncio
    async def test_create_comment_contract_not_found(
        self,
        comment_service,
        mock_db,
        mock_user
    ):
        """测试创建评论时合同不存在"""
        # 模拟数据库查询返回None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # 验证抛出异常
        with pytest.raises(ValueError, match="合同不存在"):
            await comment_service.create_comment(
                contract_id=str(uuid.uuid4()),
                author_id=str(mock_user.id),
                content="测试评论内容",
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_create_comment_with_review_id(
        self,
        comment_service,
        mock_db,
        mock_contract,
        mock_user
    ):
        """测试创建回复评审意见的评论"""
        review_id = str(uuid.uuid4())
        
        # 模拟数据库查询返回合同
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_contract
        mock_db.execute.return_value = mock_result
        
        # 模拟数据库操作
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 模拟Redis缓存清除
        with patch.object(comment_service, '_clear_review_cache', new=AsyncMock()):
            # 调用创建评论方法
            comment = await comment_service.create_comment(
                contract_id=str(mock_contract.id),
                author_id=str(mock_user.id),
                content="回复评审意见",
                review_id=review_id,
                db=mock_db
            )
            
            # 验证评论对象
            assert isinstance(comment, Comment)
            assert comment.review_id == uuid.UUID(review_id)
    
    @pytest.mark.asyncio
    async def test_create_comment_with_parent_comment_id(
        self,
        comment_service,
        mock_db,
        mock_contract,
        mock_user
    ):
        """测试创建嵌套回复"""
        parent_comment_id = str(uuid.uuid4())
        
        # 模拟数据库查询返回合同
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_contract
        mock_db.execute.return_value = mock_result
        
        # 模拟数据库操作
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 模拟Redis缓存清除
        with patch.object(comment_service, '_clear_review_cache', new=AsyncMock()):
            # 调用创建评论方法
            comment = await comment_service.create_comment(
                contract_id=str(mock_contract.id),
                author_id=str(mock_user.id),
                content="嵌套回复",
                parent_comment_id=parent_comment_id,
                db=mock_db
            )
            
            # 验证评论对象
            assert isinstance(comment, Comment)
            assert comment.parent_comment_id == uuid.UUID(parent_comment_id)
    
    @pytest.mark.asyncio
    async def test_get_comment_by_id_success(
        self,
        comment_service,
        mock_db,
        mock_comment
    ):
        """测试根据ID获取评论成功"""
        # 模拟数据库查询返回评论
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_comment
        mock_db.execute.return_value = mock_result
        
        # 调用获取评论方法
        comment = await comment_service.get_comment_by_id(
            comment_id=str(mock_comment.id),
            db=mock_db
        )
        
        # 验证返回的评论
        assert comment == mock_comment
    
    @pytest.mark.asyncio
    async def test_get_comment_by_id_not_found(
        self,
        comment_service,
        mock_db
    ):
        """测试根据ID获取评论不存在"""
        # 模拟数据库查询返回None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # 调用获取评论方法
        comment = await comment_service.get_comment_by_id(
            comment_id=str(uuid.uuid4()),
            db=mock_db
        )
        
        # 验证返回None
        assert comment is None
    
    @pytest.mark.asyncio
    async def test_get_comments_by_contract(
        self,
        comment_service,
        mock_db,
        mock_comment
    ):
        """测试获取合同的所有评论"""
        # 模拟数据库查询返回评论列表
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [mock_comment]
        mock_db.execute.return_value = mock_result
        
        # 调用获取评论方法
        comments = await comment_service.get_comments_by_contract(
            contract_id=str(mock_comment.contract_id),
            db=mock_db
        )
        
        # 验证返回的评论列表
        assert len(comments) == 1
        assert comments[0] == mock_comment
    
    @pytest.mark.asyncio
    async def test_update_comment_success(
        self,
        comment_service,
        mock_db,
        mock_comment,
        mock_user
    ):
        """测试成功更新评论"""
        # 模拟数据库查询返回评论
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_comment
        mock_db.execute.return_value = mock_result
        
        # 模拟数据库操作
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 模拟Redis缓存清除
        with patch.object(comment_service, '_clear_review_cache', new=AsyncMock()):
            # 调用更新评论方法
            updated_comment = await comment_service.update_comment(
                comment_id=str(mock_comment.id),
                author_id=str(mock_user.id),
                content="更新后的评论内容",
                db=mock_db
            )
            
            # 验证数据库操作被调用
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
            
            # 验证评论内容被更新
            assert mock_comment.content == "更新后的评论内容"
    
    @pytest.mark.asyncio
    async def test_update_comment_not_found(
        self,
        comment_service,
        mock_db,
        mock_user
    ):
        """测试更新不存在的评论"""
        # 模拟数据库查询返回None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # 验证抛出异常
        with pytest.raises(ValueError, match="评论不存在"):
            await comment_service.update_comment(
                comment_id=str(uuid.uuid4()),
                author_id=str(mock_user.id),
                content="更新后的评论内容",
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_update_comment_permission_denied(
        self,
        comment_service,
        mock_db,
        mock_comment
    ):
        """测试更新评论权限不足"""
        # 模拟数据库查询返回评论
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_comment
        mock_db.execute.return_value = mock_result
        
        # 使用不同的用户ID
        other_user_id = str(uuid.uuid4())
        
        # 验证抛出异常
        with pytest.raises(ValueError, match="您没有权限修改此评论"):
            await comment_service.update_comment(
                comment_id=str(mock_comment.id),
                author_id=other_user_id,
                content="更新后的评论内容",
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_delete_comment_success(
        self,
        comment_service,
        mock_db,
        mock_comment,
        mock_user
    ):
        """测试成功删除评论"""
        # 模拟数据库查询返回评论
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_comment
        mock_db.execute.return_value = mock_result
        
        # 模拟数据库操作
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()
        
        # 模拟Redis缓存清除
        with patch.object(comment_service, '_clear_review_cache', new=AsyncMock()):
            # 调用删除评论方法
            result = await comment_service.delete_comment(
                comment_id=str(mock_comment.id),
                author_id=str(mock_user.id),
                db=mock_db
            )
            
            # 验证数据库操作被调用
            mock_db.delete.assert_called_once_with(mock_comment)
            mock_db.commit.assert_called_once()
            
            # 验证返回True
            assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_comment_not_found(
        self,
        comment_service,
        mock_db,
        mock_user
    ):
        """测试删除不存在的评论"""
        # 模拟数据库查询返回None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # 验证抛出异常
        with pytest.raises(ValueError, match="评论不存在"):
            await comment_service.delete_comment(
                comment_id=str(uuid.uuid4()),
                author_id=str(mock_user.id),
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_delete_comment_permission_denied(
        self,
        comment_service,
        mock_db,
        mock_comment
    ):
        """测试删除评论权限不足"""
        # 模拟数据库查询返回评论
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_comment
        mock_db.execute.return_value = mock_result
        
        # 使用不同的用户ID
        other_user_id = str(uuid.uuid4())
        
        # 验证抛出异常
        with pytest.raises(ValueError, match="您没有权限删除此评论"):
            await comment_service.delete_comment(
                comment_id=str(mock_comment.id),
                author_id=other_user_id,
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_like_comment_success(
        self,
        comment_service,
        mock_db,
        mock_comment,
        mock_user
    ):
        """测试成功点赞评论"""
        # 模拟数据库查询返回评论
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_comment
        mock_db.execute.return_value = mock_result
        
        # 模拟数据库操作
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 调用点赞方法
        liked_comment = await comment_service.like_comment(
            comment_id=str(mock_comment.id),
            user_id=str(mock_user.id),
            db=mock_db
        )
        
        # 验证点赞数增加
        assert mock_comment.likes == 1
        assert str(mock_user.id) in mock_comment.liked_by
        
        # 验证数据库操作被调用
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unlike_comment_success(
        self,
        comment_service,
        mock_db,
        mock_comment,
        mock_user
    ):
        """测试成功取消点赞评论"""
        # 设置评论已被点赞
        mock_comment.likes = 1
        mock_comment.liked_by = [str(mock_user.id)]
        
        # 模拟数据库查询返回评论
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_comment
        mock_db.execute.return_value = mock_result
        
        # 模拟数据库操作
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 调用点赞方法(取消点赞)
        unliked_comment = await comment_service.like_comment(
            comment_id=str(mock_comment.id),
            user_id=str(mock_user.id),
            db=mock_db
        )
        
        # 验证点赞数减少
        assert mock_comment.likes == 0
        assert str(mock_user.id) not in mock_comment.liked_by
        
        # 验证数据库操作被调用
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_like_comment_not_found(
        self,
        comment_service,
        mock_db,
        mock_user
    ):
        """测试点赞不存在的评论"""
        # 模拟数据库查询返回None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # 验证抛出异常
        with pytest.raises(ValueError, match="评论不存在"):
            await comment_service.like_comment(
                comment_id=str(uuid.uuid4()),
                user_id=str(mock_user.id),
                db=mock_db
            )
