import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import AttachmentList from './AttachmentList';
import type { AttachmentGroup } from '../../types';

describe('AttachmentList', () => {
  const mockAttachments: AttachmentGroup[] = [
    {
      fileName: '采购合同.pdf',
      versionCount: 2,
      versions: [
        {
          id: 'att-1',
          contractId: 'contract-1',
          fileName: '采购合同.pdf',
          version: 'v2.0',
          fileSize: 2048576, // 2MB
          mimeType: 'application/pdf',
          storageKey: 'key-1',
          uploaderId: 'user-1',
          uploader: {
            id: 'user-1',
            name: '张三',
            dingtalkUserId: 'dt-1',
            role: '法务',
            createdAt: '2025-03-01T10:00:00Z',
            updatedAt: '2025-03-01T10:00:00Z',
          },
          createdAt: '2025-03-01T10:00:00Z',
        },
        {
          id: 'att-2',
          contractId: 'contract-1',
          fileName: '采购合同.pdf',
          version: 'v1.0',
          fileSize: 1048576, // 1MB
          mimeType: 'application/pdf',
          storageKey: 'key-2',
          uploaderId: 'user-2',
          uploader: {
            id: 'user-2',
            name: '李四',
            dingtalkUserId: 'dt-2',
            role: '销售',
            createdAt: '2025-02-28T10:00:00Z',
            updatedAt: '2025-02-28T10:00:00Z',
          },
          createdAt: '2025-02-28T10:00:00Z',
        },
      ],
    },
  ];

  it('应该显示"暂无附件"当没有附件时', () => {
    render(<AttachmentList attachments={[]} />);
    expect(screen.getByText('暂无附件')).toBeInTheDocument();
  });

  it('应该显示文件名和版本数量', () => {
    render(<AttachmentList attachments={mockAttachments} />);
    expect(screen.getByText('采购合同.pdf')).toBeInTheDocument();
    expect(screen.getByText('2 个版本')).toBeInTheDocument();
  });

  it('应该默认折叠版本列表', () => {
    render(<AttachmentList attachments={mockAttachments} />);
    // Version details should not be visible initially
    expect(screen.queryByText('v2.0')).not.toBeInTheDocument();
    expect(screen.queryByText('v1.0')).not.toBeInTheDocument();
  });

  it('应该在点击时展开版本列表', () => {
    render(<AttachmentList attachments={mockAttachments} />);

    // Click to expand
    const header = screen.getByText('采购合同.pdf').closest('.attachment-group-header');
    fireEvent.click(header!);

    // Version details should now be visible
    expect(screen.getByText('v2.0')).toBeInTheDocument();
    expect(screen.getByText('v1.0')).toBeInTheDocument();
  });

  it('应该标记最新版本', () => {
    render(<AttachmentList attachments={mockAttachments} />);

    // Expand to see versions
    const header = screen.getByText('采购合同.pdf').closest('.attachment-group-header');
    fireEvent.click(header!);

    // Should show "最新" badge for the first version
    expect(screen.getByText('最新')).toBeInTheDocument();
  });

  it('应该显示版本详细信息', () => {
    render(<AttachmentList attachments={mockAttachments} />);

    // Expand to see versions
    const header = screen.getByText('采购合同.pdf').closest('.attachment-group-header');
    fireEvent.click(header!);

    // Check version details
    expect(screen.getByText('v2.0')).toBeInTheDocument();
    expect(screen.getByText('2.00 MB')).toBeInTheDocument();
    expect(screen.getByText('张三')).toBeInTheDocument();

    expect(screen.getByText('v1.0')).toBeInTheDocument();
    expect(screen.getByText('1.00 MB')).toBeInTheDocument();
    expect(screen.getByText('李四')).toBeInTheDocument();
  });

  it('应该调用下载回调', () => {
    const onDownload = vi.fn();
    render(<AttachmentList attachments={mockAttachments} onDownload={onDownload} />);

    // Expand to see versions
    const header = screen.getByText('采购合同.pdf').closest('.attachment-group-header');
    fireEvent.click(header!);

    // Click download button for first version
    const downloadButtons = screen.getAllByText('下载');
    fireEvent.click(downloadButtons[0]);

    expect(onDownload).toHaveBeenCalledWith('att-1');
  });

  it('应该在再次点击时折叠版本列表', () => {
    render(<AttachmentList attachments={mockAttachments} />);

    const header = screen.getByText('采购合同.pdf').closest('.attachment-group-header');

    // Expand
    fireEvent.click(header!);
    expect(screen.getByText('v2.0')).toBeInTheDocument();

    // Collapse
    fireEvent.click(header!);
    expect(screen.queryByText('v2.0')).not.toBeInTheDocument();
  });

  it('应该处理多个文件组', () => {
    const multipleAttachments: AttachmentGroup[] = [
      mockAttachments[0],
      {
        fileName: '补充协议.docx',
        versionCount: 1,
        versions: [
          {
            id: 'att-3',
            contractId: 'contract-1',
            fileName: '补充协议.docx',
            version: 'v1.0',
            fileSize: 512000,
            mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            storageKey: 'key-3',
            uploaderId: 'user-1',
            uploader: {
              id: 'user-1',
              name: '张三',
              dingtalkUserId: 'dt-1',
              role: '法务',
              createdAt: '2025-03-01T10:00:00Z',
              updatedAt: '2025-03-01T10:00:00Z',
            },
            createdAt: '2025-03-02T10:00:00Z',
          },
        ],
      },
    ];

    render(<AttachmentList attachments={multipleAttachments} />);

    expect(screen.getByText('采购合同.pdf')).toBeInTheDocument();
    expect(screen.getByText('补充协议.docx')).toBeInTheDocument();
    expect(screen.getByText('2 个版本')).toBeInTheDocument();
    expect(screen.getByText('1 个版本')).toBeInTheDocument();
  });
});
