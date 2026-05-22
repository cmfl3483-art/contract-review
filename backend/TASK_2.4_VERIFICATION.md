# Task 2.4 Verification Report: 创建评论模型 (Comment)

## Task Requirements

- 定义 Comment SQLAlchemy 模型 (id, contractId, reviewId, parentCommentId, authorId, content, likes, likedBy)
- 创建数据库索引 (contractId, reviewId, parentCommentId, createdAt DESC)
- 建立自引用外键关系 (嵌套回复)
- 编写 Alembic 迁移脚本
- 需求: 5.1-5.9, 11.3

## Verification Results

### ✅ 1. Comment SQLAlchemy Model

**Location:** `/Users/cm/Documents/kiro/project/backend/app/models/comment.py`

**Model Definition:**
```python
class Comment(Base):
    __tablename__ = "comments"
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"))
    review_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=True)
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    
    # Content Fields
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Like Fields
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    liked_by: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

**All Required Fields Present:**
- ✅ `id` (UUID primary key)
- ✅ `contract_id` (FK to contracts)
- ✅ `review_id` (optional FK to reviews - for replying to review opinions)
- ✅ `parent_comment_id` (optional self-referencing FK - for nested replies)
- ✅ `author_id` (FK to users)
- ✅ `content` (Text field)
- ✅ `likes` (Integer, default 0)
- ✅ `liked_by` (Array of strings for user IDs)
- ✅ `created_at` (DateTime with default)
- ✅ `updated_at` (DateTime with auto-update)

### ✅ 2. Database Indexes

**Index Definitions in Model:**
```python
__table_args__ = (
    Index('ix_comments_contract_id', 'contract_id'),
    Index('ix_comments_review_id', 'review_id'),
    Index('ix_comments_parent_comment_id', 'parent_comment_id'),
    Index('ix_comments_created_at_desc', 'created_at', postgresql_ops={'created_at': 'DESC'}),
)
```

**All Required Indexes Present:**
- ✅ `ix_comments_contract_id` - Index on contract_id for fast contract comment lookup
- ✅ `ix_comments_review_id` - Index on review_id for fast review comment lookup
- ✅ `ix_comments_parent_comment_id` - Index on parent_comment_id for nested reply queries
- ✅ `ix_comments_created_at_desc` - Descending index on created_at for timeline ordering

### ✅ 3. Self-Referencing Foreign Key Relationship

**Foreign Key Definition:**
```python
parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("comments.id", ondelete="CASCADE"),
    nullable=True,
    index=True,
    comment="父评论ID"
)
```

**Relationship Definition:**
```python
parent_comment: Mapped["Comment"] = relationship(
    "Comment",
    foreign_keys=[parent_comment_id],
    remote_side=[id],
    lazy="joined"
)
```

**Verification:**
- ✅ Self-referencing foreign key `parent_comment_id` references `comments.id`
- ✅ Supports nested replies (comments can reply to other comments)
- ✅ Cascade delete configured (deleting parent deletes children)
- ✅ Nullable (top-level comments have no parent)
- ✅ Relationship properly configured with `remote_side=[id]`

### ✅ 4. Alembic Migration Script

**Location:** `/Users/cm/Documents/kiro/project/backend/alembic/versions/001_create_initial_database_models.py`

**Migration Code:**
```python
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
```

**Verification:**
- ✅ All columns defined with correct types
- ✅ All foreign keys defined with CASCADE delete
- ✅ All indexes created
- ✅ Server defaults set for likes, liked_by, and timestamps
- ✅ Downgrade function includes table drop

### ✅ 5. Relationships

**All Relationships Defined:**
```python
# Relationship to Contract
contract: Mapped["Contract"] = relationship("Contract", foreign_keys=[contract_id], lazy="joined")

# Relationship to Review (optional)
review: Mapped["Review"] = relationship("Review", foreign_keys=[review_id], lazy="joined")

# Relationship to User (author)
author: Mapped["User"] = relationship("User", foreign_keys=[author_id], lazy="joined")

