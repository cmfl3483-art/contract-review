import { useState } from 'react';
import { FileOutlined, UpOutlined, DownOutlined } from '@ant-design/icons';
import { Empty } from 'antd';
import type { AttachmentGroup } from '../../types';
import AttachmentVersion from './AttachmentVersion';
import './AttachmentList.css';

interface AttachmentListProps {
  attachments: AttachmentGroup[];
  onDownload?: (attachmentId: string) => void;
}

/**
 * AttachmentList Component
 *
 * Displays contract attachments grouped by filename with version management.
 *
 * Features:
 * - Groups attachments by filename
 * - Shows version count for each file
 * - Supports expand/collapse for version lists
 * - Displays version details (version number, upload time, uploader)
 * - Marks the latest version
 * - Provides download functionality
 * - Shows empty state when no attachments
 *
 * Requirements: 2.5, 2.6, 3.4, 3.5, 3.6, 3.7
 */
const AttachmentList: React.FC<AttachmentListProps> = ({ attachments, onDownload }) => {
  // Track which file groups are expanded
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());

  // Toggle expand/collapse for a file group
  const toggleExpand = (fileName: string) => {
    setExpandedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(fileName)) {
        next.delete(fileName);
      } else {
        next.add(fileName);
      }
      return next;
    });
  };

  // Handle download click
  const handleDownload = (attachmentId: string) => {
    onDownload?.(attachmentId);
  };

  // Show empty state if no attachments
  if (!attachments || attachments.length === 0) {
    return (
      <div className="attachment-list-empty">
        <Empty description="暂无附件" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </div>
    );
  }

  return (
    <div className="attachment-list">
      {attachments.map((group) => {
        const isExpanded = expandedFiles.has(group.fileName);

        return (
          <div key={group.fileName} className="attachment-group">
            {/* File group header */}
            <div className="attachment-group-header" onClick={() => toggleExpand(group.fileName)}>
              <div className="attachment-group-info">
                <FileOutlined className="attachment-icon" />
                <span className="attachment-filename">{group.fileName}</span>
                <span className="attachment-version-count">{group.versionCount} 个版本</span>
              </div>
              <div className="attachment-group-actions">
                {isExpanded ? <UpOutlined /> : <DownOutlined />}
              </div>
            </div>

            {/* Version list (shown when expanded) */}
            {isExpanded && (
              <div className="attachment-versions">
                {group.versions.map((version, index) => {
                  const isLatest = index === 0;

                  return (
                    <AttachmentVersion
                      key={version.id}
                      attachment={version}
                      isLatest={isLatest}
                      onDownload={handleDownload}
                    />
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default AttachmentList;
