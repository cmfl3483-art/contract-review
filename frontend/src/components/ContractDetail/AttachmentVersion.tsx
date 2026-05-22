import React from 'react';
import { Tooltip, Avatar } from 'antd';
import { DownloadOutlined, UserOutlined } from '@ant-design/icons';
import type { Attachment } from '../../types';
import { formatRelativeTime } from '../../utils/time';
import { formatFileSize } from '../../utils/format';
import './AttachmentVersion.css';

interface AttachmentVersionProps {
  attachment: Attachment;
  isLatest?: boolean;
  onDownload?: (attachmentId: string) => void;
}

const AttachmentVersion: React.FC<AttachmentVersionProps> = ({
  attachment,
  isLatest = false,
  onDownload,
}) => {
  const handleDownload = () => {
    if (onDownload) {
      onDownload(attachment.id);
    }
  };

  // Generate avatar color based on uploader name
  const getAvatarColor = (name: string) => {
    const colors = ['#f56a00', '#7265e6', '#ffbf00', '#00a2ae', '#87d068'];
    const charCode = name.charCodeAt(0);
    return colors[charCode % colors.length];
  };

  const uploaderName = attachment.uploader?.name || '未知用户';
  const avatarColor = getAvatarColor(uploaderName);

  return (
    <div className="attachment-version" data-testid="attachment-version">
      <div className="attachment-version-info">
        <div className="attachment-version-header">
          <span className="attachment-version-number">{attachment.version}</span>
          {isLatest && <span className="attachment-version-latest-badge">最新</span>}
        </div>

        <div className="attachment-version-meta">
          <div className="attachment-version-uploader">
            <Tooltip title={uploaderName}>
              <Avatar
                size="small"
                style={{ backgroundColor: avatarColor }}
                src={attachment.uploader?.avatar}
                icon={!attachment.uploader?.avatar && <UserOutlined />}
              >
                {!attachment.uploader?.avatar && uploaderName.charAt(0)}
              </Avatar>
            </Tooltip>
            <span className="attachment-version-uploader-name">{uploaderName}</span>
          </div>

          <div className="attachment-version-details">
            <span className="attachment-version-time">
              {formatRelativeTime(new Date(attachment.createdAt))}
            </span>
            <span className="attachment-version-separator">·</span>
            <span className="attachment-version-size">{formatFileSize(attachment.fileSize)}</span>
          </div>
        </div>
      </div>

      <Tooltip title="下载">
        <button
          className="attachment-version-download-btn"
          onClick={handleDownload}
          aria-label="下载附件"
        >
          <DownloadOutlined />
        </button>
      </Tooltip>
    </div>
  );
};

export default AttachmentVersion;
