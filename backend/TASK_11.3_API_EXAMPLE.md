# Task 11.3 - API Integration Example

## API端点示例

以下是如何在API端点中使用新实现的附件分组逻辑:

### 1. 获取合同详情API (包含分组附件)

```python
# app/routes/contracts.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.services.file_service import FileService
from app.services.contract_service import ContractService

router = APIRouter()

@router.get("/contracts/{contract_id}")
async def get_contract_detail(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取合同详情,包含分组的附件信息
    
    响应格式:
    {
        "success": true,
        "data": {
            "contract": {
                "id": "uuid",
                "name": "采购合同",
                "description": "...",
                "status": "progress",
                ...
            },
            "attachments": [
                {
                    "file_name": "采购清单.pdf",
                    "version_count": 3,
                    "versions": [
                        {
                            "id": "uuid",
                            "version": "v3.0",
                            "file_size": 1048576,
                            "uploader_name": "张三",
                            "created_at": "2025-05-20T10:00:00",
                            "is_latest": true
                        },
                        ...
                    ]
                },
                ...
            ],
            "reviewers": [...]
        }
    }
    """
    # 1. 获取合同信息
    contract_service = ContractService()
    contract = await contract_service.get_contract_by_id(contract_id, db)
    
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    
    # 2. 获取分组的附件信息
    file_service = FileService()
    grouped_attachments = await file_service.get_grouped_attachments(
        contract_id=contract_id,
        db=db
    )
    
    # 3. 获取评审人状态
    reviewers = await contract_service.get_reviewer_status(contract_id, db)
    
    return {
        "success": True,
        "data": {
            "contract": {
                "id": str(contract.id),
                "name": contract.name,
                "description": contract.description,
                "status": contract.status,
                "initiator_id": str(contract.initiator_id),
                "cc_users": [str(uid) for uid in (contract.cc_users or [])],
                "created_at": contract.created_at.isoformat(),
                "updated_at": contract.updated_at.isoformat()
            },
            "attachments": grouped_attachments,
            "reviewers": reviewers
        }
    }
```

### 2. 单独的附件列表API

```python
# app/routes/files.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.services.file_service import FileService

router = APIRouter()

@router.get("/contracts/{contract_id}/attachments")
async def get_contract_attachments(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取合同的分组附件列表
    
    响应格式:
    {
        "success": true,
        "data": {
            "attachments": [
                {
                    "file_name": "采购清单.pdf",
                    "version_count": 3,
                    "versions": [...]
                },
                ...
            ]
        }
    }
    """
    file_service = FileService()
    
    # 获取分组附件
    grouped_attachments = await file_service.get_grouped_attachments(
        contract_id=contract_id,
        db=db
    )
    
    return {
        "success": True,
        "data": {
            "attachments": grouped_attachments
        }
    }
```

## 前端使用示例

### React组件示例

```typescript
// AttachmentList.tsx

interface Version {
  id: string;
  version: string;
  file_size: number;
  uploader_name: string;
  created_at: string;
  is_latest: boolean;
}

interface AttachmentGroup {
  file_name: string;
  version_count: number;
  versions: Version[];
}

interface AttachmentListProps {
  contractId: string;
}

export const AttachmentList: React.FC<AttachmentListProps> = ({ contractId }) => {
  const [attachments, setAttachments] = useState<AttachmentGroup[]>([]);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchAttachments();
  }, [contractId]);

  const fetchAttachments = async () => {
    const response = await fetch(`/api/contracts/${contractId}/attachments`);
    const data = await response.json();
    if (data.success) {
      setAttachments(data.data.attachments);
    }
  };

  const toggleGroup = (fileName: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(fileName)) {
      newExpanded.delete(fileName);
    } else {
      newExpanded.add(fileName);
    }
    setExpandedGroups(newExpanded);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
  };

  if (attachments.length === 0) {
    return <div className="empty-state">暂无附件</div>;
  }

  return (
    <div className="attachment-list">
      {attachments.map((group) => (
        <div key={group.file_name} className="attachment-group">
          <div 
            className="group-header"
            onClick={() => toggleGroup(group.file_name)}
          >
            <span className="file-name">{group.file_name}</span>
            <span className="version-count">
              {group.version_count} 个版本
            </span>
            <span className="expand-icon">
              {expandedGroups.has(group.file_name) ? '▼' : '▶'}
            </span>
          </div>

          {expandedGroups.has(group.file_name) && (
            <div className="versions-list">
              {group.versions.map((version) => (
                <div key={version.id} className="version-item">
                  <div className="version-info">
                    <span className="version-number">{version.version}</span>
                    {version.is_latest && (
                      <span className="latest-badge">最新</span>
                    )}
                  </div>
                  <div className="version-meta">
                    <span>{version.uploader_name}</span>
                    <span>{formatDate(version.created_at)}</span>
                    <span>{formatFileSize(version.file_size)}</span>
                  </div>
                  <button 
                    className="download-btn"
                    onClick={() => downloadFile(version.id)}
                  >
                    下载
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
```

### CSS样式示例

