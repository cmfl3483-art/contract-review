"""
点赞 API 测试
测试评审意见和评论的点赞功能
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.user import User
from app.models.contract import Contract
from app.models.review import Review, ReviewStatus
from app.models.comment import Comment


@pytest.mark.asyncio
class TestLikeAPI:
    """点赞 API 测试类"""
    
    async def test_like_review_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_contract: Contract,
        test_review: Review,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """测试点赞评审意见成功"""
        # 点赞评审
        response = await async_client.post(
            f"/api/reviews/{test_review.id}/like",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["likes"] == 1
        
        # 验证数据库中的点赞数
        await db_session.refresh(test_review)
        assert test_review.likes == 1
        assert str(test_user.id) in test_review.liked_by
    
    async def test_unlike_review_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_contract: Contract,
        test_review: Review,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """测试取消点赞评审意见成功"""
        # 先点赞
        test_review.likes = 1
        test_review.liked_by = [str(test_user.id)]
        await db_session.commit()
        
        # 取消点赞
        response = await async_client.post(
            f"/api/reviews/{test_review.id}/like",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["likes"] == 0
        
        # 验证数据库中的点赞数
        await db_session.refresh(test_review)
        assert test_review.likes == 0
        assert str(test_user.id) not in test_review.liked_by
    
    async def test_like_review_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """测试点赞不存在的评审意见"""
        fake_review_id = str(uuid4())
        
        response = await async_client.post(
            f"/api/reviews/{fake_review_id}/like",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "不存在" in data["detail"]
    
    async def test_like_review_unauthorized(
        self,
        async_client: AsyncClient,
        test_review: Review
    ):
        """测试未授权点赞评审意见"""
        response = await async_client.post(
            f"/api/reviews/{test_review.id}/like"
        )
        
        assert response.status_code == 401
    
    async def test_like_comment_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_contract: Contract,
        test_comment: Comment,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """测试点赞评论成功"""
        # 点赞评论
        response = await async_client.post(
            f"/api/comments/{test_comment.id}/like",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["likes"] == 1
        
        # 验证数据库中的点赞数
        await db_session.refresh(test_comment)
        assert test_comment.likes == 1
        assert str(test_user.id) in test_comment.liked_by
    
    async def test_unlike_comment_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_contract: Contract,
        test_comment: Comment,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """测试取消点赞评论成功"""
        # 先点赞
        test_comment.likes = 1
        test_comment.liked_by = [str(test_user.id)]
        await db_session.commit()
        
        # 取消点赞
        response = await async_client.post(
            f"/api/comments/{test_comment.id}/like",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["likes"] == 0
        
        # 验证数据库中的点赞数
        await db_session.refresh(test_comment)
        assert test_comment.likes == 0
        assert str(test_user.id) not in test_comment.liked_by
    
    async def test_like_comment_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """测试点赞不存在的评论"""
        fake_comment_id = str(uuid4())
        
        response = await async_client.post(
            f"/api/comments/{fake_comment_id}/like",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "不存在" in data["detail"]
    
    async def test_like_comment_unauthorized(
        self,
        async_client: AsyncClient,
        test_comment: Comment
    ):
        """测试未授权点赞评论"""
        response = await async_client.post(
            f"/api/comments/{test_comment.id}/like"
        )
        
        assert response.status_code == 401
    
    async def test_multiple_users_like_review(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_contract: Contract,
        test_review: Review,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """测试多个用户点赞同一评审意见"""
        # 第一个用户点赞
        response = await async_client.post(
            f"/api/reviews/{test_review.id}/like",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["likes"] == 1
        
        # 模拟第二个用户点赞
        test_review.likes = 2
        test_review.liked_by = [str(test_user.id), str(uuid4())]
        await db_session.commit()
        await db_session.refresh(test_review)
        
        assert test_review.likes == 2
        assert len(test_review.liked_by) == 2
    
    async def test_like_review_toggle(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_contract: Contract,
        test_review: Review,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """测试点赞切换功能"""
        # 第一次点赞
        response1 = await async_client.post(
            f"/api/reviews/{test_review.id}/like",
            headers=auth_headers
        )
        assert response1.json()["data"]["likes"] == 1
        
        # 第二次点赞(取消)
        response2 = await async_client.post(
            f"/api/reviews/{test_review.id}/like",
            headers=auth_headers
        )
        assert response2.json()["data"]["likes"] == 0
        
        # 第三次点赞(再次点赞)
        response3 = await async_client.post(
            f"/api/reviews/{test_review.id}/like",
            headers=auth_headers
        )
        assert response3.json()["data"]["likes"] == 1
