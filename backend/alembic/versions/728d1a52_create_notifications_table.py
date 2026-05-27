"""create notifications table

Revision ID: 728d1a52
Revises: 1cafed87
Create Date: 2025-07-14 12:10:00.000000

新建 notifications 表，用于存储系统通知记录（审批通过、评论新增、评论回复、@ 提及）。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '728d1a52'
down_revision = '1cafed87'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """新建 notifications 表及相关枚举类型和索引（全部使用原生 SQL 避免 SQLAlchemy 枚举自动创建问题）"""
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notification_type AS ENUM (
                'review_approved', 'comment_added', 'comment_replied', 'user_mentioned'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            actor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type notification_type NOT NULL,
            contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
            anchor_id VARCHAR(100),
            preview VARCHAR(200),
            is_read BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_notifications_recipient_read
        ON notifications (recipient_id, is_read);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_notifications_created_at_desc
        ON notifications (created_at DESC);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_notifications_recipient_id
        ON notifications (recipient_id);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_notifications_contract_id
        ON notifications (contract_id);
    """)


def downgrade() -> None:
    """删除 notifications 表、索引及枚举类型"""
    op.execute("DROP TABLE IF EXISTS notifications")
    op.execute("DROP TYPE IF EXISTS notification_type")
