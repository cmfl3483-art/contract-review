import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AttachmentVersion from './AttachmentVersion';
import type { Attachment } from '../../types';

describe('AttachmentVersion', () => {
  const mockAttachment: Attachment = {
    id: 'attachment-1',
    contractId: 'contract-1',
    fileName: 'test.pdf',
    version: 'v1.0',
    fileSize: 1048576, // 1MB
    mimeType: 'application/pdf',
    storageKey: 'storage-key-1',
    uploaderId: 'user-1',
    uploader: {
      id: 'user-1',
      dingtalkUserId: 'dingtalk-1',
      name: '张三',
      role: '法务',
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
  };

  it('应该渲染附件版本信息', () => {
    render(<AttachmentVersion attachment={mockAttachment} />);

    expect(screen.getByText('v1.0')).toBeInTheDocument();
    expect(screen.getByText('张三')).toBeInTheDocument();
    expect(screen.getByText('1.00 MB')).toBeInTheDocument();
  });

  it('当 isLatest 为 true 时应该显示最新标签', () => {
    render(<AttachmentVersion attachment={mockAttachment} isLatest={true} />);

    expect(screen.getByText('最新')).toBeInTheDocument();
  });

  it('当 isLatest 为 false 时不应该显示最新标签', () => {
    render(<AttachmentVersion attachment={mockAttachment} isLatest={false} />);

    expect(screen.queryByText('最新')).not.toBeInTheDocument();
  });

  it('应该显示上传者头像', () => {
    render(<AttachmentVersion attachment={mockAttachment} />);

    const avatar = screen.getByText('张').closest('.ant-avatar');
    expect(avatar).toBeInTheDocument();
  });

  it('当上传者有头像时应该显示头像图片', () => {
    const attachmentWithAvatar = {
      ...mockAttachment,
      uploader: {
        ...mockAttachment.uploader!,
        avatar: 'https://example.com/avatar.jpg',
      },
    };

    render(<AttachmentVersion attachment={attachmentWithAvatar} />);

    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://example.com/avatar.jpg');
  });

  it('当上传者信息缺失时应该显示默认文本', () => {
    const attachmentWithoutUploader = {
      ...mockAttachment,
      uploader: undefined,
    };

    render(<AttachmentVersion attachment={attachmentWithoutUploader} />);

    expect(screen.getByText('未知用户')).toBeInTheDocument();
  });

  it('应该显示相对时间', () => {
    render(<AttachmentVersion attachment={mockAttachment} />);

    // The formatRelativeTime function should format 2 hours ago
    expect(screen.getByText('2小时前')).toBeInTheDocument();
  });

  it('点击下载按钮应该调用 onDownload 回调', () => {
    const onDownload = vi.fn();
    render(<AttachmentVersion attachment={mockAttachment} onDownload={onDownload} />);

    const downloadButton = screen.getByLabelText('下载附件');
    fireEvent.click(downloadButton);

    expect(onDownload).toHaveBeenCalledWith('attachment-1');
    expect(onDownload).toHaveBeenCalledTimes(1);
  });

  it('当没有提供 onDownload 回调时点击下载按钮不应该报错', () => {
    render(<AttachmentVersion attachment={mockAttachment} />);

    const downloadButton = screen.getByLabelText('下载附件');
    expect(() => fireEvent.click(downloadButton)).not.toThrow();
  });

  it('应该显示文件大小格式化后的文本', () => {
    const attachmentWithLargeFile = {
      ...mockAttachment,
      fileSize: 5242880, // 5MB
    };

    render(<AttachmentVersion attachment={attachmentWithLargeFile} />);

    expect(screen.getByText('5.00 MB')).toBeInTheDocument();
  });

  it('应该有正确的测试 ID', () => {
    const { container } = render(<AttachmentVersion attachment={mockAttachment} />);

    const versionElement = container.querySelector('[data-testid="attachment-version"]');
    expect(versionElement).toBeInTheDocument();
  });

  it('应该显示分隔符', () => {
    render(<AttachmentVersion attachment={mockAttachment} />);

    expect(screen.getByText('·')).toBeInTheDocument();
  });
});