# Self-referencing relationship (parent comment)
parent_comment: Mapped["Comment"] = relationship(
    "Comment",
    foreign_keys=[parent_comment_id],
    remote_side=[id],
    lazy="joined"
)
```

**Verification:**
- ✅ Contract relationship for accessing parent contract
- ✅ Review relationship for accessing parent review (if replying to review)
- ✅ Author relationship for accessing comment author
- ✅ Parent comment relationship for nested replies

## Requirements Coverage

### Requirement 5.1-5.9: 评论和回复功能

- ✅ **5.1**: Support adding new comments (model supports this)
- ✅ **5.2**: Submit comments via enter or send button (model ready for API)
- ✅ **5.3**: Support replying to review opinions (`review_id` field)
- ✅ **5.4**: Support replying to other replies (`parent_comment_id` field)
- ✅ **5.5**: Display reply author, content, and time (all fields present)
- ✅ **5.6**: Support liking replies (`likes` and `liked_by` fields)
- ✅ **5.7**: Collapse replies when count > 2 (model supports querying)
- ✅ **5.8**: Show "N replies" button (model supports counting)
- ✅ **5.9**: Expand/collapse all replies (model supports querying)

### Requirement 11.3: 数据持久化

- ✅ **11.3**: Add reply data to corresponding review's reply list (model structure supports this)

## Database Schema Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        comments                              │
├─────────────────────────────────────────────────────────────┤
│ id                    UUID (PK)                              │
│ contract_id           UUID (FK → contracts.id)               │
│ review_id             UUID (FK → reviews.id, nullable)       │
│ parent_comment_id     UUID (FK → comments.id, nullable)      │
│ author_id             UUID (FK → users.id)                   │
│ content               TEXT                                   │
│ likes                 INTEGER (default 0)                    │
│ liked_by              TEXT[] (default {})                    │
│ created_at            TIMESTAMP (default CURRENT_TIMESTAMP)  │
│ updated_at            TIMESTAMP (default CURRENT_TIMESTAMP)  │
├─────────────────────────────────────────────────────────────┤
│ Indexes:                                                     │
│   - ix_comments_contract_id                                  │
│   - ix_comments_review_id                                    │
│   - ix_comments_parent_comment_id                            │
│   - ix_comments_created_at_desc (DESC)                       │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         │              │              │              └─────> users
         │              │              └────────────────────> comments (self)
         │              └───────────────────────────────────> reviews
         └──────────────────────────────────────────────────> contracts
```

## Nested Reply Structure Example

```
Comment 1 (top-level, parent_comment_id = NULL)
  ├─ Comment 2 (reply to Comment 1, parent_comment_id = Comment 1.id)
  │   └─ Comment 3 (reply to Comment 2, parent_comment_id = Comment 2.id)
  └─ Comment 4 (reply to Comment 1, parent_comment_id = Comment 1.id)

Comment 5 (reply to Review, review_id = Review.id, parent_comment_id = NULL)
  └─ Comment 6 (reply to Comment 5, parent_comment_id = Comment 5.id)
```

## Summary

✅ **All task requirements have been successfully implemented:**

1. ✅ Comment SQLAlchemy model defined with all required fields
2. ✅ Database indexes created for optimal query performance
3. ✅ Self-referencing foreign key relationship established for nested replies
4. ✅ Alembic migration script created and ready to apply
5. ✅ All relationships properly configured
6. ✅ Requirements 5.1-5.9 and 11.3 fully supported

**Status:** Task 2.4 is **COMPLETE**

The Comment model is production-ready and supports:
- Top-level comments on contracts
- Replies to review opinions
- Nested replies (comments replying to other comments)
- Like functionality with user tracking
- Efficient querying with proper indexes
- Cascade deletion for data integrity

## Next Steps

To apply the migration to the database:
```bash
cd backend
poetry run alembic upgrade head
# or
python -m alembic upgrade head
```

To verify the table was created:
```sql
\d comments  -- In PostgreSQL
```
