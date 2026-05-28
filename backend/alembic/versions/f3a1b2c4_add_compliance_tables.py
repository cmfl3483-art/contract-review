"""add compliance tables

Revision ID: f3a1b2c4
Revises: e2d6da7f
Create Date: 2025-07-20 10:00:00.000000

新建合规检查相关的 3 个枚举类型和 3 张表：
- rule_type ENUM ('number','name','description','file')
- rule_severity ENUM ('must','should')
- compliance_check_status ENUM ('pending','completed','failed')
- compliance_rule_sets
- compliance_rules
- compliance_check_results

设计原则：
- 使用原生 SQL 执行，避免 SQLAlchemy 在迁移过程中自动尝试创建/删除已存在的枚举类型
- compliance_check_results 不含指向 contracts 表的外键（Requirement 6.7）
- partial unique index uq_compliance_rule_sets_one_active 保证同一时刻最多一个 active 规则集合
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f3a1b2c4'
down_revision = 'e2d6da7f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 创建枚举类型
    op.execute(
        "CREATE TYPE rule_type AS ENUM ('number','name','description','file')"
    )
    op.execute(
        "CREATE TYPE rule_severity AS ENUM ('must','should')"
    )
    op.execute(
        "CREATE TYPE compliance_check_status AS ENUM ('pending','completed','failed')"
    )

    # 2. 创建 compliance_rule_sets 表
    op.execute("""
        CREATE TABLE compliance_rule_sets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL,
            description VARCHAR(1000),
            is_active BOOLEAN NOT NULL DEFAULT false,
            created_by UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)

    # is_active 普通索引（加速 WHERE is_active = true 查询）
    op.execute("""
        CREATE INDEX ix_compliance_rule_sets_is_active
        ON compliance_rule_sets (is_active)
    """)

    # partial unique index：同一时刻最多一个 is_active=true 的规则集合
    op.execute("""
        CREATE UNIQUE INDEX uq_compliance_rule_sets_one_active
        ON compliance_rule_sets (is_active)
        WHERE is_active = true
    """)

    # 3. 创建 compliance_rules 表
    op.execute("""
        CREATE TABLE compliance_rules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            rule_set_id UUID NOT NULL REFERENCES compliance_rule_sets(id) ON DELETE CASCADE,
            rule_type rule_type NOT NULL,
            title VARCHAR(100) NOT NULL,
            requirement VARCHAR(2000) NOT NULL,
            severity rule_severity NOT NULL DEFAULT 'must',
            "order" INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)

    # 复合索引：加速按 rule_set_id 查询并按 rule_type/order/created_at 排序
    op.execute("""
        CREATE INDEX ix_compliance_rules_set_id_order
        ON compliance_rules (rule_set_id, rule_type, "order", created_at)
    """)

    # rule_type 单列索引
    op.execute("""
        CREATE INDEX ix_compliance_rules_rule_type
        ON compliance_rules (rule_type)
    """)

    # 4. 创建 compliance_check_results 表（无 contracts 外键，Requirement 6.7）
    op.execute("""
        CREATE TABLE compliance_check_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            requested_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rule_set_id UUID REFERENCES compliance_rule_sets(id) ON DELETE SET NULL,
            status compliance_check_status NOT NULL DEFAULT 'pending',
            file_storage_key VARCHAR(500) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_size BIGINT NOT NULL,
            file_mime_type VARCHAR(100) NOT NULL,
            extracted_text TEXT NOT NULL DEFAULT '',
            text_truncated BOOLEAN NOT NULL DEFAULT false,
            number_draft VARCHAR(100),
            name_draft VARCHAR(200),
            description_draft VARCHAR(2000),
            violations JSONB NOT NULL DEFAULT '[]',
            suggested_name VARCHAR(200),
            suggested_description VARCHAR(2000),
            compliance_score INTEGER,
            error_message VARCHAR(200),
            requested_at TIMESTAMP NOT NULL DEFAULT now(),
            completed_at TIMESTAMP
        )
    """)

    # 复合索引：历史列表分页（按 requested_by + requested_at DESC）
    op.execute("""
        CREATE INDEX ix_compliance_check_results_requester_time
        ON compliance_check_results (requested_by, requested_at DESC)
    """)

    # status 单列索引
    op.execute("""
        CREATE INDEX ix_compliance_check_results_status
        ON compliance_check_results (status)
    """)

    # requested_by 单列索引
    op.execute("""
        CREATE INDEX ix_compliance_check_results_requested_by
        ON compliance_check_results (requested_by)
    """)


def downgrade() -> None:
    # 逆序删除：先删索引，再删表，最后删枚举类型

    # compliance_check_results 索引
    op.execute("DROP INDEX IF EXISTS ix_compliance_check_results_requested_by")
    op.execute("DROP INDEX IF EXISTS ix_compliance_check_results_status")
    op.execute("DROP INDEX IF EXISTS ix_compliance_check_results_requester_time")
    op.execute("DROP TABLE IF EXISTS compliance_check_results")

    # compliance_rules 索引
    op.execute("DROP INDEX IF EXISTS ix_compliance_rules_rule_type")
    op.execute("DROP INDEX IF EXISTS ix_compliance_rules_set_id_order")
    op.execute("DROP TABLE IF EXISTS compliance_rules")

    # compliance_rule_sets 索引
    op.execute("DROP INDEX IF EXISTS uq_compliance_rule_sets_one_active")
    op.execute("DROP INDEX IF EXISTS ix_compliance_rule_sets_is_active")
    op.execute("DROP TABLE IF EXISTS compliance_rule_sets")

    # 枚举类型
    op.execute("DROP TYPE IF EXISTS compliance_check_status")
    op.execute("DROP TYPE IF EXISTS rule_severity")
    op.execute("DROP TYPE IF EXISTS rule_type")
