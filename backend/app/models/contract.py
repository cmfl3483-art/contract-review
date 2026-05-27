"""
合同模型
Contract model
"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Index, Enum as SQLEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
import enum

from app.core.database import Base


class ContractStatus(str, enum.Enum):
    """合同状态枚举"""
    PROGRESS = "progress"  # 进行中
    COMPLETED = "completed"  # 已完成


class Contract(Base):
    """
    合同模型
    存储合同的基本信息和状态
    """
    __tablename__ = "contracts"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="合同ID"
    )

    # 合同基本信息
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="合同名称"
    )
    contract_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="合同编号"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="合同描述"
    )
    status: Mapped[ContractStatus] = mapped_column(
        SQLEnum(ContractStatus, name="contract_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ContractStatus.PROGRESS,
        index=True,
        comment="合同状态"
    )

    # 关联用户
    initiator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="发起人ID"
    )

    # 抄送人列表(存储用户ID数组)
    cc_users: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="抄送人ID列表"
    )

    # 乐观锁版本号
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="版本号(用于乐观锁)"
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
    initiator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[initiator_id],
        lazy="joined"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="contract",
        cascade="all, delete-orphan",
        lazy="select"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment",
        back_populates="contract",
        cascade="all, delete-orphan",
        lazy="select"
    )

    # 索引
    __table_args__ = (
        Index('ix_contracts_initiator_id', 'initiator_id'),
        Index('ix_contracts_status', 'status'),
        Index('ix_contracts_created_at_desc', 'created_at', postgresql_ops={'created_at': 'DESC'}),
    )

    def __repr__(self) -> str:
        return f"<Contract(id={self.id}, name={self.name}, status={self.status})>"
