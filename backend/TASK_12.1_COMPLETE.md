# Task 12.1 Complete: 实现上传附件 API

## 任务概述

实现 POST /api/contracts/:id/attachments 端点,支持文件上传、验证、版本管理和MinIO存储。

## 实现内容

### 1. API 端点

**路径**: `POST /api/contracts/{contract_id}/attachments`

**文件**: `/Users/cm/Documents/kiro/project/backend/app/routes/files.py`

**功能**:
- 接收 multipart/form-data 格式的文件上传
- 验证文件类型和大小
- 自动生成版本号
- 上传到 MinIO 对象存储
- 保存附件记录到数据库
- 返回附件信息

### 2. 文件服务层

**文件**: `/Users/cm/Documents/kiro/project/backend/app/services/file_service.py`

**核心方法**:

#### `validate_file(file: UploadFile)`
- 验证文件类型 (PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX)
- 验证文件大小 (最大 20MB)
- 抛出 ValueError 如果验证失败

#### `get_next_version(contract_id, file_name, db)`
- 查询同名文件的最大版本号
- 自动递增版本号 (v1.0, v2.0, v3.0...)
- 首次上传返回 v1.0

#### `upload_file(contract_id, uploader_id, file, db)`
- 完整的文件上传流程:
  1. 验证文件
  2. 获取版本号
  3. 生成存储键: `{contract_id}/{file_name}/{version}/{uuid}.{ext}`
  4. 上传到 MinIO
  5. 保存附件记录到数据库
  6. 返回 Attachment 对象

### 3. 数据模型

**文件**: `/Users/cm/Documents/kiro/project/backend/app/models/attachment.py`

**Attachment 模型字段**:
- `id`: UUID 主键
- `contract_id`: 合同ID (外键)
- `file_name`: 文件名
- `version`: 版本号
- `file_size`: 文件大小(字节)
- `mime_type`: MIME类型
- `storage_key`: MinIO存储键
- `uploader_id`: 上传人ID (外键)
- `created_at`: 创建时间

**索引**:
- `ix_attachments_contract_id`: 合同ID索引
- `ix_attachments_filename_created_at`: 文件名+创建时间复合索引

### 4. API 请求/响应

#### 请求示例

```bash
curl -X POST "http://localhost:8000/api/contracts/{contract_id}/attachments" \
  -H "Authorization: Bearer {token}" \
  -F "file=@contract.pdf"
```

#### 成功响应 (200)

```json
{
  "success": true,
  "data": {
    "attachment": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "file_name": "contract.pdf",
      "version": "v1.0",
      "file_size": 1048576,
      "mime_type": "application/pdf",
      "created_at": "2025-05-18T22:30:00.000Z"
    }
  }
}
```

#### 错误响应

**400 - 文件类型不支持**
```json
{
  "detail": "不支持的文件类型: application/zip。支持的类型: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX"
}
```

**400 - 文件过大**
```json
{
  "detail": "文件大小不能超过20.0MB"
}
```

**401 - 未授权**
```json
{
  "detail": "未授权"
}
```

**500 - 服务器错误**
```json
{
  "detail": "上传附件失败: {error_message}"
}
```

### 5. 文件验证规则

