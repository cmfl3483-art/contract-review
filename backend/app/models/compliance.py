"""
合规检查相关 ORM 模型
Compliance check related ORM models
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RuleType(str, enum.Enum):
    NUMBER = "number"
    NAME = "name"
    DESCRIPTION = "description"
    FILE = "file"


class RuleSeverity(str, enum.Enum):
    MUST = "must"
    SHOULD = "should"


class ComplianceCheckStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ComplianceRuleSet(Base):
    __tablename__ = "compliance_rule_sets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    rules: Mapped[list["ComplianceRule"]] = relationship(
        "ComplianceRule",
        back_populates="rule_set",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        # Partial unique index: 同一时刻最多一个 is_active=true 的规则集合
        Index(
            "uq_compliance_rule_sets_one_active",
            "is_active",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_rule_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_type: Mapped[RuleType] = mapped_column(
        SQLEnum(
            RuleType,
            name="rule_type",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    requirement: Mapped[str] = mapped_column(String(2000), nullable=False)
    severity: Mapped[RuleSeverity] = mapped_column(
        SQLEnum(
            RuleSeverity,
            name="rule_severity",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=RuleSeverity.MUST,
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    rule_set: Mapped["ComplianceRuleSet"] = relationship(
        "ComplianceRuleSet", back_populates="rules"
    )

    __table_args__ = (
        Index(
            "ix_compliance_rules_set_id_order",
            "rule_set_id",
            "rule_type",
            "order",
            "created_at",
        ),
    )


class ComplianceCheckResult(Base):
    __tablename__ = "compliance_check_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_set_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_rule_sets.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[ComplianceCheckStatus] = mapped_column(
        SQLEnum(
            ComplianceCheckStatus,
            name="compliance_check_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ComplianceCheckStatus.PENDING,
        index=True,
    )

    # 文件元数据
    file_storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # 抽取结果
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    text_truncated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # 字段初稿（任一可空）
    number_draft: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    name_draft: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description_draft: Mapped[Optional[str]] = mapped_column(
        String(2000), nullable=True
    )

    # AI 输出
    violations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    suggested_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    suggested_description: Mapped[Optional[str]] = mapped_column(
        String(2000), nullable=True
    )
    compliance_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 0..100, R4.13

    # 失败原因
    error_message: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # 时间戳
    requested_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关系
    requester: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[requested_by], lazy="joined"
    )
    rule_set: Mapped[Optional["ComplianceRuleSet"]] = relationship(
        "ComplianceRuleSet", foreign_keys=[rule_set_id], lazy="joined"
    )

    __table_args__ = (
        Index(
            "ix_compliance_check_results_requester_time",
            "requested_by",
            "requested_at",
            postgresql_ops={"requested_at": "DESC"},
        ),
        Index("ix_compliance_check_results_status", "status"),
    )
