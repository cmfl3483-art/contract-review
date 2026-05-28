"""merge contract_number and compliance heads

Revision ID: 005
Revises: 004, f3a1b2c4
Create Date: 2026-05-28 09:00:00.000000

合并两个并行迁移分支：
- 004: add contract_number field to contracts
- f3a1b2c4: add compliance tables
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = ('004', 'f3a1b2c4')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
