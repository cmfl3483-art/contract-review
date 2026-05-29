"""allow multiple active compliance rule sets

去掉 compliance_rule_sets 上的 partial unique index，允许同时存在多条 is_active=true 的记录。
业务层保证至少 1 条 active（通过 update_rule_set 拒绝把最后一条 active 改为 inactive）。
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_compliance_rule_sets_one_active")


def downgrade() -> None:
    # 回滚需要重新创建唯一约束。如果当前数据有多条 active，会失败 —— 需要先手动整理数据
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_compliance_rule_sets_one_active
        ON compliance_rule_sets (is_active)
        WHERE is_active = true
    """)
