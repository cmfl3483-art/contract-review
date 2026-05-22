# Task 11.3 Implementation Summary

## 任务描述
实现附件分组逻辑 (Implement Attachment Grouping Logic)

## 实现内容

### 1. 按文件名分组附件的方法 (Group Attachments by Filename)

**方法名**: `group_attachments_by_filename`

**功能**: 将附件列表按文件名分组,相同文件名的附件归为一组

**实现位置**: `/backend/app/services/file_service.py` (行 318-333)

**输入**: 
- `attachments: List[Attachment]` - 附件列表

**输出**: 
- `Dict[str, List[Attachment]]` - 按文件名分组的字典

**实现逻辑**:
```python
def group_attachments_by_filename(
    self,
    attachments: List[Attachment]
) -> Dict[str, List[Attachment]]:
    grouped = defaultdict(list)
    
    for attachment in attachments:
        grouped[attachment.file_name].append(attachment)
    
    return dict(grouped)
```

### 2. 按时间倒序排列版本的方法 (Sort Versions by Time Descending)

**方法名**: `sort_versions_by_time_desc`

**功能**: 将同一文件的多个版本按创建时间倒序排列(最新的在前)

**实现位置**: `/backend/app/services/file_service.py` (行 335-348)

**输入**: 
- `versions: List[Attachment]` - 同一文件的版本列表

**输出**: 
- `List[Attachment]` - 按创建时间倒序排列的版本列表

**实现逻辑**:
```python
def sort_versions_by_time_desc(
    self,
    versions: List[Attachment]
) -> List[Attachment]:
    return sorted(versions, key=lambda v: v.created_at, reverse=True)
```

### 3. 标记最新版本的方法 (Mark Latest Version)

**方法名**: `mark_latest_version`

**功能**: 为版本列表中的每个版本添加 `is_latest` 标记,第一个版本(最新)标记为 True

**实现位置**: `/backend/app/services/file_service.py` (行 350-381)

**输入**: 
- `versions: List[Attachment]` - 已按时间倒序排列的版本列表

**输出**: 
- `List[Dict[str, Any]]` - 包含 is_latest 标记的版本字典列表

**实现逻辑**:
```python
def mark_latest_version(
    self,
    versions: List[Attachment]
) -> List[Dict[str, Any]]:
    result = []
    
    for i, version in enumerate(versions):
        version_dict = {
            "id": str(version.id),
            "file_name": version.file_name,
            "version": version.version,
            "file_size": version.file_size,
            "mime_type": version.mime_type,
            "storage_key": version.storage_key,
            "uploader_id": str(version.uploader_id),
            "uploader_name": version.uploader.name if version.uploader else None,
            "created_at": version.created_at.isoformat(),
            "is_latest": i == 0  # 第一个版本是最新的
        }
        result.append(version_dict)
    
    return result
```

### 4. 综合方法 - 获取分组附件 (Get Grouped Attachments)

**方法名**: `get_grouped_attachments`

**功能**: 综合使用上述三个方法,获取合同的所有附件并进行完整的分组、排序和标记处理

**实现位置**: `/backend/app/services/file_service.py` (行 383-428)

**输入**: 
- `contract_id: str` - 合同ID
- `db: AsyncSession` - 数据库会话

**输出**: 
- `List[Dict[str, Any]]` - 分组后的附件列表

**输出格式**:
```python
[
    {
        "file_name": "采购清单.pdf",
        "version_count": 3,
        "versions": [
            {
                "id": "uuid",
                "file_name": "采购清单.pdf",
                "version": "v3.0",
                "file_size": 1048576,
                "mime_type": "application/pdf",
                "storage_key": "contract-123/采购清单.pdf/v3.0/uuid.pdf",
                "uploader_id": "uuid",
                "uploader_name": "张三",
                "created_at": "2025-05-20T10:00:00",
                "is_latest": True
            },
            {
                "id": "uuid",
                "version": "v2.0",
                "is_latest": False,
                ...
            }
        ],
        "latest_upload_time": datetime(2025, 5, 20, 10, 0, 0)
    },
    ...
]
```

**实现逻辑**:
1. 获取合同的所有附件
2. 按文件名分组
3. 对每个分组:
   - 按时间倒序排列版本
   - 标记最新版本
   - 记录最新上传时间
4. 按最新上传时间倒序排列不同文件组

## 需求覆盖

本实现满足以下需求:

- **需求 3.4**: THE System SHALL 按文件名分组显示附件,每组显示版本数量
- **需求 3.5**: THE System SHALL 为每个附件版本显示版本号、上传时间和上传人
- **需求 3.6**: THE System SHALL 按时间倒序排列同一文件的多个版本
- **需求 3.7**: THE System SHALL 为最新版本标记"最新"标签
- **需求 3.8**: THE System SHALL 按最新上传时间倒序排列不同文件组

## 测试

已创建完整的单元测试文件: `/backend/tests/services/test_file_service_grouping.py`

测试覆盖:
- ✅ 按文件名分组功能
- ✅ 按时间倒序排列功能
- ✅ 标记最新版本功能
- ✅ 综合分组功能
- ✅ 空附件列表处理
- ✅ 单文件多版本场景
- ✅ 多文件多版本场景

## 使用示例

```python
from app.services.file_service import FileService
from app.core.database import get_db

file_service = FileService()

# 获取合同的分组附件
async with get_db() as db:
    grouped_attachments = await file_service.get_grouped_attachments(
        contract_id="contract-123",
        db=db
    )
    
    # 遍历文件组
    for group in grouped_attachments:
        print(f"文件名: {group['file_name']}")
        print(f"版本数: {group['version_count']}")
        
        # 遍历版本
        for version in group['versions']:
            latest_tag = "【最新】" if version['is_latest'] else ""
            print(f"  {latest_tag}{version['version']} - {version['uploader_name']} - {version['created_at']}")
```

## 依赖

- `typing.List`, `typing.Dict`, `typing.Any` - 类型注解
- `collections.defaultdict` - 分组实现
- `app.models.attachment.Attachment` - 附件模型
- `sqlalchemy.ext.asyncio.AsyncSession` - 异步数据库会话

## 注意事项

1. **性能考虑**: 
   - 使用了数据库索引 `ix_attachments_filename_created_at` 来优化查询性能
   - 分组和排序在内存中进行,适合中小规模数据

2. **时区处理**: 
   - 所有时间使用 UTC 时间
   - 前端需要根据用户时区进行转换

3. **空值处理**: 
   - 如果合同没有附件,返回空列表 `[]`
   - 如果上传人信息不存在,`uploader_name` 为 `None`

4. **扩展性**: 
   - 方法设计为独立的小函数,便于单独测试和复用
   - 可以轻松添加其他排序或过滤逻辑

## 完成状态

✅ 任务已完成

- [x] 实现按文件名分组附件的方法
- [x] 实现按时间倒序排列版本的方法
- [x] 实现标记最新版本的方法
- [x] 创建综合方法整合所有功能
- [x] 编写完整的单元测试
- [x] 满足所有相关需求 (3.4-3.8)
