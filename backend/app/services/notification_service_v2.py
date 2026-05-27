"""
通知服务 V2
Notification Service V2

提供完整的通知管理功能，包括：
- 创建各类通知（审批通过、新评论、评论回复、@ 提及）
- 查询通知列表（分页）
- 获取未读数（Redis 缓存）
- 标记已读 / 全部已读
- Socket.IO 实时推送
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from app.models.notification import Notification, NotificationType
from app.models.contract import Contract
from app.models.comment import Comment
from app.core.redis_client import redis_client
from app.core.socketio_server import emit_to_user


class NotificationServiceV2:
    """通知服务 V2 - 支持持久化通知 + Socket.IO 实时推送"""

    # ------------------------------------------------------------------ #
    #  创建通知                                                            #
    # ------------------------------------------------------------------ #

    async def create_notification(
        self,
        recipient_id: str,
        actor_id: str,
        notification_type: NotificationType,
        contract_id: str,
        anchor_id: Optional[str],
        preview: Optional[str],
        db: AsyncSession,
    ) -> Optional[Notification]:
        """
        创建通知记录并推送 Socket.IO 事件。

        当 recipient_id == actor_id 时跳过（不给自己发通知）。

        Args:
            recipient_id: 接收人用户 ID
            actor_id: 操作人用户 ID
            notification_type: 通知类型
            contract_id: 关联合同 ID
            anchor_id: 前端定位锚点（评论 ID 或评审 ID）
            preview: 内容预览
            db: 数据库会话

        Returns:
            创建的 Notification 对象，或 None（自通知跳过）
        """
        if str(recipient_id) == str(actor_id):
            return None  # 不给自己发通知

        notification = Notification(
            recipient_id=recipient_id,
            actor_id=actor_id,
            type=notification_type,
            contract_id=contract_id,
            anchor_id=anchor_id,
            preview=preview[:200] if preview else None,
        )
        db.add(notification)
        await db.flush()

        # 通过 Socket.IO 推送（失败不影响主流程）
        await self._push_to_socket(notification)

        # 清除未读数缓存
        await redis_client.delete(f"notification:unread:{recipient_id}")

        return notification

    # ------------------------------------------------------------------ #
    #  业务场景通知                                                        #
    # ------------------------------------------------------------------ #

    async def create_review_approved_notification(
        self, review, db: AsyncSession
    ) -> None:
        """
        审批通过通知 → 发给合同发起人。

        Args:
            review: Review 对象（需含 reviewer 关系）
            db: 数据库会话
        """
        contract = await self._get_contract(review.contract_id, db)
        if contract is None:
            return

        await self.create_notification(
            recipient_id=str(contract.initiator_id),
            actor_id=str(review.reviewer_id),
            notification_type=NotificationType.REVIEW_APPROVED,
            contract_id=str(review.contract_id),
            anchor_id=str(review.id),
            preview=f"{review.reviewer.name} 审批通过了合同",
            db=db,
        )

    async def create_comment_added_notification(
        self, comment: Comment, db: AsyncSession
    ) -> None:
        """
        新评论通知 → 发给合同发起人（仅顶层评论触发）。

        Args:
            comment: Comment 对象
            db: 数据库会话
        """
        # 仅顶层评论触发
        if comment.parent_comment_id is not None:
            return

        contract = await self._get_contract(comment.contract_id, db)
        if contract is None:
            return

        await self.create_notification(
            recipient_id=str(contract.initiator_id),
            actor_id=str(comment.author_id),
            notification_type=NotificationType.COMMENT_ADDED,
            contract_id=str(comment.contract_id),
            anchor_id=str(comment.id),
            preview=comment.content[:100],
            db=db,
        )

    async def create_comment_replied_notification(
        self, comment: Comment, db: AsyncSession
    ) -> None:
        """
        回复通知 → 发给被回复的评论作者（仅子评论触发）。

        Args:
            comment: Comment 对象
            db: 数据库会话
        """
        # 仅子评论触发
        if comment.parent_comment_id is None:
            return

        parent = await self._get_comment(comment.parent_comment_id, db)
        if parent is None:
            return

        await self.create_notification(
            recipient_id=str(parent.author_id),
            actor_id=str(comment.author_id),
            notification_type=NotificationType.COMMENT_REPLIED,
            contract_id=str(comment.contract_id),
            anchor_id=str(comment.id),
            preview=comment.content[:100],
            db=db,
        )

    async def create_mention_notifications(
        self, comment: Comment, db: AsyncSession
    ) -> None:
        """
        @ 提及通知 → 为每个被提及的用户创建通知。

        Args:
            comment: Comment 对象（需含 mentioned_user_ids）
            db: 数据库会话
        """
        for user_id in (comment.mentioned_user_ids or []):
            await self.create_notification(
                recipient_id=user_id,
                actor_id=str(comment.author_id),
                notification_type=NotificationType.USER_MENTIONED,
                contract_id=str(comment.contract_id),
                anchor_id=str(comment.id),
                preview=comment.content[:100],
                db=db,
            )

    async def create_contract_revised_notifications(
        self,
        contract: Contract,
        changed_fields: list[str],
        db: AsyncSession,
    ) -> None:
        """
        合同重审通知 → 为该合同所有评审人各生成一条 CONTRACT_REVISED 通知。

        发起人本人若同时是评审人，由 create_notification 内置的
        actor==recipient 跳过逻辑过滤掉，不会收到自己的通知。

        Args:
            contract: 已被修改的 Contract 对象
            changed_fields: 变更字段列表（'name'/'description'/'attachment'）
            db: 数据库会话
        """
        from app.models.review import Review

        # 加载该合同所有评审人
        result = await db.execute(
            select(Review).where(Review.contract_id == contract.id)
        )
        reviews = result.scalars().all()

        preview = (
            f"{contract.name} 已修改：{', '.join(changed_fields)}，请重新审批"
        )

        for review in reviews:
            await self.create_notification(
                recipient_id=str(review.reviewer_id),
                actor_id=str(contract.initiator_id),
                notification_type=NotificationType.CONTRACT_REVISED,
                contract_id=str(contract.id),
                anchor_id=None,
                preview=preview,
                db=db,
            )

    # ------------------------------------------------------------------ #
    #  查询 / 已读                                                         #
    # ------------------------------------------------------------------ #

    async def get_notifications(
        self,
        recipient_id: str,
        page: int,
        page_size: int,
        db: AsyncSession,
    ) -> dict:
        """
        分页查询通知列表，按创建时间倒序。

        Args:
            recipient_id: 接收人用户 ID
            page: 页码（从 1 开始）
            page_size: 每页条数
            db: 数据库会话

        Returns:
            {
                "notifications": [...],
                "total": int,
                "page": int,
                "page_size": int,
            }
        """
        base_query = (
            select(Notification)
            .options(
                selectinload(Notification.actor),
                selectinload(Notification.contract),
            )
            .where(Notification.recipient_id == recipient_id)
            .order_by(Notification.created_at.desc())
        )

        # 总数
        count_query = select(func.count()).select_from(
            select(Notification)
            .where(Notification.recipient_id == recipient_id)
            .subquery()
        )
        total = await db.scalar(count_query) or 0

        # 分页数据
        offset = (page - 1) * page_size
        result = await db.execute(base_query.offset(offset).limit(page_size))
        items = result.scalars().all()

        # 序列化
        notifications = []
        for n in items:
            notifications.append({
                "id": str(n.id),
                "type": n.type,
                "actorId": str(n.actor_id),
                "actorName": n.actor.name if n.actor else None,
                "contractId": str(n.contract_id),
                "contractName": n.contract.name if n.contract else None,
                "anchorId": n.anchor_id,
                "preview": n.preview,
                "isRead": n.is_read,
                "createdAt": n.created_at.isoformat(),
            })

        return {
            "notifications": notifications,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_unread_count(self, recipient_id: str, db: AsyncSession) -> int:
        """
        获取未读通知数量，优先读 Redis 缓存（TTL 60s）。

        Args:
            recipient_id: 接收人用户 ID
            db: 数据库会话

        Returns:
            未读通知数量
        """
        cache_key = f"notification:unread:{recipient_id}"

        # 先查缓存
        cached = await redis_client.get(cache_key)
        if cached is not None:
            return int(cached)

        # 缓存未命中，查 DB
        count = await db.scalar(
            select(func.count()).select_from(Notification).where(
                Notification.recipient_id == recipient_id,
                Notification.is_read == False,  # noqa: E712
            )
        ) or 0

        # 写入缓存
        await redis_client.set(cache_key, str(count), ex=60)

        return count

    async def mark_as_read(
        self, notification_id: str, recipient_id: str, db: AsyncSession
    ) -> bool:
        """
        标记单条通知为已读。

        Args:
            notification_id: 通知 ID
            recipient_id: 接收人用户 ID（用于权限校验）
            db: 数据库会话

        Returns:
            是否更新成功（rowcount > 0）
        """
        result = await db.execute(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.recipient_id == recipient_id,
            )
            .values(is_read=True)
        )

        # 删除未读数缓存
        await redis_client.delete(f"notification:unread:{recipient_id}")

        return result.rowcount > 0

    async def mark_all_as_read(self, recipient_id: str, db: AsyncSession) -> int:
        """
        将当前用户所有未读通知标记为已读。

        Args:
            recipient_id: 接收人用户 ID
            db: 数据库会话

        Returns:
            更新的行数
        """
        result = await db.execute(
            update(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )

        # 将缓存直接设为 "0"，避免立即失效后重复查 DB
        await redis_client.set(
            f"notification:unread:{recipient_id}", "0", ex=60
        )

        return result.rowcount

    # ------------------------------------------------------------------ #
    #  私有辅助方法                                                        #
    # ------------------------------------------------------------------ #

    async def _push_to_socket(self, notification: Notification) -> None:
        """
        通过 Socket.IO 向接收人推送 notification:new 事件。
        失败时静默忽略，不影响主流程。

        Args:
            notification: Notification 对象
        """
        try:
            await emit_to_user(
                str(notification.recipient_id),
                "notification:new",
                {
                    "id": str(notification.id),
                    "type": notification.type,
                    "contractId": str(notification.contract_id),
                    "anchorId": notification.anchor_id,
                    "preview": notification.preview,
                    "createdAt": notification.created_at.isoformat(),
                },
            )
        except Exception:
            pass  # Socket.IO 不可用时静默失败，通知已持久化

    async def _get_contract(
        self, contract_id, db: AsyncSession
    ) -> Optional[Contract]:
        """
        查询合同对象。

        Args:
            contract_id: 合同 ID
            db: 数据库会话

        Returns:
            Contract 对象，或 None
        """
        result = await db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        return result.scalar_one_or_none()

    async def _get_comment(
        self, comment_id, db: AsyncSession
    ) -> Optional[Comment]:
        """
        查询评论对象。

        Args:
            comment_id: 评论 ID
            db: 数据库会话

        Returns:
            Comment 对象，或 None
        """
        result = await db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()


# 全局实例
notification_service_v2 = NotificationServiceV2()
