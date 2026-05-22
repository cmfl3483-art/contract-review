# UploadButton Component

## 概述

UploadButton 是一个用于上传合同附件的组件。它提供文件选择、类型验证、大小验证、上传进度显示和成功/失败提示等功能。

## 功能特性

- ✅ 支持的文件格式: PDF, DOC, DOCX, PPTX, XLSX
- ✅ 文件大小限制: 最大 20MB
- ✅ 文件类型验证 (MIME 类型和文件扩展名)
- ✅ 文件大小验证
- ✅ 上传进度显示
- ✅ 上传成功/失败提示
- ✅ 自动刷新合同详情缓存

## Props

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| contractId | string | 是 | - | 合同ID |
| disabled | boolean | 否 | false | 是否禁用按钮 |

## 使用示例

### 基本用法

```tsx
import { UploadButton } from '@/components/ContractDetail';

function ContractDetailPage() {
  const contractId = 'contract-123';
  
  return (
    <div>
      <h2>合同附件</h2>
      <UploadButton contractId={contractId} />
    </div>
  );
}
```

### 禁用状态

```tsx
import { UploadButton } from '@/components/ContractDetail';

function ContractDetailPage() {
  const contractId = 'contract-123';
  const isReadOnly = true;
  
  return (
    <div>
      <h2>合同附件</h2>
      <UploadButton 
        contractId={contractId} 
        disabled={isReadOnly}
      />
    </div>
  );
}
```

## 文件验证规则

### 支持的文件类型

- PDF: `.pdf` (application/pdf)
- Word: `.doc`, `.docx` (application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document)
- PowerPoint: `.ppt`, `.pptx` (application/vnd.ms-powerpoint, application/vnd.openxmlformats-officedocument.presentationml.presentation)
- Excel: `.xls`, `.xlsx` (application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

### 文件大小限制

- 最大文件大小: 20MB (20 * 1024 * 1024 bytes)
- 超过限制时会显示错误提示,包含当前文件大小

## 上传流程

1. 用户点击"上传附件"按钮
2. 打开文件选择对话框
3. 用户选择文件
4. 验证文件类型和大小
5. 如果验证失败,显示错误提示并停止
6. 如果验证通过,开始上传
7. 显示上传进度条
8. 上传完成后显示成功提示
9. 自动刷新合同详情缓存

## 错误处理

### 文件类型错误

```
不支持的文件类型,仅支持 PDF、DOC、DOCX、PPTX、XLSX 格式
```

### 文件大小错误

```
文件大小不能超过 20MB,当前文件大小: 25.5 MB
```

### 上传失败

```
上传失败: [错误信息]
```

## 样式定制

组件使用 `UploadButton.css` 文件定义样式,可以通过覆盖以下 CSS 类来定制样式:

- `.upload-button-container`: 容器样式
- `.upload-progress`: 进度条容器样式
- `.ant-btn`: 按钮样式 (Ant Design Button)

## 依赖

- `antd`: Button, Progress, message 组件
- `@ant-design/icons`: UploadOutlined 图标
- `@tanstack/react-query`: 用于缓存管理
- `../../hooks/useAttachments`: 上传附件的 hook

## 注意事项

1. 组件需要在 `QueryClientProvider` 内使用
2. 上传成功后会自动刷新合同详情缓存
3. 文件选择后会立即开始上传,无需额外确认
4. 上传进度是模拟的,实际进度需要后端支持
5. 同一文件可以重复上传 (input value 会在上传后清空)

## 相关组件

- `AttachmentList`: 附件列表组件
- `AttachmentVersion`: 附件版本组件
- `ContractDetail`: 合同详情组件

## API 接口

上传附件 API:

```
POST /api/contracts/:contractId/attachments
Content-Type: multipart/form-data

Body:
- file: File (必填)
- version: string (可选)

Response:
{
  success: true,
  data: {
    attachment: {
      id: string,
      contractId: string,
      fileName: string,
      version: string,
      fileSize: number,
      mimeType: string,
      storageKey: string,
      uploaderId: string,
      createdAt: string
    }
  }
}
```
