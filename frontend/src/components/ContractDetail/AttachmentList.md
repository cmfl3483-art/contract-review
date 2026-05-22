# AttachmentList Component

## Overview

The `AttachmentList` component displays contract attachments grouped by filename with version management capabilities. It provides an intuitive interface for viewing and downloading different versions of contract files.

## Features

- **File Grouping**: Attachments are grouped by filename
- **Version Count**: Shows the number of versions for each file
- **Expand/Collapse**: Click to expand and view all versions of a file
- **Version Details**: Displays version number, file size, uploader, and upload time
- **Latest Badge**: Marks the most recent version with a "最新" badge
- **Download**: Provides download functionality for each version
- **Empty State**: Shows a friendly message when no attachments exist

## Props

```typescript
interface AttachmentListProps {
  attachments: AttachmentGroup[];
  onDownload?: (attachmentId: string) => void;
}
```

### `attachments`
- **Type**: `AttachmentGroup[]`
- **Required**: Yes
- **Description**: Array of attachment groups, where each group contains versions of the same file

### `onDownload`
- **Type**: `(attachmentId: string) => void`
- **Required**: No
- **Description**: Callback function triggered when user clicks download button

## AttachmentGroup Structure

```typescript
interface AttachmentGroup {
  fileName: string;
  versionCount: number;
  versions: Attachment[];
}

interface Attachment {
  id: string;
  contractId: string;
  fileName: string;
  version: string;
  fileSize: number;
  mimeType: string;
  storageKey: string;
  uploaderId: string;
  uploader?: User;
  createdAt: string;
}
```

## Usage Example

```tsx
import { AttachmentList } from '@/components/ContractDetail';

function ContractDetailPage() {
  const attachments = [
    {
      fileName: '采购合同.pdf',
      versionCount: 2,
      versions: [
        {
          id: 'att-1',
          contractId: 'contract-1',
          fileName: '采购合同.pdf',
          version: 'v2.0',
          fileSize: 2048576,
          mimeType: 'application/pdf',
          storageKey: 'key-1',
          uploaderId: 'user-1',
          uploader: {
            id: 'user-1',
            name: '张三',
            // ... other user fields
          },
          createdAt: '2025-03-01T10:00:00Z',
        },
        // ... more versions
      ],
    },
  ];

  const handleDownload = (attachmentId: string) => {
    // Download logic
    console.log('Downloading attachment:', attachmentId);
  };

  return (
    <AttachmentList 
      attachments={attachments} 
      onDownload={handleDownload} 
    />
  );
}
```

## Behavior

### Default State
- All file groups are collapsed by default
- Only the filename and version count are visible

### Expanded State
- Click on a file group header to expand it
- Shows all versions sorted by upload time (newest first)
- Each version displays:
  - Version number (e.g., "v2.0")
  - "最新" badge for the latest version
  - File size (formatted, e.g., "2.00 MB")
  - Uploader name (with tooltip)
  - Upload time (relative format, e.g., "5分钟前")
  - Download button

### Empty State
- When `attachments` array is empty, displays an empty state with message "暂无附件"

## Styling

The component uses custom CSS classes defined in `AttachmentList.css`:

- `.attachment-list`: Main container
- `.attachment-group`: Individual file group container
- `.attachment-group-header`: Clickable header for each file group
- `.attachment-versions`: Container for version list
- `.attachment-version`: Individual version item
- `.attachment-version-badge`: "最新" badge for latest version

## Accessibility

- Clickable headers have hover effects for better UX
- Tooltips show full uploader names on hover
- Download buttons are clearly labeled
- Empty state provides clear feedback

## Requirements Coverage

This component implements the following requirements from the design document:

- **Requirement 2.5**: Display attachments when contract has them
- **Requirement 2.6**: Show "暂无附件" when no attachments
- **Requirement 3.4**: Group attachments by filename
- **Requirement 3.5**: Show version count for each file group
- **Requirement 3.6**: Display version details (version number, upload time, uploader)
- **Requirement 3.7**: Mark latest version with badge

## Related Components

- `ContractDetail`: Parent component that uses AttachmentList
- `UploadButton`: Component for uploading new attachments
- `AttachmentVersion`: Could be extracted as a separate component if needed

## Testing

Unit tests are available in `AttachmentList.test.tsx` covering:
- Empty state rendering
- File group display
- Expand/collapse functionality
- Latest version badge
- Version details display
- Download callback
- Multiple file groups

## Future Enhancements

Potential improvements for future iterations:
- Preview functionality for PDF/image files
- Drag-and-drop file upload
- Bulk download of all versions
- Version comparison feature
- File type icons based on MIME type
