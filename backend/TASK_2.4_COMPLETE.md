# Task 2.4 完成报告 - 创建评论模型 (Comment)

## 任务概述

创建 Comment 模型用于数据库,支持评论和嵌套回复功能。

## 执行结果

✅ **任务已完成** - Comment 模型已经存在并完全符合设计规范

## 实施详情

### 1. 模型文件位置

- **文件路径**: `/backend/app/models/comment.py`
- **状态**: ✅ 已存在并完整实现

### 2. 模型结构验证

Comment 模型包含以下字段,完全符合设计文档要求:

#### 主键
- `id`: UUID - 评论ID (主键)

#### 关联字段
- `contract_id`: UUID - 合同ID (外键 -> contracts.id, CASCADE删除)
- `review_id`: UUID (可选) - 评审记录ID (外键 -> reviews.id, CASCADE删除)
- `parent_comment_id`: UUID (可选) - 父评论ID (外键 -> comments.id, CASCADE删除,支持嵌套回复)
- `author_id`: UUID - 作者ID (外键 -> users.id, CASCADE删除)

#### 内容字段
- `content`: Text - 评论内容 (必填)

#### 点赞功能
- `likes`: Integer - 点赞数 (默认0)
- `liked_by`: ARRAY(String) - 点赞用户ID列表 (默认空数组)

#### 时间戳
- `created_at`: DateTime - 创建时间 (自动设置)
- `updated_at`: DateTime - 更新时间 (自动更新)

### 3. 关系定义

模型定义了以下 SQLAlchemy 关系:

```python
# 关联合同
contract: Mapped["Contract"] = relationship("Contract", foreign_keys=[contract_id], lazy="joined")

# 关联评审记录
review: Mapped["Review"] = relationship("Review", foreign_keys=[review_id], lazy="joined")

# 关联作者
author: Mapped["User"] = relationship("User", foreign_keys=[author_id], lazy="joined")

# 自引用关系(嵌套回复)
parent_comment: Mapped["Comment"] = relationship(
    "Comment",
    foreign_keys=[parent_comment_id],
    remote_side=[id],
    lazy="joined"
)
```

### 4. 索引配置

模型配置了以下索引以优化查询性能:

- `ix_comments_contract_id` - 按合同ID查询
- `ix_comments_review_id` - 按评审记录ID查询
- `ix_comments_parent_comment_id` - 按父评论ID查询
- `ix_comments_created_at_desc` - 按创建时间倒序排列

### 5. 数据库迁移

Comment 表已包含在初始数据库迁移中:

- **迁移文件**: `/backend/alembic/versions/001_create_initial_database_models.py`
- **表名**: `comments`
- **状态**: ✅ 已定义

迁移包含:
- 所有字段定义
- 外键约束 (CASCADE 删除)
- 索引创建
- 默认值设置

### 6. 模型导出

Comment 模型已在 `/backend/app/models/__init__.py` 中正确导出:

```python
from app.models.comment import Comment

__all__ = [
    "Base",
    "User",
    "Contract",
    "ContractStatus",
    "Review",
    "ReviewStatus",
    "Comment",  # ✅ 已导出
    "Attachment",
    "AISummary",
    "ApprovalStatus",
]
```

### 7. 测试文件

创建了单元测试文件验证模型功能:

- **文件路径**: `/backend/tests/test_comment_model.py`
- **测试覆盖**:
  - ✅ 评论实例创建
  - ✅ 关联评审记录的评论
  - ✅ 嵌套回复功能
  - ✅ 点赞功能
  - ✅ 字符串表示 (repr)
  - ✅ 表名验证
  - ✅ 默认值验证

## 设计规范符合性检查

### 与 design.md 对比

| 设计要求 | 实现状态 | 说明 |
|---------|---------|------|
| UUID 主键 | ✅ | 使用 postgresql.UUID(as_uuid=True) |
| contract_id 外键 | ✅ | 关联 contracts.id, CASCADE 删除 |
| review_id 可选外键 | ✅ | 支持回复评审意见 |
| parent_comment_id 可选外键 | ✅ | 支持嵌套回复 |
| author_id 外键 | ✅ | 关联 users.id |
| content 文本字段 | ✅ | 使用 Text 类型 |
| likes 点赞数 | ✅ | Integer 类型,默认 0 |
| liked_by 点赞用户列表 | ✅ | ARRAY(String) 类型 |
| created_at 时间戳 | ✅ | DateTime,自动设置 |
| updated_at 时间戳 | ✅ | DateTime,自动更新 |
| 索引优化 | ✅ | 4 个索引,包括倒序时间索引 |

### 与 requirements.md 对比

