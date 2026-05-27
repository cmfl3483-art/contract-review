"""
数据库模型
Database models
"""

from app.core.database import Base

# 导入所有模型以便 Alembic 能够检测到
from app.models.user import User
from app.models.contract import Contract, ContractStatus
from app.models.review import Review, ReviewStatus
from app.models.comment import Comment
from app.models.attachment import Attachment
from app.models.ai_summary import AISummary, ApprovalStatus
from app.models.notification import Notification, NotificationType
from app.models.contract_revision_log import ContractRevisionLog

__all__ = [
    "Base",
    "User",
    "Contract",
    "ContractStatus",
    "Review",
    "ReviewStatus",
    "Comment",
    "Attachment",
    "AISummary",
    "ApprovalStatus",
    "Notification",
    "NotificationType",
    "ContractRevisionLog",
]
