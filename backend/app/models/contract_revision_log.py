"""
合同修改审计日志模型
Contract revision log model
"""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from app.core.database import Base


class ContractRevisionLog(Base):
    """合同修改审计日志"""
    __tablename__ = "contract_revision_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        comment="日志ID"
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False, index=True,
        comment="合同ID"
    )
    revised_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="修改人ID"
    )
    changed_fields: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False,
        comment="变更字段列表（name/description/attachment）"
    )
    revised_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True,
        comment="变更时间"
    )

    contract: Mapped["Contract"] = relationship(
        "Contract", foreign_keys=[contract_id], lazy="joined"
    )
    revised_by_user: Mapped["User"] = relationship(
        "User", foreign_keys=[revised_by], lazy="joined"
    )

    __table_args__ = (
        Index('ix_revision_logs_contract_revised_at', 'contract_id', 'revised_at'),
    )

    def __repr__(self) -> str:
        return f"<ContractRevisionLog(id={self.id}, contract_id={self.contract_id})>"
