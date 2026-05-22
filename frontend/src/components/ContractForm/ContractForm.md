# ContractForm Component

## Overview

The `ContractForm` component is a modal dialog form for creating new contract pre-review requests. It provides a user-friendly interface for entering contract details, selecting reviewers and CC users, and uploading attachments.

## Features

- **Contract Name Input** (Required): Text input for the contract name with validation
- **Contract Description** (Optional): Textarea for detailed contract description with character count
- **Reviewers Selection** (Required): Multi-select dropdown for choosing reviewers from available users
- **CC Users Selection** (Optional): Multi-select dropdown for choosing users to be CC'd
- **File Upload**: Drag-and-drop file upload with support for PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX formats
- **File Validation**: Automatic validation of file types and size (max 20MB per file)
- **Form Validation**: Client-side validation with error messages
- **Loading State**: Shows loading indicator during form submission

## Props

```typescript
interface ContractFormProps {
  visible: boolean;  // Controls modal visibility
  onClose: () => void;  // Callback when modal is closed
}
```

## Usage

```tsx
import { useState } from 'react';
import ContractForm from './components/ContractForm';

function MyComponent() {
  const [isFormVisible, setIsFormVisible] = useState(false);

  const handleOpenForm = () => {
    setIsFormVisible(true);
  };

  const handleCloseForm = () => {
    setIsFormVisible(false);
  };

  return (
    <>
      <Button onClick={handleOpenForm}>发起合同预审</Button>
      <ContractForm visible={isFormVisible} onClose={handleCloseForm} />
    </>
  );
}
```

## Form Fields

### Contract Name (name)
- **Type**: Text input
- **Required**: Yes
- **Validation**: 
  - Cannot be empty
  - Maximum 200 characters
- **Placeholder**: "请输入合同名称"

### Contract Description (description)
- **Type**: Textarea
- **Required**: No
- **Validation**: Maximum 1000 characters
- **Features**: Character counter
- **Placeholder**: "请输入合同描述(可选)"

### Reviewers (reviewers)
- **Type**: Multi-select dropdown
- **Required**: Yes
- **Validation**: At least one reviewer must be selected
- **Features**: 
  - Search/filter functionality
  - Shows user name and role
- **Placeholder**: "请选择评审人"

### CC Users (ccUsers)
- **Type**: Multi-select dropdown
- **Required**: No
- **Features**: 
  - Search/filter functionality
  - Shows user name and role
- **Placeholder**: "请选择抄送人(可选)"

### Files (files)
- **Type**: File upload (drag-and-drop)
- **Required**: No
- **Supported Formats**: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX
- **Size Limit**: 20MB per file
- **Features**:
  - Multiple file upload
  - Drag-and-drop support
  - File list with remove option
  - Automatic validation

## Validation Rules

1. **Contract Name**: Required, max 200 characters
2. **Description**: Optional, max 1000 characters
3. **Reviewers**: Required, at least one reviewer
4. **CC Users**: Optional
5. **Files**: Optional, but must meet format and size requirements

## File Upload Validation

- **Supported MIME Types**:
  - `application/pdf` (PDF)
  - `application/msword` (DOC)
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX)
  - `application/vnd.ms-powerpoint` (PPT)
  - `application/vnd.openxmlformats-officedocument.presentationml.presentation` (PPTX)
  - `application/vnd.ms-excel` (XLS)
  - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (XLSX)

- **Size Limit**: 20MB per file
- **Validation Messages**:
  - Unsupported file type: "{filename} 不是支持的文件类型"
  - File too large: "{filename} 文件大小超过 20MB 限制"

## Form Submission

When the form is submitted:

1. Form fields are validated
2. If validation passes, data is sent to the API via `useCreateContract` hook
3. On success:
   - Success message is displayed
   - Form is reset
   - Modal is closed
   - Contract list is automatically refreshed
   - Pending count badge is updated
4. On error:
   - Error message is displayed
   - Form remains open for correction

## API Integration

The component uses the `useCreateContract` hook from `../../hooks/useContracts` which:
- Sends a POST request to `/api/contracts`
- Automatically invalidates contract list cache on success
- Automatically invalidates pending count cache on success

## Mock Data

Currently, the component uses mock user data for the reviewers and CC users dropdowns:

```typescript
const MOCK_USERS = [
  { id: 'user-1', name: '张三', role: '法务' },
  { id: 'user-2', name: '李四', role: '财务' },
  { id: 'user-3', name: '王五', role: '业务' },
  { id: 'user-4', name: '赵六', role: '销售' },
  { id: 'user-5', name: '钱七', role: '运营' },
  { id: 'user-6', name: '孙八', role: '人事' },
  { id: 'user-7', name: '周九', role: '法务' },
  { id: 'user-8', name: '吴十', role: '财务' },
];
```

**TODO**: Replace with real user data from API when the users endpoint is implemented.

## Styling

The component uses custom CSS defined in `ContractForm.css` with the following features:
- Consistent spacing and layout
- Focus states for inputs
- Hover effects for upload area
- Error state styling
- Responsive design

## Dependencies

- `antd`: UI components (Modal, Form, Input, Select, Upload, Button, message)
- `@ant-design/icons`: Icons (InboxOutlined)
- `react`: Core React library
- `../../hooks/useContracts`: Custom hook for contract creation
- `../../types`: TypeScript type definitions

## Requirements Coverage

This component implements the following requirements from the design document:

- **需求 8.1**: Display contract creation dialog when button is clicked
- **需求 8.2**: Contract name input (required)
- **需求 8.3**: Contract description input (optional)
- **需求 8.4**: Reviewer multi-select from preset list
- **需求 8.5**: CC user multi-select from preset list
- **需求 8.6**: File upload functionality
- **需求 8.7**: Form validation with error messages
- **需求 8.8**: Create contract and set status to "进行中"
- **需求 8.9**: Create review tasks for selected reviewers
- **需求 8.10**: Set current user as contract initiator
- **需求 8.11**: Clear form and close dialog on success
- **需求 8.12**: Refresh contract list and update pending badge

## Future Enhancements

1. **User API Integration**: Replace mock users with real user data from `/api/users` endpoint
2. **File Preview**: Add preview functionality for uploaded files
3. **Draft Saving**: Allow users to save form as draft
4. **Template Support**: Support for contract templates
5. **Batch Upload**: Improve batch file upload experience
6. **Progress Indicator**: Show upload progress for large files
