"""
合规检查相关 Pydantic schemas
Compliance check related Pydantic schemas
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────
# 规则集合 (Rule Set)
# ─────────────────────────────────────────────


class CreateRuleSetRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="规则集合名称")
    description: Optional[str] = Field(
        None, max_length=1000, description="规则集合描述"
    )
    is_active: bool = Field(False, description="是否为当前生效的规则集合")

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name 不能为空白字符串")
        return v


class UpdateRuleSetRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("name 不能为空白字符串")
        return v


class RuleSetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    is_active: bool
    rule_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 规则 (Rule)
# ─────────────────────────────────────────────


class CreateRuleRequest(BaseModel):
    rule_type: Literal["number", "name", "description", "file"] = Field(
        ..., description="规则作用对象"
    )
    title: str = Field(..., min_length=1, max_length=100, description="规则名称")
    requirement: str = Field(
        ..., min_length=1, max_length=2000, description="规则正文描述"
    )
    severity: Literal["must", "should"] = Field("must", description="严重程度")
    order: int = Field(0, description="排序权重")

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title 不能为空白字符串")
        return v

    @field_validator("requirement")
    @classmethod
    def requirement_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("requirement 不能为空白字符串")
        return v


class UpdateRuleRequest(BaseModel):
    rule_type: Optional[Literal["number", "name", "description", "file"]] = None
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    requirement: Optional[str] = Field(None, min_length=1, max_length=2000)
    severity: Optional[Literal["must", "should"]] = None
    order: Optional[int] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("title 不能为空白字符串")
        return v

    @field_validator("requirement")
    @classmethod
    def requirement_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("requirement 不能为空白字符串")
        return v


class RuleResponse(BaseModel):
    id: str
    rule_set_id: str
    rule_type: Literal["number", "name", "description", "file"]
    title: str
    requirement: str
    severity: Literal["must", "should"]
    order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 合规检查结果 (Check Result)
# ─────────────────────────────────────────────


class UserBriefDto(BaseModel):
    id: str
    name: str
    avatar: Optional[str]

    model_config = {"from_attributes": True}


class ViolationDto(BaseModel):
    rule_id: str
    rule_title: str  # 后端 join 补全
    rule_type: Literal["number", "name", "description", "file"]
    location: Literal["number", "name", "description", "file"]
    excerpt: str  # ≤ 500
    description: str  # ≤ 500
    suggestion: str  # ≤ 500
    severity: Literal["must", "should"]


class ComplianceCheckResultDto(BaseModel):
    id: str
    status: Literal["pending", "completed", "failed"]
    requested_by: UserBriefDto
    rule_set_id: Optional[str]
    rule_set_name: Optional[str]
    file_name: str
    file_size: int
    file_mime_type: str
    extracted_text: str  # 0-100k
    text_truncated: bool
    number_draft: Optional[str]
    name_draft: Optional[str]
    description_draft: Optional[str]
    violations: list[ViolationDto]
    suggested_name: Optional[str]
    suggested_description: Optional[str]
    compliance_score: Optional[int]  # 0..100, status != completed 时为 None
    requested_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    # 注意: 不包含 suggested_number / contract_text 字段 (R5.1)

    model_config = {"from_attributes": True}


class ComplianceCheckListItemDto(BaseModel):
    id: str
    status: Literal["pending", "completed", "failed"]
    name_draft: Optional[str]
    rule_set_name: Optional[str]
    file_name: str
    text_truncated: bool
    violation_count: Optional[int]  # 仅 completed 才有，否则 None
    compliance_score: Optional[int]  # 0..100, status != completed 时为 None
    requested_at: datetime
    completed_at: Optional[datetime]
    # 不包含 contract_text / extracted_text (R5.2)

    model_config = {"from_attributes": True}


class ComplianceCheckListResponse(BaseModel):
    items: list[ComplianceCheckListItemDto]
    total: int
    page: int
    page_size: int
