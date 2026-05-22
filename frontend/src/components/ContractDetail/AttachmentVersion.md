# AttachmentVersion Component

## Overview

The `AttachmentVersion` component displays a single version of an attachment file with detailed information including version number, uploader, upload time, file size, and a download button.

## Features

- **Version Display**: Shows the version number prominently
- **Latest Badge**: Displays a "最新" (Latest) badge for the most recent version
- **Uploader Information**: Shows uploader avatar and name with tooltip
- **Metadata**: Displays upload time (relative format) and file size
- **Download Action**: Provides a download button with hover effects
- **Responsive Design**: Adapts to different screen sizes
- **Accessibility**: Includes proper ARIA labels and keyboard navigation

## Props

```typescript
interface AttachmentVersionProps {
  attachment: Attachment;      // The attachment data
  isLatest?: boolean;          // Whether this is the latest version (default: false)
  onDownload?: (attachmentId: string) => void;  // Download callback
}
```

## Usage

```tsx
import AttachmentVersion from './AttachmentVersion';

// Basic usage
<AttachmentVersion
  attachment={attachmentData}
  isLatest={true}
  onDownload={(id) => handleDownload(id)}
/>
```

## Styling

The component uses the following CSS classes:
- `.attachment-version` - Main container
- `.attachment-version-info` - Information section
- `.attachment-version-header` - Version number and badge
- `.attachment-version-latest-badge` - Latest version badge
- `.attachment-version-meta` - Metadata section
- `.attachment-version-uploader` - Uploader information
- `.attachment-version-details` - Time and size details
- `.attachment-version-download-btn` - Download button

## Requirements

Implements the following requirements from the design document:
- **3.6**: Display version number, upload time, and uploader
- **3.7**: Mark the latest version with a label
- **2.6**: Provide download functionality
- **10.3**: Implement hover effects for interactive elements

## Dependencies

- `antd`: Tooltip, Avatar components
- `@ant-design/icons`: DownloadOutlined, UserOutlined icons
- `../../utils/time`: formatRelativeTime function
- `../../utils/format`: formatFileSize function
- `../../types`: Attachment type definition

## Testing

Unit tests are available in `AttachmentVersion.test.tsx` covering:
- Rendering of version information
- Latest badge display logic
- Uploader avatar and name display
- Download button functionality
- Edge cases (missing uploader, no callback)

## Accessibility

- Download button has `aria-label="下载附件"`
- Uploader name is shown in a tooltip for better UX
- Keyboard navigation is supported for the download button
- Focus states are clearly visible

## Browser Support

Compatible with all modern browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
