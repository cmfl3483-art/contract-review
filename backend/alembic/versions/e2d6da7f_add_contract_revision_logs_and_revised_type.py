"""add contract_revision_logs table and contract_revised notification type

Revision ID: e2d6da7f
Revises: 728d1a52
Create Date: 2025-07-15 09:00:00.000000

新建 contract_revision_logs 表用于记录合同发起人对关键字段
（name / description / attachment）的修改审计日志；同时为
notification_type 枚举追加 'contract_revised' 取值，使通知系统
可以为合同重审场景投递新的通知类型。

设计原则：
- 全部使用原生 SQL 执行，避免 SQLAlchemy 在迁移过程中自动尝试创建
  / 删除已存在的枚举类型导致冲突（与 728d1a52 一致的写法）。
- PostgreSQL 不支持移除单个枚举值，downgrade 不回退枚举扩展。
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e2d6da7f'
down_revision = '728d1a52'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """扩展 notification_type 枚举并新建 contract_revision_logs 表 + 索引"""
    # 1. 扩展 notification_type 枚举（必须在事务外被 PostgreSQL 接受；
    #    Alembic 在默认事务中执行，但 ADD VALUE IF NOT EXISTS 在多数
    #    PostgreSQL 版本中允许在事务内执行）
    op.execute(
        "ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'contract_revised'"
    )

    # 2. 新建 contract_revision_logs 表
    op.execute("""
        CREATE TABLE IF NOT EXISTS contract_revision_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
            revised_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            changed_fields VARCHAR[] NOT NULL,
            revised_at TIMESTAMP NOT NULL DEFAULT now()
        );
    """)

    # 3. 复合索引：按合同分组并按时间倒序检索修改历史
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_revision_logs_contract_revised_at
        ON contract_revision_logs (contract_id, revised_at DESC);
    """)

    # 4. 单列索引：与模型层 contract_id 字段 index=True 声明保持一致
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_revision_logs_contract_id
        ON contract_revision_logs (contract_id);
    """)


def downgrade() -> None:
    """删除 contract_revision_logs 表（PostgreSQL 不支持移除单个枚举值，保留）"""
    op.execute("DROP TABLE IF EXISTS contract_revision_logs")