```css
/* AttachmentList.css */

.attachment-list {
  padding: 16px;
}

.attachment-group {
  margin-bottom: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f5f5;
  cursor: pointer;
  transition: background-color 0.2s;
}

.group-header:hover {
  background-color: #eeeeee;
}

.file-name {
  flex: 1;
  font-weight: 500;
  font-size: 14px;
}

.version-count {
  margin-right: 12px;
  color: #666;
  font-size: 12px;
}

.expand-icon {
  color: #999;
  font-size: 12px;
}

.versions-list {
  padding: 8px;
}

.version-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.version-item:hover {
  background-color: #fafafa;
}

.version-item:last-child {
  border-bottom: none;
}

.version-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 100px;
}

.version-number {
  font-weight: 500;
  color: #333;
}

.latest-badge {
  padding: 2px 8px;
  background-color: #1890ff;
  color: white;
  font-size: 12px;
  border-radius: 4px;
}

.version-meta {
  flex: 1;
  display: flex;
  gap: 16px;
  color: #666;
  font-size: 12px;
}

.download-btn {
  padding: 6px 16px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.2s;
}

.download-btn:hover {
  background-color: #40a9ff;
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #999;
}
```

## 数据流程图

```
┌─────────────────┐
│  前端请求       │
│  GET /contracts │
│  /{id}          │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  API端点                             │
│  get_contract_detail()              │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  FileService                         │
│  get_grouped_attachments()          │
└────────┬────────────────────────────┘
         │
         ├──► 1. get_attachments_by_contract()
         │         └─► 从数据库获取所有附件
         │
         ├──► 2. group_attachments_by_filename()
         │         └─► 按文件名分组
         │
         ├──► 3. sort_versions_by_time_desc()
         │         └─► 每组按时间倒序排列
         │
         ├──► 4. mark_latest_version()
         │         └─► 标记最新版本
         │
         └──► 5. 按最新上传时间排序文件组
                   └─► 返回最终结果
```

## 性能优化建议

### 1. 数据库查询优化

```python
# 使用 joinedload 预加载上传人信息,避免 N+1 查询
from sqlalchemy.orm import joinedload

query = select(Attachment).where(
    Attachment.contract_id == contract_id
).options(
    joinedload(Attachment.uploader)
).order_by(Attachment.created_at.desc())
```

### 2. 缓存优化

```python
# 使用 Redis 缓存分组结果
import json
from app.core.redis_client import redis_client

async def get_grouped_attachments_cached(
    self,
    contract_id: str,
    db: AsyncSession
) -> List[Dict[str, Any]]:
    # 尝试从缓存获取
    cache_key = f"attachments:grouped:{contract_id}"
    cached = await redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # 缓存未命中,从数据库获取
    result = await self.get_grouped_attachments(contract_id, db)
    
    # 存入缓存,过期时间 10 分钟
    await redis_client.setex(
        cache_key,
        600,
        json.dumps(result, default=str)
    )
    
    return result
```

### 3. 分页支持

```python
async def get_grouped_attachments_paginated(
    self,
    contract_id: str,
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    分页获取分组附件
    """
    # 获取所有分组
    all_groups = await self.get_grouped_attachments(contract_id, db)
    
    # 计算分页
    total = len(all_groups)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "groups": all_groups[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
```

## 测试建议

### 1. 单元测试

已实现完整的单元测试,参见 `tests/services/test_file_service_grouping.py`

### 2. 集成测试

```python
# tests/routes/test_contracts_integration.py

@pytest.mark.asyncio
async def test_get_contract_with_grouped_attachments(client, test_contract, test_attachments):
    """测试获取合同详情包含分组附件"""
    response = await client.get(f"/api/contracts/{test_contract.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "attachments" in data["data"]
    
    attachments = data["data"]["attachments"]
    assert len(attachments) > 0
    
    # 验证分组结构
    for group in attachments:
        assert "file_name" in group
        assert "version_count" in group
        assert "versions" in group
        assert len(group["versions"]) == group["version_count"]
        
        # 验证最新版本标记
        assert group["versions"][0]["is_latest"] is True
        for version in group["versions"][1:]:
            assert version["is_latest"] is False
```

### 3. 性能测试

```python
import time

@pytest.mark.asyncio
async def test_grouping_performance(db, large_attachment_dataset):
    """测试大数据集的分组性能"""
    file_service = FileService()
    
    start_time = time.time()
    result = await file_service.get_grouped_attachments(
        contract_id="test-contract",
        db=db
    )
    end_time = time.time()
    
    # 验证性能要求(例如: 1000个附件应在1秒内完成)
    assert end_time - start_time < 1.0
    assert len(result) > 0
```

## 总结

本实现提供了完整的附件分组功能,包括:

1. ✅ 按文件名分组
2. ✅ 按时间倒序排列版本
3. ✅ 标记最新版本
4. ✅ 按最新上传时间排序文件组
5. ✅ 完整的API集成示例
6. ✅ 前端组件示例
7. ✅ 性能优化建议
8. ✅ 测试覆盖

该实现满足所有相关需求(3.4-3.8),并提供了良好的扩展性和性能。
