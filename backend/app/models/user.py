"""
用户模型
User model
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class User(Base):
    """
    用户模型
    存储钉钉授权登录的用户信息
    """
    __tablename__ = "users"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="用户ID"
    )

    # 钉钉相关字段
    dingtalk_user_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="钉钉用户ID"
    )
    dingtalk_union_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="钉钉UnionID"
    )

    # 用户基本信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="用户姓名"
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="用户角色(销售/法务/财务/业务/运营/人事)"
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="邮箱"
    )
    mobile: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="手机号"
    )
    avatar: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="头像URL"
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="部门"
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
        comment="更新时间"
    )

    # 索引
    __table_args__ = (
        Index('ix_users_dingtalk_user_id', 'dingtalk_user_id'),
        Index('ix_users_role', 'role'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, role={self.role})>"
