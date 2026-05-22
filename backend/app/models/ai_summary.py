"""
AI总结模型
AI Summary model
"""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from app.core.database import Base


class ApprovalStatus(str, enum.Enum):
    """审批状态枚举"""
    COMPLETED = "completed"  # 已全部通过
    IN_PROGRESS = "in_progress"  # 审批进行中


class AISummary(Base):
    """
    AI智能总结模型
    存储AI生成的合同审批进度和关键问题摘要
    """
    __tablename__ = "ai_summaries"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="AI总结ID"
    )

    # 关联合同(一对一关系)
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="合同ID"
    )

    # 审批进度信息
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        SQLEnum(ApprovalStatus, name="approval_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="审批状态"
    )
    completed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="已完成审批人数"
    )
    total_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="总审批人数"
    )
    review_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="评审意见总数"
    )

    # 关键问题(JSONB格式存储)
    # 格式: [{"issue": "问题描述", "solution": "解决方案(可选)"}]
    key_issues: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="关键问题列表"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True,
        comment="更新时间"
    )

    # 关系
    contract: Mapped["Contract"] = relationship(
        "Contract",
        foreign_keys=[contract_id],
        lazy="joined"
    )

    # 索引
    __table_args__ = (
        Index('ix_ai_summaries_contract_id', 'contract_id', unique=True),
        Index('ix_ai_summaries_updated_at_desc', 'updated_at', postgresql_ops={'updated_at': 'DESC'}),
    )

    def __repr__(self) -> str:
        return f"<AISummary(id={self.id}, contract_id={self.contract_id}, status={self.approval_status})>"
