"""
评论服务层
实现评论CRUD功能
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid

from app.models.comment import Comment
from app.models.contract import Contract
from app.models.user import User
from app.core.redis_client import redis_client
from app.services.notification_service import notification_service
from app.utils.cache_invalidation import cache_invalidation


class CommentService:
    """评论服务类"""
    
    async def create_comment(
        self,
        contract_id: str,
        author_id: str,
        content: str,
        review_id: Optional[str] = None,
        parent_comment_id: Optional[str] = None,
        db: AsyncSession = None
    ) -> Comment:
        """
        创建评论
        
        Args:
            contract_id: 合同ID
            author_id: 作者ID
            content: 评论内容
            review_id: 评审ID(可选,回复评审意见时提供)
            parent_comment_id: 父评论ID(可选,嵌套回复时提供)
            db: 数据库会话
            
        Returns:
            创建的评论对象
            
        Raises:
            ValueError: 如果合同不存在
        """
        # 验证合同是否存在
        contract_query = select(Contract).where(Contract.id == contract_id)
        contract_result = await db.execute(contract_query)
        contract = contract_result.scalar_one_or_none()
        
        if not contract:
            raise ValueError("合同不存在")
        
        # 创建评论
        comment = Comment(
            id=uuid.uuid4(),
            contract_id=uuid.UUID(contract_id),
            review_id=uuid.UUID(review_id) if review_id else None,
            parent_comment_id=uuid.UUID(parent_comment_id) if parent_comment_id else None,
            author_id=uuid.UUID(author_id),
            content=content,
            likes=0,
            liked_by=[]
        )
        
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        
        # 加载关联数据以便发送通知
        await db.refresh(comment, ["author"])
        
        # 清除缓存 - 使用统一的缓存失效策略
        await cache_invalidation.invalidate_comment_added(contract_id)
        
        # 发送实时通知
        if parent_comment_id:
            # 嵌套回复 - 发送 reply:added 事件
            await notification_service.notify_reply_added(
                contract_id=contract_id,
                reply_data={
                    "id": str(comment.id),
                    "contract_id": contract_id,
                    "parent_comment_id": str(parent_comment_id),
                    "author_id": str(comment.author_id),
                    "author_name": comment.author.name,
                    "content": comment.content,
                    "created_at": comment.created_at.isoformat()
                }
            )
        else:
            # 直接评论或回复评审 - 发送 comment:added 事件
            await notification_service.notify_comment_added(
                contract_id=contract_id,
                comment_data={
                    "id": str(comment.id),
                    "contract_id": contract_id,
                    "review_id": str(review_id) if review_id else None,
                    "author_id": str(comment.author_id),
                    "author_name": comment.author.name,
                    "content": comment.content,
                    "created_at": comment.created_at.isoformat()
                }
            )
        
        return comment
    
    async def get_comment_by_id(
        self,
        comment_id: str,
        db: AsyncSession
    ) -> Optional[Comment]:
        """
        根据ID获取评论
        
        Args:
            comment_id: 评论ID
            db: 数据库会话
            
        Returns:
            评论对象,如果不存在则返回None
        """
        query = select(Comment).options(
            selectinload(Comment.author)
        ).where(Comment.id == comment_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_comments_by_contract(
        self,
        contract_id: str,
        db: AsyncSession
    ) -> List[Comment]:
        """
        获取合同的所有评论
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
            
        Returns:
            评论列表(按创建时间倒序)
        """
        query = select(Comment).options(
            selectinload(Comment.author)
        ).where(
            Comment.contract_id == contract_id
        ).order_by(Comment.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_comments_by_review(
        self,
        review_id: str,
        db: AsyncSession
    ) -> List[Comment]:
        """
        获取评审的所有评论
        
        Args:
            review_id: 评审ID
            db: 数据库会话
            
        Returns:
            评论列表(按创建时间倒序)
        """
        query = select(Comment).options(
            selectinload(Comment.author)
        ).where(
            Comment.review_id == review_id
        ).order_by(Comment.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_replies_by_parent(
        self,
        parent_comment_id: str,
        db: AsyncSession
    ) -> List[Comment]:
        """
        获取父评论的所有回复
        
        Args:
            parent_comment_id: 父评论ID
            db: 数据库会话
            
        Returns:
            回复列表(按创建时间正序)
        """
        query = select(Comment).options(
            selectinload(Comment.author)
        ).where(
            Comment.parent_comment_id == parent_comment_id
        ).order_by(Comment.created_at.asc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_comment(
        self,
        comment_id: str,
        author_id: str,
        content: str,
        db: AsyncSession
    ) -> Comment:
        """
        更新评论内容
        
        Args:
            comment_id: 评论ID
            author_id: 作者ID(用于权限验证)
            content: 新的评论内容
            db: 数据库会话
            
        Returns:
            更新后的评论对象
            
        Raises:
            ValueError: 如果评论不存在或权限不足
        """
        query = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(query)
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise ValueError("评论不存在")
        
        if str(comment.author_id) != author_id:
            raise ValueError("您没有权限修改此评论")
        
        # 更新评论内容
        comment.content = content
        comment.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(comment)
        
        # 清除评审缓存
        await self._clear_review_cache(str(comment.contract_id))
        
        return comment
    
    async def delete_comment(
        self,
        comment_id: str,
        author_id: str,
        db: AsyncSession
    ) -> bool:
        """
        删除评论
        
        Args:
            comment_id: 评论ID
            author_id: 作者ID(用于权限验证)
            db: 数据库会话
            
        Returns:
            是否删除成功
            
        Raises:
            ValueError: 如果评论不存在或权限不足
        """
        query = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(query)
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise ValueError("评论不存在")
        
        if str(comment.author_id) != author_id:
            raise ValueError("您没有权限删除此评论")
        
        contract_id = str(comment.contract_id)
        
        # 删除评论(级联删除子回复)
        await db.delete(comment)
        await db.commit()
        
        # 清除评审缓存
        await self._clear_review_cache(contract_id)
        
        return True
    
    async def like_comment(
        self,
        comment_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Comment:
        """
        点赞/取消点赞评论
        
        Args:
            comment_id: 评论ID
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            更新后的评论对象
            
        Raises:
            ValueError: 如果评论不存在
        """
        query = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(query)
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise ValueError("评论不存在")
        
        # 切换点赞状态
        liked_by = comment.liked_by or []
        if user_id in liked_by:
            # 取消点赞
            liked_by.remove(user_id)
            comment.likes = max(0, comment.likes - 1)
        else:
            # 点赞
            liked_by.append(user_id)
            comment.likes += 1
        
        comment.liked_by = liked_by
        comment.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(comment)
        
        # 发送点赞更新通知
        await notification_service.notify_like_updated(
            contract_id=str(comment.contract_id),
            like_data={
                "target_type": "comment",
                "target_id": str(comment_id),
                "likes": comment.likes,
                "user_id": user_id,
                "action": "unlike" if user_id not in liked_by else "like"
            }
        )
        
        # 清除缓存 - 使用统一的缓存失效策略
        await cache_invalidation.invalidate_like_updated(str(comment.contract_id))
        
        return comment
    
    async def _clear_review_cache(self, contract_id: str):
        """
        清除评审缓存
        
        Args:
            contract_id: 合同ID
        """
        cache_key = f"reviews:{contract_id}"
        await redis_client.delete(cache_key)
