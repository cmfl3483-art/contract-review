"""
评审服务层
实现评审CRUD和状态更新功能
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid
import logging

from app.models.review import Review
from app.models.comment import Comment
from app.models.contract import Contract
from app.models.ai_summary import AISummary
from app.core.redis_client import redis_client
from app.services.comment_service import CommentService
from app.services.notification_service import notification_service
from app.services.notification_service_v2 import notification_service_v2
from app.utils.cache_invalidation import cache_invalidation

# 配置日志
logger = logging.getLogger(__name__)
class ReviewService:
    """评审服务类"""
    
    def __init__(self):
        """初始化评审服务"""
        self.comment_service = CommentService()
    
    async def get_contract_reviews(
        self,
        contract_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        获取合同的所有评审记录(过滤空记录) + 顶层游离评论
        性能优化:
        1. 使用Redis缓存评审列表
        2. 使用selectinload预加载关联数据
        3. 使用索引 ix_reviews_contract_created_at 加速查询
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
            
        Returns:
            字典: { "reviews": [...], "top_level_comments": [...] }
        """
        # 生成缓存键 (v2 区分旧 List 格式)
        cache_key = f"reviews:v2:{contract_id}"
        
        # 尝试从缓存获取
        cached = await redis_client.get(cache_key)
        if cached is not None and isinstance(cached, dict) and "reviews" in cached:
            return cached
        
        # 使用索引 ix_reviews_contract_created_at 和 selectinload 预加载
        query = select(Review).options(
            selectinload(Review.reviewer),
            selectinload(Review.comments).selectinload(Comment.author)
        ).where(
            Review.contract_id == contract_id
        ).order_by(Review.created_at.desc())
        
        result = await db.execute(query)
        reviews = result.scalars().all()
        
        # 过滤空评审记录
        filtered_reviews = []
        for review in reviews:
            # 如果有意见内容或有回复,则保留
            if review.opinion and review.opinion.strip():
                # 过滤占位文本
                if review.opinion not in ["待评审", "待评审,请反馈"]:
                    filtered_reviews.append(review)
            elif review.comments:
                # 没有意见但有回复,也保留
                filtered_reviews.append(review)
        
        # 辅助：将扁平评论列表按 parent_comment_id 组装为多层树
        def _serialize_comment_node(c: Comment) -> Dict[str, Any]:
            return {
                "id": str(c.id),
                "contract_id": str(c.contract_id),
                "review_id": str(c.review_id) if c.review_id else None,
                "parent_comment_id": str(c.parent_comment_id) if c.parent_comment_id else None,
                "content": c.content,
                "author": {
                    "id": str(c.author.id),
                    "name": c.author.name,
                    "avatar": c.author.avatar
                } if c.author else None,
                "likes": c.likes,
                "liked_by": c.liked_by or [],
                "created_at": c.created_at.isoformat(),
                "replies": []
            }
        
        def _build_comment_tree(flat: List[Comment]) -> List[Dict[str, Any]]:
            by_parent: Dict[Any, List[Comment]] = {}
            for c in flat:
                key = str(c.parent_comment_id) if c.parent_comment_id else None
                by_parent.setdefault(key, []).append(c)
            
            def _build(parent_id: Optional[str]) -> List[Dict[str, Any]]:
                items: List[Dict[str, Any]] = []
                for c in by_parent.get(parent_id, []):
                    node = _serialize_comment_node(c)
                    node["replies"] = _build(str(c.id))
                    items.append(node)
                return items
            
            return _build(None)
        
        # 序列化为字典以便缓存 (review 下的评论也要树形化)
        serialized_reviews = [
            {
                "id": str(r.id),
                "contract_id": str(r.contract_id),
                "reviewer_id": str(r.reviewer_id),
                "reviewer": {
                    "id": str(r.reviewer.id),
                    "name": r.reviewer.name,
                    "avatar": r.reviewer.avatar,
                    "role": r.role
                } if r.reviewer else None,
                "role": r.role,
                "step": r.step,
                "opinion": r.opinion,
                "status": r.status,
                "likes": r.likes,
                "liked_by": r.liked_by,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
                # comments 只保留一级 (parent IS NULL), 其余挂在 .replies
                "comments": _build_comment_tree(list(r.comments))
            }
            for r in filtered_reviews
        ]
        
        # 查询顶层游离评论及其所有后裔 (review_id IS NULL)
        # 一次查出该合同下所有游离评论 (含多层回复), 在内存建树, 避免 N+1
        floating_query = select(Comment).options(
            selectinload(Comment.author)
        ).where(
            and_(
                Comment.contract_id == contract_id,
                Comment.review_id.is_(None)
            )
        ).order_by(Comment.created_at.asc())
        floating_result = await db.execute(floating_query)
        floating_comments = list(floating_result.scalars().all())
        
        # 树形组装后顶层按创建时间倒序 (最新在前)
        serialized_top_comments = _build_comment_tree(floating_comments)
        serialized_top_comments.sort(key=lambda x: x["created_at"], reverse=True)
        
        payload = {
            "reviews": serialized_reviews,
            "top_level_comments": serialized_top_comments
        }
        
        # 缓存结果 - 使用中等TTL(5分钟)
        await redis_client.set(cache_key, payload, ex=redis_client.TTL_MEDIUM)
        
        return payload
    
    async def get_ai_summary(
        self,
        contract_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        获取合同的AI智能总结
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
            
        Returns:
            AI总结数据字典,如果不存在则返回None
        """
        # 查询AI总结
        query = select(AISummary).where(AISummary.contract_id == contract_id)
        result = await db.execute(query)
        summary = result.scalar_one_or_none()
        
        if not summary:
            return None
        
        # 格式化返回数据
        return {
            "id": str(summary.id),
            "approvalStatus": summary.approval_status.value,
            "completedCount": summary.completed_count,
            "totalCount": summary.total_count,
            "reviewCount": summary.review_count,
            "keyIssues": summary.key_issues,
            "createdAt": summary.created_at.isoformat(),
            "updatedAt": summary.updated_at.isoformat()
        }
    
    async def approve_review(
        self,
        review_id: str,
        reviewer_id: str,
        opinion: str,
        db: AsyncSession
    ) -> Review:
        """
        同意评审(使用事务处理确保数据一致性)
        
        Args:
            review_id: 评审ID
            reviewer_id: 评审人ID
            opinion: 评审意见
            db: 数据库会话
            
        Returns:
            更新后的评审记录
            
        Raises:
            ValueError: 如果评审不存在或权限不足
            Exception: 数据库操作失败时回滚事务
        """
        try:
            async with db.begin():
                # 查询评审记录
                query = select(Review).where(Review.id == review_id)
                result = await db.execute(query)
                review = result.scalar_one_or_none()
                
                if not review:
                    raise ValueError("评审记录不存在")
                
                if str(review.reviewer_id) != str(reviewer_id):
                    raise ValueError("您没有权限审批此评审项")
                
                # 保存合同ID用于后续操作
                contract_id = review.contract_id
                
                # 更新评审状态
                review.status = "approved"
                review.opinion = opinion
                review.updated_at = datetime.utcnow()
                
                await db.flush()  # 刷新以获取更新后的数据
                
                # 检查是否所有评审都已通过,并更新合同状态
                await self._check_and_update_contract_status_in_transaction(contract_id, db)
                
                # 事务提交点 - 如果上述操作有任何失败,事务会自动回滚
                await db.commit()
                
            # 事务成功提交后,执行后续操作
            await db.refresh(review)
            
            # 加载关联数据以便发送通知
            await db.refresh(review, ["reviewer"])
            
            # 发送评审更新通知
            await notification_service.notify_review_added(
                contract_id=str(contract_id),
                review_data={
                    "id": str(review.id),
                    "contract_id": str(contract_id),
                    "reviewer_id": str(review.reviewer_id),
                    "reviewer_name": review.reviewer.name,
                    "role": review.role,
                    "opinion": review.opinion,
                    "status": review.status,
                    "created_at": review.created_at.isoformat()
                }
            )
            # 触发持久化通知（新增）
            await notification_service_v2.create_review_approved_notification(review, db)
            
            # 清除相关缓存 - 使用统一的缓存失效策略
            # 获取所有评审人ID用于批量清除待办缓存
            all_reviews_query = select(Review).where(Review.contract_id == contract_id)
            all_reviews_result = await db.execute(all_reviews_query)
            all_reviews = all_reviews_result.scalars().all()
            all_reviewer_ids = [r.reviewer_id for r in all_reviews]
            
            await cache_invalidation.invalidate_review_approved(
                contract_id=str(contract_id),
                reviewer_id=reviewer_id,
                all_reviewer_ids=all_reviewer_ids
            )
            
            # 计算新的待办数量并发送通知
            pending_count = await self._get_pending_count(reviewer_id, db)
            await notification_service.notify_pending_changed(
                user_id=reviewer_id,
                pending_count=pending_count,
                contract_id=str(contract_id)
            )
            
            return review
            
        except ValueError as e:
            # 业务逻辑错误,直接抛出
            raise e
        except Exception as e:
            # 数据库操作失败,事务已自动回滚
            # 记录错误日志
            logger.error(f"审批评审失败,事务已回滚: review_id={review_id}, error={str(e)}")
            raise Exception(f"审批评审失败: {str(e)}")
    
    async def like_review(
        self,
        review_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Review:
        """
        点赞/取消点赞评审意见
        
        Args:
            review_id: 评审ID
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            更新后的评审记录
        """
        query = select(Review).where(Review.id == review_id)
        result = await db.execute(query)
        review = result.scalar_one_or_none()
        
        if not review:
            raise ValueError("评审记录不存在")
        
        # 切换点赞状态
        liked_by = review.liked_by or []
        if user_id in liked_by:
            # 取消点赞
            liked_by.remove(user_id)
            review.likes = max(0, review.likes - 1)
        else:
            # 点赞
            liked_by.append(user_id)
            review.likes += 1
        
        review.liked_by = liked_by
        
        await db.commit()
        await db.refresh(review)
        
        # 发送点赞更新通知
        await notification_service.notify_like_updated(
            contract_id=str(review.contract_id),
            like_data={
                "target_type": "review",
                "target_id": str(review_id),
                "likes": review.likes,
                "user_id": user_id,
                "action": "unlike" if user_id not in liked_by else "like"
            }
        )
        
        # 清除缓存 - 使用统一的缓存失效策略
        await cache_invalidation.invalidate_like_updated(str(review.contract_id))
        
        return review
    
    async def add_comment(
        self,
        contract_id: str,
        author_id: str,
        content: str,
        review_id: Optional[str] = None,
        parent_comment_id: Optional[str] = None,
        mentioned_user_ids: Optional[List[str]] = None,  # 新增
        db: AsyncSession = None
    ) -> Comment:
        """
        添加评论(委托给CommentService)
        
        Args:
            contract_id: 合同ID
            author_id: 作者ID
            content: 评论内容
            review_id: 评审ID(可选,回复评审意见时提供)
            parent_comment_id: 父评论ID(可选,嵌套回复时提供)
            mentioned_user_ids: 被@提及的用户ID列表(可选)
            db: 数据库会话
            
        Returns:
            创建的评论对象
        """
        return await self.comment_service.create_comment(
            contract_id=contract_id,
            author_id=author_id,
            content=content,
            review_id=review_id,
            parent_comment_id=parent_comment_id,
            mentioned_user_ids=mentioned_user_ids,  # 新增
            db=db
        )
    
    async def like_comment(
        self,
        comment_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Comment:
        """
        点赞/取消点赞评论(委托给CommentService)
        
        Args:
            comment_id: 评论ID
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            更新后的评论对象
        """
        return await self.comment_service.like_comment(
            comment_id=comment_id,
            user_id=user_id,
            db=db
        )
    
    async def _check_and_update_contract_status_in_transaction(
        self,
        contract_id: str,
        db: AsyncSession
    ):
        """
        在事务中检查合同是否全部通过并更新合同状态
        此方法在事务上下文中调用,不执行commit
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
        """
        # 查询合同的所有评审记录
        query = select(Review).where(Review.contract_id == contract_id)
        result = await db.execute(query)
        reviews = result.scalars().all()
        
        # 检查是否所有评审都已通过
        all_approved = all(review.status == "approved" for review in reviews)
        
        if all_approved:
            # 更新合同状态为已完成
            contract_query = select(Contract).where(Contract.id == contract_id)
            contract_result = await db.execute(contract_query)
            contract = contract_result.scalar_one_or_none()
            
            if contract and contract.status != "completed":
                contract.status = "completed"
                # 不在这里commit,由外层事务控制
    
    async def _check_and_update_contract_status(
        self,
        contract_id: str,
        db: AsyncSession
    ):
        """
        检查合同是否全部通过,更新合同状态
        此方法用于独立调用,会执行commit和发送通知
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
        """
        # 查询合同的所有评审记录
        query = select(Review).where(Review.contract_id == contract_id)
        result = await db.execute(query)
        reviews = result.scalars().all()
        
        # 检查是否所有评审都已通过
        all_approved = all(review.status == "approved" for review in reviews)
        
        if all_approved:
            # 更新合同状态为已完成
            contract_query = select(Contract).where(Contract.id == contract_id)
            contract_result = await db.execute(contract_query)
            contract = contract_result.scalar_one_or_none()
            
            if contract and contract.status != "completed":
                contract.status = "completed"
                await db.commit()
                
                # 发送合同更新通知
                await notification_service.notify_contract_updated(
                    contract_id=str(contract_id),
                    contract_data={
                        "id": str(contract.id),
                        "name": contract.name,
                        "status": contract.status,
                        "updated_at": contract.updated_at.isoformat()
                    }
                )
                
                # 清除合同列表缓存
                await redis_client.delete_pattern("contract:list:*")
    
    async def _clear_review_cache(self, contract_id: str):
        """清除评审缓存"""
        cache_key = f"reviews:{contract_id}"
        await redis_client.delete(cache_key)
    
    async def _clear_pending_count_cache(self, user_id: str):
        """清除待办数量缓存"""
        cache_key = f"contract:pending:{user_id}"
        await redis_client.delete(cache_key)
    
    async def _get_pending_count(self, user_id: str, db: AsyncSession) -> int:
        """
        获取用户待办数量
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            待办数量
        """
        query = select(func.count()).select_from(Review).where(
            and_(
                Review.reviewer_id == user_id,
                Review.status == "pending"
            )
        )
        
        result = await db.execute(query)
        return result.scalar() or 0
