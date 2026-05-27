"""
通知模型
Notification model
"""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
    """通知类型枚举"""
    REVIEW_APPROVED = "review_approved"    # 审批通过
    COMMENT_ADDED = "comment_added"        # 新评论
    COMMENT_REPLIED = "comment_replied"    # 评论被回复
    USER_MENTIONED = "user_mentioned"      # 被@提及
    CONTRACT_REVISED = "contract_revised"    # 合同被发起人修改触发重审


class Notification(Base):
    """
    通知模型
    存储系统通知记录，支持审批、评论、回复、@提及等场景
    """
    __tablename__ = "notifications"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="通知ID"
    )

    # 接收人（通知目标用户）
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="接收人用户ID"
    )

    # 操作人（触发通知的用户）
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="操作人用户ID"
    )

    # 通知类型
    type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType, name="notification_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="通知类型"
    )

    # 关联合同
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联合同ID"
    )

    # 前端定位锚点（评论ID或评审ID）
    anchor_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="关联的评论或评审ID，用于前端定位"
    )

    # 内容预览
    preview: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="内容预览（最多200字符）"
    )

    # 已读状态
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="是否已读"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="创建时间"
    )

    # 关系
    recipient: Mapped["User"] = relationship(
        "User",
        foreign_keys=[recipient_id],
        lazy="joined"
    )
    actor: Mapped["User"] = relationship(
        "User",
        foreign_keys=[actor_id],
        lazy="joined"
    )
    contract: Mapped["Contract"] = relationship(
        "Contract",
        foreign_keys=[contract_id],
        lazy="joined"
    )

    # 复合索引
    __table_args__ = (
        Index('ix_notifications_recipient_read', 'recipient_id', 'is_read'),
        Index('ix_notifications_created_at_desc', 'created_at', postgresql_ops={'created_at': 'DESC'}),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.type}, recipient_id={self.recipient_id}, is_read={self.is_read})>"
