"""
评论模型
Comment model
"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from app.core.database import Base


class Comment(Base):
    """
    评论模型
    支持对评审意见的评论和嵌套回复
    """
    __tablename__ = "comments"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="评论ID"
    )

    # 关联合同
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="合同ID"
    )

    # 关联评审记录(可选,如果是回复评审意见)
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="评审记录ID"
    )

    # 父评论ID(用于嵌套回复)
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="父评论ID"
    )

    # 评论作者
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="作者ID"
    )

    # 评论内容
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="评论内容"
    )

    # 点赞相关
    likes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="点赞数"
    )
    liked_by: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="点赞用户ID列表"
    )

    # 被@提及的用户
    mentioned_user_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="被@提及的用户ID列表"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )

    # 关系
    contract: Mapped["Contract"] = relationship(
        "Contract",
        foreign_keys=[contract_id],
        lazy="joined"
    )
    review: Mapped["Review"] = relationship(
        "Review",
        foreign_keys=[review_id],
        lazy="joined"
    )
    author: Mapped["User"] = relationship(
        "User",
        foreign_keys=[author_id],
        lazy="joined"
    )
    parent_comment: Mapped["Comment"] = relationship(
        "Comment",
        foreign_keys=[parent_comment_id],
        remote_side=[id],
        lazy="joined"
    )

    # 索引
    __table_args__ = (
        Index('ix_comments_contract_id', 'contract_id'),
        Index('ix_comments_review_id', 'review_id'),
        Index('ix_comments_parent_comment_id', 'parent_comment_id'),
        Index('ix_comments_created_at_desc', 'created_at', postgresql_ops={'created_at': 'DESC'}),
    )

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, contract_id={self.contract_id}, author_id={self.author_id})>"
