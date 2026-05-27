"""add mentioned_user_ids to comments

Revision ID: 1cafed87
Revises: 003
Create Date: 2025-07-14 12:00:00.000000

为 comments 表新增 mentioned_user_ids 列，用于存储评论中 @ 提及的用户 ID 列表。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '1cafed87'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """新增 mentioned_user_ids 列"""
    op.add_column(
        'comments',
        sa.Column(
            'mentioned_user_ids',
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default='{}'
        )
    )


def downgrade() -> None:
    """删除 mentioned_user_ids 列"""
    op.drop_column('comments', 'mentioned_user_ids')