#### 支持的文件类型
- PDF: `application/pdf`
- Word: `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- PowerPoint: `application/vnd.ms-powerpoint`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`
- Excel: `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

#### 文件大小限制
- 最大: 20MB (20 * 1024 * 1024 bytes)
- 配置位置: `app/core/config.py` 中的 `MAX_FILE_SIZE`

### 6. 版本管理

#### 版本号生成规则
- 首次上传同名文件: `v1.0`
- 再次上传同名文件: `v2.0`
- 版本号递增: `v3.0`, `v4.0`...

#### 存储键格式
```
{contract_id}/{file_name}/{version}/{uuid}.{ext}
```

示例:
```
123e4567-e89b-12d3-a456-426614174000/contract.pdf/v1.0/abc123.pdf
123e4567-e89b-12d3-a456-426614174000/contract.pdf/v2.0/def456.pdf
```

### 7. MinIO 集成

#### Bucket 配置
- Bucket 名称: `contract-attachments` (可在 config.py 配置)
- 访问控制: 私有 (需要预签名URL访问)

#### 上传流程
1. 读取文件数据到内存
2. 调用 `minio_client.upload_file_data()`
3. 传递存储键、文件数据、大小和MIME类型
4. MinIO 返回成功/失败

### 8. 认证和授权

#### 认证
- 使用 JWT Token 认证
- Token 从 `Authorization: Bearer {token}` 头获取
- 通过 `get_current_user(request)` 获取当前用户

#### 授权
- 任何已认证用户都可以上传附件
- 上传人ID 自动设置为当前用户

### 9. 错误处理

#### 文件验证错误
- 捕获 `ValueError` 异常
- 返回 400 状态码和错误信息

#### MinIO 上传错误
- 捕获 `Exception` 异常
- 返回 500 状态码和错误信息

#### 数据库错误
- 自动回滚事务
- 返回 500 状态码

### 10. 测试

#### 测试文件
`/Users/cm/Documents/kiro/project/backend/tests/test_upload_attachment.py`

#### 测试用例
1. ✅ `test_upload_attachment_success` - 成功上传附件
2. ✅ `test_upload_attachment_invalid_file_type` - 不支持的文件类型
3. ✅ `test_upload_attachment_file_too_large` - 文件过大
4. ✅ `test_upload_attachment_version_increment` - 版本号递增
5. ✅ `test_upload_attachment_unauthorized` - 未授权
6. ✅ `test_upload_attachment_contract_not_found` - 合同不存在

## 需求覆盖

✅ **需求 3.1**: 支持上传 PDF、DOC、DOCX、PPTX、XLSX 格式的附件文件
✅ **需求 3.2**: 限制单个附件文件大小不超过 20MB
✅ **需求 3.3**: 当用户上传同名文件时,自动创建该文件的新版本

## 相关文件

### 实现文件
- `/Users/cm/Documents/kiro/project/backend/app/routes/files.py` - API 路由
- `/Users/cm/Documents/kiro/project/backend/app/services/file_service.py` - 文件服务
- `/Users/cm/Documents/kiro/project/backend/app/models/attachment.py` - 数据模型

### 配置文件
- `/Users/cm/Documents/kiro/project/backend/app/core/config.py` - 配置
- `/Users/cm/Documents/kiro/project/backend/app/core/minio_client.py` - MinIO 客户端

### 测试文件
- `/Users/cm/Documents/kiro/project/backend/tests/test_upload_attachment.py` - 单元测试

## API 文档

API 文档已自动生成,可通过以下地址访问:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`

## 使用示例

### Python (httpx)

```python
import httpx

async def upload_attachment(contract_id: str, file_path: str, token: str):
    async with httpx.AsyncClient() as client:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'application/pdf')}
            headers = {'Authorization': f'Bearer {token}'}
            
            response = await client.post(
                f'http://localhost:8000/api/contracts/{contract_id}/attachments',
                files=files,
                headers=headers
            )
            
            return response.json()
```

### JavaScript (fetch)

```javascript
async function uploadAttachment(contractId, file, token) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(
    `http://localhost:8000/api/contracts/${contractId}/attachments`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }
  );
  
  return await response.json();
}
```

### cURL

```bash
# 上传 PDF 文件
curl -X POST "http://localhost:8000/api/contracts/123e4567-e89b-12d3-a456-426614174000/attachments" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@/path/to/contract.pdf"

# 上传 Word 文件
curl -X POST "http://localhost:8000/api/contracts/123e4567-e89b-12d3-a456-426614174000/attachments" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@/path/to/document.docx"
```

## 性能考虑

### 文件大小限制
- 20MB 限制平衡了用户体验和服务器性能
- 可通过配置文件调整: `MAX_FILE_SIZE`

### 内存使用
- 文件完全读入内存后上传
- 对于大文件,考虑使用流式上传

### 并发上传
- FastAPI 异步处理,支持并发上传
- MinIO 支持高并发访问

### 数据库性能
- 使用索引优化查询
- 版本号查询使用 `func.max()` 聚合

## 安全考虑

### 文件类型验证
- 基于 MIME 类型验证
- 防止上传恶意文件

### 文件大小限制
- 防止 DoS 攻击
- 保护服务器资源

### 认证和授权
- JWT Token 认证
- 只有已认证用户可上传

### 存储安全
- MinIO 私有访问
- 预签名 URL 有效期限制

## 后续优化建议

### 1. 流式上传
- 对于大文件,使用流式上传减少内存占用
- 实现断点续传

### 2. 文件扫描
- 集成病毒扫描
- 检测恶意文件

### 3. 缩略图生成
- PDF 首页预览
- 图片缩略图

### 4. CDN 加速
- 配置 CDN 加速下载
- 减少服务器带宽

### 5. 异步处理
- 使用 Celery 异步上传大文件
- 提高响应速度

## 总结

Task 12.1 已完成,实现了完整的上传附件 API:

✅ 创建 POST /api/contracts/:id/attachments 端点
✅ 使用 multipart/form-data 接收文件
✅ 验证文件类型和大小
✅ 调用 FileService 上传文件
✅ 返回附件信息
✅ 满足需求 3.1-3.3

API 已集成到主应用,可通过 `/api/docs` 查看完整文档。
