import { useEffect, useState } from 'react';
import { Alert, Empty, Spin, Tag, Modal, Upload, Input, Button, Space, message } from 'antd';
import { AxiosError } from 'axios';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  UserOutlined,
  UploadOutlined,
  DownOutlined,
  UpOutlined,
  DownloadOutlined,
  FileTextOutlined,
  CheckOutlined,
  EditOutlined,
} from '@ant-design/icons';
import { useSelectedContractStore } from '../../stores';
import { useUserStore } from '../../stores/useUserStore';
import { useContractDetail, useUploadAttachment } from '../../hooks';
import { useReviseContract } from '../../hooks/useReviseContract';
import { formatDateTime } from '../../utils/time';
import { getAttachmentDownloadUrl, downloadAttachment } from '../../hooks/useAttachments';
import QuickApprovalDialog from '../QuickApprovalDialog/QuickApprovalDialog';
import './ContractDetail.css';

const ContractDetail: React.FC = () => {
  const { selectedContractId } = useSelectedContractStore();
  const currentUser = useUserStore((s) => s.currentUser);
  const { data, isLoading, error } = useContractDetail(selectedContractId || undefined);
  const uploadAttachmentMutation = useUploadAttachment();
  const reviseContractMutation = useReviseContract(selectedContractId || '');

  // 折叠/展开详情 (默认展开，折叠后仅显示合同名称)
  const [expanded, setExpanded] = useState(true);

  // 默认全部展开附件分组: 记录被用户主动收起的分组
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [uploadVersion, setUploadVersion] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // 编辑模式状态
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editContractNumber, setEditContractNumber] = useState('');
  const [editDescription, setEditDescription] = useState('');

  // 切换合同时退出编辑模式（避免编辑状态串到其他合同）
  useEffect(() => {
    setIsEditing(false);
  }, [selectedContractId]);

  // 快速审批弹窗 (针对当前用户的某条 review)
  const [approvalReview, setApprovalReview] = useState<{
    id: string;
    role: string;
    step?: string;
  } | null>(null);

  const toggleGroup = (fileName: string) => {
    const next = new Set(collapsedGroups);
    if (next.has(fileName)) {
      next.delete(fileName);
    } else {
      next.add(fileName);
    }
    setCollapsedGroups(next);
  };

  const handleUploadClick = () => {
    setUploadModalVisible(true);
    setUploadVersion('');
    setUploadFile(null);
  };

  const handleUploadConfirm = () => {
    if (!uploadFile || !selectedContractId) {
      message.error('请选择文件');
      return;
    }

    uploadAttachmentMutation.mutate(
      {
        contractId: selectedContractId,
        file: uploadFile,
        version: uploadVersion || undefined,
      },
      {
        onSuccess: () => {
          message.success('上传成功');
          setUploadModalVisible(false);
          setUploadVersion('');
          setUploadFile(null);
        },
        onError: (error) => {
          message.error(error instanceof Error ? error.message : '上传失败');
        },
      }
    );
  };

  // 进入编辑模式：用当前合同值填充编辑表单
  const handleEnterEdit = () => {
    if (!data?.contract) return;
    setEditName(data.contract.name || '');
    setEditContractNumber(data.contract.contractNumber || '');
    setEditDescription(data.contract.description || '');
    setIsEditing(true);
  };

  // 取消编辑：恢复原值并退出
  const handleCancelEdit = () => {
    if (data?.contract) {
      setEditName(data.contract.name || '');
      setEditDescription(data.contract.description || '');
    }
    setIsEditing(false);
  };

  // 保存编辑：仅传 dirty 字段
  const handleSaveEdit = async () => {
    if (!data?.contract) return;

    const trimmedName = editName.trim();
    if (trimmedName.length < 1 || trimmedName.length > 200) {
      message.error('合同名称长度需在 1-200 字符');
      return;
    }
    if (editDescription.length > 5000) {
      message.error('合同描述长度不能超过 5000 字符');
      return;
    }

    const payload: { name?: string; contract_number?: string; description?: string } = {};
    const originalName = (data.contract.name || '').trim();
    const originalContractNumber = (data.contract.contractNumber || '').trim();
    const originalDescription = data.contract.description || '';

    if (trimmedName !== originalName) {
      payload.name = trimmedName;
    }
    if (editContractNumber.trim() !== originalContractNumber) {
      payload.contract_number = editContractNumber.trim();
    }
    if (editDescription !== originalDescription) {
      payload.description = editDescription;
    }

    // 没有任何变更，直接退出编辑模式
    if (Object.keys(payload).length === 0) {
      setIsEditing(false);
      return;
    }

    try {
      await reviseContractMutation.mutateAsync(payload);
      message.success('保存成功，所有评审人需重新审批');
      setIsEditing(false);
    } catch (err) {
      // 优先解析后端结构化错误（HTTP 422 detail = { field, limit }）
      if (err instanceof AxiosError) {
        const status = err.response?.status;
        const detail = (err.response?.data as { detail?: unknown; error?: string } | undefined)
          ?.detail;
        if (status === 422 && detail && typeof detail === 'object') {
          const { field, limit } = detail as { field?: string; limit?: string };
          if (field || limit) {
            message.error(
              `字段 ${field || '未知'} 超出限制${limit ? `（${limit}）` : ''}`
            );
            return;
          }
        }
        const errMsg =
          (err.response?.data as { error?: string; message?: string } | undefined)?.error ||
          (err.response?.data as { error?: string; message?: string } | undefined)?.message ||
          err.message;
        message.error(errMsg || '保存失败');
        return;
      }
      message.error(err instanceof Error ? err.message : '保存失败');
    }
  };

  // 如果没有选中合同，显示空状态
  if (!selectedContractId) {
    return (
      <div className="contract-detail">
        <div className="contract-detail-content">
          <Empty description="请选择一个合同查看详情" />
        </div>
      </div>
    );
  }

  // 加载状态
  if (isLoading) {
    return (
      <div className="contract-detail">
        <div className="contract-detail-content">
          <Spin size="large" tip="加载中..." />
        </div>
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div className="contract-detail">
        <div className="contract-detail-content">
          <Empty description={error instanceof Error ? error.message : '加载失败'} />
        </div>
      </div>
    );
  }

  // 数据不存在
  if (!data) {
    return (
      <div className="contract-detail">
        <div className="contract-detail-content">
          <Empty description="合同不存在" />
        </div>
      </div>
    );
  }

  const { contract, reviewers, attachments } = data;

  // 是否可编辑：仅发起人在 progress 状态下显示「编辑」按钮
  const canEdit =
    !!currentUser &&
    !!contract.initiator &&
    currentUser.id === contract.initiator.id &&
    contract.status === 'progress';

  // 区分已审核和待审核的评审人
  const approvedReviewers = reviewers.filter((r) => r.status === 'approved');
  const pendingReviewers = reviewers.filter((r) => r.status !== 'approved');

  // 当前用户的待审项 (id 是 review.id, userId 是用户 id)
  const myPendingReviews = currentUser
    ? reviewers.filter(
        (r) => r.status !== 'approved' && r.userId === currentUser.id
      )
    : [];

  // 附件总数量量化
  const totalAttachmentCount = attachments.reduce(
    (sum, group) => sum + (group.versionCount || group.versions?.length || 0),
    0
  );

  return (
    <div className="contract-detail">
      {/* 标题 + 描述 */}
      <div className="contract-detail-header">
        {isEditing ? (
          <div className="contract-edit-form">
            <Alert
              type="warning"
              showIcon
              message="修改后所有评审人需重新审批"
              style={{ marginBottom: 12 }}
            />
            <div style={{ marginBottom: 8 }}>
              <Input
                value={editContractNumber}
                maxLength={100}
                placeholder="合同编号"
                onChange={(e) => setEditContractNumber(e.target.value)}
                disabled={reviseContractMutation.isPending}
              />
            </div>
            <div style={{ marginBottom: 8 }}>
              <Input
                value={editName}
                maxLength={200}
                showCount
                placeholder="合同名称"
                onChange={(e) => setEditName(e.target.value)}
                disabled={reviseContractMutation.isPending}
              />
            </div>
            <div style={{ marginBottom: 8 }}>
              <Input.TextArea
                value={editDescription}
                maxLength={5000}
                showCount
                rows={4}
                placeholder="合同描述"
                onChange={(e) => setEditDescription(e.target.value)}
                disabled={reviseContractMutation.isPending}
              />
            </div>
            <Space>
              <Button
                type="primary"
                onClick={handleSaveEdit}
                loading={reviseContractMutation.isPending}
              >
                保存
              </Button>
              <Button
                onClick={handleCancelEdit}
                disabled={reviseContractMutation.isPending}
              >
                取消
              </Button>
            </Space>
          </div>
        ) : (
          <>
            <div className="contract-title-row">
              <h2 className="contract-title">{(contract.contractNumber ? contract.contractNumber + ' ' : '') + contract.name}</h2>
              {canEdit && (
                <Button
                  size="small"
                  icon={<EditOutlined />}
                  onClick={handleEnterEdit}
                >
                  编辑
                </Button>
              )}
            </div>
            {expanded && contract.description && (
              <p className="contract-description">
                <span role="img" aria-label="file">📄</span> {contract.description}
              </p>
            )}
          </>
        )}
      </div>

      {/* 折叠/展开分隔条 */}
      <div
        className="contract-detail-toggle"
        onClick={() => setExpanded((v) => !v)}
        role="button"
        tabIndex={0}
      >
        {expanded ? (
          <>
            <UpOutlined />
            <span>收起详情</span>
          </>
        ) : (
          <>
            <DownOutlined />
            <span>展开详情</span>
          </>
        )}
      </div>

      {/* 以下区块仅在展开时显示 */}
      {expanded && (
        <>
      {/* 附件区 (对齐原型: attach-info + attach-header + attachment-list) */}
      <div className="contract-section attach-info">
        <div className="attach-header">
          <h3 className="section-title">
            <span role="img" aria-label="clip">📎</span> 附件
            {totalAttachmentCount > 0 && (
              <span className="attach-count"> ({totalAttachmentCount})</span>
            )}
          </h3>
          <button className="upload-btn" onClick={handleUploadClick}>
            <UploadOutlined />
            <span>上传新版本</span>
          </button>
        </div>
        {attachments.length === 0 ? (
          <Empty
            description="暂无附件"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{ margin: '12px 0' }}
          />
        ) : (
          <div className="attachment-list">
            {attachments.map((group) => {
              const isExpanded = !collapsedGroups.has(group.fileName);
              return (
                <div key={group.fileName} className="attachment-group">
                  <div
                    className="attachment-group-header"
                    onClick={() => toggleGroup(group.fileName)}
                  >
                    <div className="attachment-group-name">
                      <FileTextOutlined style={{ color: '#1677ff' }} />
                      <span>{group.fileName}</span>
                      <Tag color="blue">{group.versionCount} 个版本</Tag>
                    </div>
                    {isExpanded ? <UpOutlined /> : <DownOutlined />}
                  </div>
                  {isExpanded && (
                    <div className="attachment-versions">
                      {group.versions.map((version, index) => (
                        <div key={version.id} className="attachment-version">
                          <span className="version-badge">{version.version}</span>
                          {index === 0 && <span className="version-latest">最新</span>}
                          <span className="version-time">
                            {formatDateTime(version.createdAt)}
                          </span>
                          <span className="version-uploader">
                            by {version.uploader?.name || '未知'}
                          </span>
                          <a
                            href={getAttachmentDownloadUrl(version.id)}
                            onClick={(e) => {
                              e.preventDefault();
                              downloadAttachment(
                                version.id,
                                group.fileName
                              ).catch((err) => {
                                message.error(
                                  err instanceof Error
                                    ? `下载失败：${err.message}`
                                    : '下载失败'
                                );
                              });
                            }}
                            className="version-download"
                            title="下载"
                          >
                            <DownloadOutlined />
                            <span>下载</span>
                          </a>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 评审人状态 (原型: reviewer-status 横向三步序列) */}
      <div className="contract-section reviewer-status">
        <div className="status-done">
          <CheckCircleOutlined />
          <span>
            已审核：
            {approvedReviewers.length
              ? approvedReviewers.map((r) => r.name).join('、')
              : '无'}
          </span>
        </div>
        <div className="status-pending">
          <ClockCircleOutlined />
          <span>
            待审核：
            {pendingReviewers.length
              ? pendingReviewers.map((r) => r.name).join('、')
              : '无'}
          </span>
        </div>
        <div className="status-total">
          <UserOutlined />
          <span>需审核人总数：{reviewers.length}</span>
        </div>
      </div>

      {/* 我的待审 (仅当前用户对该合同存在 pending 评审时显示) */}
      {myPendingReviews.length > 0 && (
        <div className="contract-section my-pending-reviews">
          <div className="my-pending-header">
            <ClockCircleOutlined style={{ color: '#fa8c16' }} />
            <span className="my-pending-title">我的待审 ({myPendingReviews.length})</span>
          </div>
          <div className="my-pending-list">
            {myPendingReviews.map((r) => (
              <div key={r.id} className="my-pending-item">
                <div className="my-pending-info">
                  <Tag color="processing">{r.role}</Tag>
                  <span className="my-pending-name">作为「{r.role}」需要您审批</span>
                </div>
                <Button
                  type="primary"
                  size="small"
                  icon={<CheckOutlined />}
                  onClick={() =>
                    setApprovalReview({ id: r.id, role: r.role })
                  }
                >
                  同意
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
        </>
      )}

      {/* 上传附件模态框 */}
      <Modal
        title="上传附件新版本"
        open={uploadModalVisible}
        onOk={handleUploadConfirm}
        onCancel={() => setUploadModalVisible(false)}
        confirmLoading={uploadAttachmentMutation.isPending}
        okText="上传"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 8 }}>选择文件</label>
          <Upload
            beforeUpload={(file) => {
              setUploadFile(file);
              return false;
            }}
            maxCount={1}
            fileList={uploadFile ? [uploadFile as any] : []}
            onRemove={() => setUploadFile(null)}
          >
            <button className="upload-btn">
              <UploadOutlined />
              <span>选择文件</span>
            </button>
          </Upload>
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 8 }}>版本号（可选）</label>
          <Input
            placeholder="例如: v2.0"
            value={uploadVersion}
            onChange={(e) => setUploadVersion(e.target.value)}
          />
          <div style={{ fontSize: 12, color: '#666', marginTop: 8 }}>
            💡 提示：如果上传同名文件，将自动创建新版本
          </div>
        </div>
      </Modal>

      {/* 快速审批弹窗 */}
      <QuickApprovalDialog
        visible={!!approvalReview}
        contractId={selectedContractId}
        contractName={contract.name}
        presetReview={approvalReview}
        onClose={() => setApprovalReview(null)}
      />
    </div>
  );
};

export default ContractDetail;