| 需求 | 实现状态 | 说明 |
|-----|---------|------|
| 需求 5.1: 支持评论 | ✅ | content 字段存储评论内容 |
| 需求 5.2: 支持回复评审意见 | ✅ | review_id 字段关联评审记录 |
| 需求 5.3: 支持嵌套回复 | ✅ | parent_comment_id 支持多层回复 |
| 需求 5.4: 显示作者信息 | ✅ | author_id 关联用户表 |
| 需求 5.5: 支持点赞 | ✅ | likes 和 liked_by 字段 |
| 需求 5.6: 时间戳记录 | ✅ | created_at 和 updated_at |

## 功能特性

### 1. 灵活的评论类型

Comment 模型支持三种评论类型:

1. **独立评论**: 只设置 contract_id,不关联评审或父评论
2. **评审回复**: 设置 review_id,回复特定评审意见
3. **嵌套回复**: 设置 parent_comment_id,回复其他评论

### 2. 点赞功能

- 使用 PostgreSQL ARRAY 类型存储点赞用户ID
- 支持快速查询某用户是否点赞
- 点赞数与点赞用户列表分离存储,提高查询效率

### 3. 级联删除

所有外键都配置了 CASCADE 删除:
- 删除合同时,自动删除所有相关评论
- 删除评审记录时,自动删除相关评论
- 删除父评论时,自动删除所有子回复
- 删除用户时,自动删除其所有评论

### 4. 查询优化

索引配置优化了常见查询场景:
- 按合同查询所有评论
- 按评审记录查询回复
- 按父评论查询子回复
- 按时间倒序排列(时间线展示)

## 数据库 Schema

```sql
CREATE TABLE comments (
    id UUID PRIMARY KEY,
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    review_id UUID REFERENCES reviews(id) ON DELETE CASCADE,
    parent_comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    likes INTEGER NOT NULL DEFAULT 0,
    liked_by TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_comments_contract_id ON comments(contract_id);
CREATE INDEX ix_comments_review_id ON comments(review_id);
CREATE INDEX ix_comments_parent_comment_id ON comments(parent_comment_id);
CREATE INDEX ix_comments_created_at_desc ON comments(created_at DESC);
```

## 使用示例

### 1. 创建独立评论

```python
from app.models.comment import Comment
import uuid

comment = Comment(
    id=uuid.uuid4(),
    contract_id=contract_id,
    author_id=user_id,
    content="这是一条评论",
    likes=0,
    liked_by=[]
)
```

### 2. 回复评审意见

```python
reply = Comment(
    id=uuid.uuid4(),
    contract_id=contract_id,
    review_id=review_id,  # 关联评审记录
    author_id=user_id,
    content="回复评审意见",
    likes=0,
    liked_by=[]
)
```

### 3. 嵌套回复

```python
nested_reply = Comment(
    id=uuid.uuid4(),
    contract_id=contract_id,
    parent_comment_id=parent_comment_id,  # 关联父评论
    author_id=user_id,
    content="回复评论",
    likes=0,
    liked_by=[]
)
```

### 4. 点赞操作

```python
# 添加点赞
comment.likes += 1
comment.liked_by.append(str(user_id))

# 取消点赞
comment.likes -= 1
comment.liked_by.remove(str(user_id))
```

## 验证清单

- [x] 模型文件存在且完整
- [x] 所有必需字段已定义
- [x] 外键关系正确配置
- [x] 索引已创建
- [x] 数据库迁移已定义
- [x] 模型已导出到 __init__.py
- [x] 支持嵌套回复
- [x] 支持点赞功能
- [x] 级联删除配置正确
- [x] 测试文件已创建

## 后续任务

Comment 模型已完全实现,可以继续以下任务:

1. **Task 5.1**: 实现评论 API 端点
   - POST /api/contracts/:id/comments - 创建评论
   - GET /api/contracts/:id/comments - 获取评论列表
   - POST /api/comments/:id/like - 点赞评论

2. **Task 5.2**: 实现评论服务层
   - CommentService.create_comment()
   - CommentService.get_comments()
   - CommentService.toggle_like()

3. **Task 5.3**: 实现 WebSocket 实时通知
   - comment:added 事件
   - reply:added 事件
   - like:updated 事件

## 总结

Task 2.4 已成功完成。Comment 模型已完整实现并符合所有设计规范和需求。模型支持:

- ✅ 独立评论
- ✅ 评审意见回复
- ✅ 嵌套回复(多层)
- ✅ 点赞功能
- ✅ 级联删除
- ✅ 查询优化

模型已准备好用于后续的 API 开发和业务逻辑实现。
