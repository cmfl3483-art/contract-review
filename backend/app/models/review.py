"""
评审记录模型
Review model
"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Index, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
import enum

from app.core.database import Base


class ReviewStatus(str, enum.Enum):
    """评审状态枚举"""
    PENDING = "pending"  # 待处理
    REVIEWING = "reviewing"  # 评审中
    APPROVED = "approved"  # 已通过(✅)


class Review(Base):
    """
    评审记录模型
    存储评审人对合同的评审意见和状态
    """
    __tablename__ = "reviews"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="评审记录ID"
    )

    # 关联合同和评审人
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="合同ID"
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="评审人ID"
    )

    # 评审信息
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="评审人角色"
    )
    step: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="评审步骤(如'法务初审')"
    )
    opinion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="评审意见"
    )
    status: Mapped[ReviewStatus] = mapped_column(
        SQLEnum(ReviewStatus, name="review_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ReviewStatus.PENDING,
        index=True,
        comment="评审状态"
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
        back_populates="reviews",
        lazy="joined"
    )
    reviewer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[reviewer_id],
        lazy="joined"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        foreign_keys="Comment.review_id",
        back_populates="review",
        lazy="select"
    )

    # 索引
    __table_args__ = (
        Index('ix_reviews_contract_id', 'contract_id'),
        Index('ix_reviews_reviewer_id', 'reviewer_id'),
        Index('ix_reviews_status', 'status'),
        Index('ix_reviews_created_at_desc', 'created_at', postgresql_ops={'created_at': 'DESC'}),
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, contract_id={self.contract_id}, status={self.status})>"
