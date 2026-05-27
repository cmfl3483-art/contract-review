"""add contract_number field to contracts

Revision ID: 004
Revises: e2d6da7f
Create Date: 2026-05-26 14:50:00.000000

为 contracts 表添加 contract_number 字段:
1. 添加 contract_number 字段(VARCHAR 100, 允许NULL)
2. 该字段用于存储合同编号
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = 'e2d6da7f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加 contract_number 字段"""
    op.add_column(
        'contracts',
        sa.Column('contract_number', sa.String(100), nullable=True, comment='合同编号')
    )


def downgrade() -> None:
    """删除 contract_number 字段"""
    op.drop_column('contracts', 'contract_number')
