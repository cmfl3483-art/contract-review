"""add performance indexes

Revision ID: 002
Revises: 001
Create Date: 2025-01-10 10:00:00.000000

添加性能优化索引:
1. 复合索引用于常见查询模式
2. 部分索引用于特定筛选条件
3. 覆盖索引减少回表查询
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加性能优化索引"""
    
    # 1. 合同表复合索引
    # 用于"待我处理"筛选 + 时间排序
    op.create_index(
        'ix_contracts_status_created_at',
        'contracts',
        ['status', sa.text('created_at DESC')],
        postgresql_ops={'created_at': 'DESC'}
    )
    
    # 用于发起人筛选 + 时间排序
    op.create_index(
        'ix_contracts_initiator_created_at',
        'contracts',
        ['initiator_id', sa.text('created_at DESC')],
        postgresql_ops={'created_at': 'DESC'}
    )
    
    # 2. 评审表复合索引
    # 用于查询用户的待处理评审项(最常用的查询)
    op.create_index(
        'ix_reviews_reviewer_status',
        'reviews',
        ['reviewer_id', 'status']
    )
    
    # 用于查询合同的评审记录 + 时间排序
    op.create_index(
        'ix_reviews_contract_created_at',
        'reviews',
        ['contract_id', sa.text('created_at DESC')],
        postgresql_ops={'created_at': 'DESC'}
    )
    
    # 用于查询待处理评审项的合同列表
    op.create_index(
        'ix_reviews_reviewer_status_contract',
        'reviews',
        ['reviewer_id', 'status', 'contract_id']
    )
    
    # 3. 评论表复合索引
    # 用于查询合同的评论 + 时间排序
    op.create_index(
        'ix_comments_contract_created_at',
        'comments',
        ['contract_id', sa.text('created_at DESC')],
        postgresql_ops={'created_at': 'DESC'}
    )
    
    # 用于查询评审的评论
    op.create_index(
        'ix_comments_review_created_at',
        'comments',
        ['review_id', sa.text('created_at DESC')],
        postgresql_ops={'created_at': 'DESC'},
        postgresql_where=sa.text('review_id IS NOT NULL')
    )
    
    # 用于查询嵌套回复
    op.create_index(
        'ix_comments_parent_created_at',
        'comments',
        ['parent_comment_id', sa.text('created_at DESC')],
        postgresql_ops={'created_at': 'DESC'},
        postgresql_where=sa.text('parent_comment_id IS NOT NULL')
    )
    
    # 4. 附件表复合索引
    # 用于按文件名分组和版本排序
    op.create_index(
        'ix_attachments_contract_filename_created',
        'attachments',
        ['contract_id', 'file_name', sa.text('created_at DESC')],
        postgresql_ops={'created_at': 'DESC'}
    )
    
    # 5. AI总结表索引(如果表存在)
    # 用于快速查询合同的AI总结
    op.create_index(
        'ix_ai_summaries_contract_updated',
        'ai_summaries',
        ['contract_id', sa.text('updated_at DESC')],
        postgresql_ops={'updated_at': 'DESC'}
    )


def downgrade() -> None:
    """删除性能优化索引"""
    
    # 删除所有添加的索引
    op.drop_index('ix_ai_summaries_contract_updated', table_name='ai_summaries')
    op.drop_index('ix_attachments_contract_filename_created', table_name='attachments')
    op.drop_index('ix_comments_parent_created_at', table_name='comments')
    op.drop_index('ix_comments_review_created_at', table_name='comments')
    op.drop_index('ix_comments_contract_created_at', table_name='comments')
    op.drop_index('ix_reviews_reviewer_status_contract', table_name='reviews')
    op.drop_index('ix_reviews_contract_created_at', table_name='reviews')
    op.drop_index('ix_reviews_reviewer_status', table_name='reviews')
    op.drop_index('ix_contracts_initiator_created_at', table_name='contracts')
    op.drop_index('ix_contracts_status_created_at', table_name='contracts')
