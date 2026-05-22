"""add optimistic locking version field

Revision ID: 003
Revises: 002
Create Date: 2025-01-10 12:00:00.000000

添加乐观锁版本字段:
1. 为contracts表添加version字段
2. 设置默认值为1
3. 为现有记录设置初始版本号
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加乐观锁版本字段"""
    
    # 1. 添加version字段(允许NULL,以便为现有记录设置值)
    op.add_column(
        'contracts',
        sa.Column('version', sa.Integer(), nullable=True, comment='版本号(用于乐观锁)')
    )
    
    # 2. 为现有记录设置初始版本号
    op.execute("UPDATE contracts SET version = 1 WHERE version IS NULL")
    
    # 3. 将字段设置为NOT NULL
    op.alter_column('contracts', 'version', nullable=False)


def downgrade() -> None:
    """删除乐观锁版本字段"""
    
    # 删除version字段
    op.drop_column('contracts', 'version')
