"""Create initial database models

Revision ID: 001
Revises: 
Create Date: 2025-01-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建枚举类型
    contract_status_enum = postgresql.ENUM('progress', 'completed', name='contract_status', create_type=False)
    contract_status_enum.create(op.get_bind(), checkfirst=True)
    
    review_status_enum = postgresql.ENUM('pending', 'reviewing', 'approved', name='review_status', create_type=False)
    review_status_enum.create(op.get_bind(), checkfirst=True)
    
    approval_status_enum = postgresql.ENUM('completed', 'in_progress', name='approval_status', create_type=False)
    approval_status_enum.create(op.get_bind(), checkfirst=True)
    
    # 创建 users 表
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, comment='用户ID'),
        sa.Column('dingtalk_user_id', sa.String(100), nullable=False, unique=True, comment='钉钉用户ID'),
        sa.Column('dingtalk_union_id', sa.String(100), nullable=True, comment='钉钉UnionID'),
        sa.Column('name', sa.String(100), nullable=False, comment='用户姓名'),
        sa.Column('role', sa.String(50), nullable=False, comment='用户角色(销售/法务/财务/业务/运营/人事)'),
        sa.Column('email', sa.String(255), nullable=True, comment='邮箱'),
        sa.Column('mobile', sa.String(20), nullable=True, comment='手机号'),
        sa.Column('avatar', sa.String(500), nullable=True, comment='头像URL'),
        sa.Column('department', sa.String(100), nullable=True, comment='部门'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
    )
    op.create_index('ix_users_dingtalk_user_id', 'users', ['dingtalk_user_id'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])
    
    # 创建 contracts 表
    op.create_table(
        'contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, comment='合同ID'),
        sa.Column('name', sa.String(255), nullable=False, comment='合同名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='合同描述'),
        sa.Column('status', contract_status_enum, nullable=False, server_default='progress', comment='合同状态'),
        sa.Column('initiator_id', postgresql.UUID(as_uuid=True), nullable=False, comment='发起人ID'),
        sa.Column('cc_users', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}', comment='抄送人ID列表'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['initiator_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_contracts_initiator_id', 'contracts', ['initiator_id'])
    op.create_index('ix_contracts_status', 'contracts', ['status'])
    op.create_index('ix_contracts_created_at_desc', 'contracts', [sa.text('created_at DESC')])
    
    # 创建 reviews 表
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, comment='评审记录ID'),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), nullable=False, comment='合同ID'),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=False, comment='评审人ID'),
        sa.Column('role', sa.String(50), nullable=False, comment='评审人角色'),
        sa.Column('step', sa.String(100), nullable=False, comment='评审步骤(如法务初审)'),
        sa.Column('opinion', sa.Text(), nullable=True, comment='评审意见'),
        sa.Column('status', review_status_enum, nullable=False, server_default='pending', comment='评审状态'),
        sa.Column('likes', sa.Integer(), nullable=False, server_default='0', comment='点赞数'),
        sa.Column('liked_by', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}', comment='点赞用户ID列表'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_reviews_contract_id', 'reviews', ['contract_id'])
    op.create_index('ix_reviews_reviewer_id', 'reviews', ['reviewer_id'])
    op.create_index('ix_reviews_status', 'reviews', ['status'])
    op.create_index('ix_reviews_created_at_desc', 'reviews', [sa.text('created_at DESC')])
    
    # 创建 comments 表
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, comment='评论ID'),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), nullable=False, comment='合同ID'),
        sa.Column('review_id', postgresql.UUID(as_uuid=True), nullable=True, comment='评审记录ID'),
        sa.Column('parent_comment_id', postgresql.UUID(as_uuid=True), nullable=True, comment='父评论ID'),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False, comment='作者ID'),
        sa.Column('content', sa.Text(), nullable=False, comment='评论内容'),
        sa.Column('likes', sa.Integer(), nullable=False, server_default='0', comment='点赞数'),
        sa.Column('liked_by', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}', comment='点赞用户ID列表'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['review_id'], ['reviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_comments_contract_id', 'comments', ['contract_id'])
    op.create_index('ix_comments_review_id', 'comments', ['review_id'])
    op.create_index('ix_comments_parent_comment_id', 'comments', ['parent_comment_id'])
    op.create_index('ix_comments_created_at_desc', 'comments', [sa.text('created_at DESC')])
    
    # 创建 attachments 表
    op.create_table(
        'attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, comment='附件ID'),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), nullable=False, comment='合同ID'),
        sa.Column('file_name', sa.String(255), nullable=False, comment='文件名'),
        sa.Column('version', sa.String(50), nullable=False, comment='版本号'),
        sa.Column('file_size', sa.BigInteger(), nullable=False, comment='文件大小(字节)'),
        sa.Column('mime_type', sa.String(100), nullable=False, comment='MIME类型'),
        sa.Column('storage_key', sa.String(500), nullable=False, comment='MinIO存储键'),
        sa.Column('uploader_id', postgresql.UUID(as_uuid=True), nullable=False, comment='上传人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_attachments_contract_id', 'attachments', ['contract_id'])
    op.create_index('ix_attachments_filename_created_at', 'attachments', ['file_name', sa.text('created_at DESC')])
    
    # 创建 ai_summaries 表
    op.create_table(
        'ai_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, comment='AI总结ID'),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, comment='合同ID'),
        sa.Column('approval_status', approval_status_enum, nullable=False, comment='审批状态'),
        sa.Column('completed_count', sa.Integer(), nullable=False, server_default='0', comment='已完成审批人数'),
        sa.Column('total_count', sa.Integer(), nullable=False, server_default='0', comment='总审批人数'),
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0', comment='评审意见总数'),
        sa.Column('key_issues', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]', comment='关键问题列表'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_ai_summaries_contract_id', 'ai_summaries', ['contract_id'], unique=True)
    op.create_index('ix_ai_summaries_updated_at_desc', 'ai_summaries', [sa.text('updated_at DESC')])


def downgrade() -> None:
    # 删除表(按依赖关系逆序)
    op.drop_table('ai_summaries')
    op.drop_table('attachments')
    op.drop_table('comments')
    op.drop_table('reviews')
    op.drop_table('contracts')
    op.drop_table('users')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS approval_status')
    op.execute('DROP TYPE IF EXISTS review_status')
    op.execute('DROP TYPE IF EXISTS contract_status')
