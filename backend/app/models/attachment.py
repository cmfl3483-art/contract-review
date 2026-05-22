"""
附件模型
Attachment model
"""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Attachment(Base):
    """
    附件模型
    存储合同附件信息,支持版本管理
    """
    __tablename__ = "attachments"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="附件ID"
    )

    # 关联合同
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="合同ID"
    )

    # 文件信息
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="文件名"
    )
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="版本号"
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="文件大小(字节)"
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="MIME类型"
    )

    # 存储信息
    storage_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="MinIO存储键"
    )

    # 上传人
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="上传人ID"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )

    # 关系
    contract: Mapped["Contract"] = relationship(
        "Contract",
        foreign_keys=[contract_id],
        back_populates="attachments",
        lazy="joined"
    )
    uploader: Mapped["User"] = relationship(
        "User",
        foreign_keys=[uploader_id],
        lazy="joined"
    )

    # 索引
    __table_args__ = (
        Index('ix_attachments_contract_id', 'contract_id'),
        # 复合索引用于按文件名分组和按时间排序
        Index(
            'ix_attachments_filename_created_at',
            'file_name',
            'created_at',
            postgresql_ops={'created_at': 'DESC'}
        ),
    )

    def __repr__(self) -> str:
        return f"<Attachment(id={self.id}, file_name={self.file_name}, version={self.version})>"
