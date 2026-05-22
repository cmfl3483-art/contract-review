import { useEffect, useState } from 'react';
import { Modal, Input, List, Spin, Empty, Tag, message } from 'antd';
import axios from '../../utils/axios';
import type { ApiResponse } from '../../types';
import { API_BASE_URL, API_ENDPOINTS } from '../../config/api';
import { useUserStore } from '../../stores/useUserStore';
import { useApproveReview } from '../../hooks/useReviews';
import './QuickApprovalDialog.css';

const { TextArea } = Input;

interface QuickApprovalDialogProps {
  visible: boolean;
  contractId: string | null;
  contractName?: string;
  /** 已知的待审项 (来自合同详情)，如果传了就跳过远程拉取 */
  presetReview?: { id: string; role: string; step?: string } | null;
  onClose: () => void;
  onSuccess?: () => void;
}

const DEFAULT_OPINION = '同意并确认';

/**
 * 快速审批弹窗 (共享组件)
 * - 从合同详情接口拉取 reviewers (与详情页同源)
 * - 过滤当前用户的未完成项
 * - 任何条数都直接进入“确认通过”输入框
 * - 确认后调用真实 API 完成审批
 */
const QuickApprovalDialog: React.FC<QuickApprovalDialogProps> = ({
  visible,
  contractId,
  contractName,
  presetReview,
  onClose,
  onSuccess,
}) => {
  const currentUser = useUserStore((s) => s.currentUser);
  const approveMutation = useApproveReview();

  const [loading, setLoading] = useState(false);
  const [pendingReviews, setPendingReviews] = useState<
    Array<{ id: string; role: string; step?: string }>
  >([]);
  const [selectedReview, setSelectedReview] = useState<{
    id: string;
    role: string;
    step?: string;
  } | null>(null);
  const [opinion, setOpinion] = useState(DEFAULT_OPINION);

  // 打开时拉取待审项
  useEffect(() => {
    if (!visible || !contractId) return;

    // 重置
    setOpinion(DEFAULT_OPINION);
    setSelectedReview(null);

    // 如果调用方已经指定了具体 review，跳过远程拉取
    if (presetReview) {
      setSelectedReview(presetReview);
      setPendingReviews([]);
      return;
    }

    if (!currentUser) {
      message.error('未登录，无法审批');
      onClose();
      return;
    }

    const fetchPending = async () => {
      try {
        setLoading(true);
        // 改走合同详情接口 (与详情页同源)，避免 reviews 接口过滤掉 pending 导致数据丢失
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const resp = await axios.get<ApiResponse<any>>(
          `${API_BASE_URL}${API_ENDPOINTS.CONTRACTS.DETAIL(contractId)}`
        );
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const reviewers: any[] = resp.data?.data?.reviewers ?? [];
        const myPending = reviewers
          .filter(
            (r) =>
              r &&
              r.status !== 'approved' &&
              String(r.userId ?? r.user_id ?? '') === String(currentUser.id)
          )
          .map((r) => ({
            id: String(r.id),
            role: r.role,
            step: r.step,
          }));
        setPendingReviews(myPending);
        // 与详情页体验保持一致：任何 pending 都直接选中第一条，跳过选择列表
        if (myPending.length >= 1) {
          setSelectedReview(myPending[0]);
        }
      } catch (err) {
        console.error('拉取合同详情失败:', err);
        message.error('加载待审项失败');
      } finally {
        setLoading(false);
      }
    };

    fetchPending();
  }, [visible, contractId, currentUser, presetReview, onClose]);

  const handleSelect = (review: { id: string; role: string; step?: string }) => {
    setSelectedReview({ id: review.id, role: review.role, step: review.step });
  };

  const handleConfirm = async () => {
    if (!contractId || !selectedReview) {
      message.error('请选择待审项');
      return;
    }
    if (!opinion.trim()) {
      message.error('请输入审批意见');
      return;
    }
    try {
      await approveMutation.mutateAsync({
        contractId,
        reviewId: selectedReview.id,
        opinion: opinion.trim(),
      });
      message.success('审批成功');
      onSuccess?.();
      onClose();
    } catch (err) {
      const msg = err instanceof Error ? err.message : '审批失败，请重试';
      message.error(msg);
    }
  };

  // 保留 contractName 变量以避免未使用警告（外部仍会传入，预留未来扩展）
  void contractName;

  const showSelection = !presetReview && pendingReviews.length > 1 && !selectedReview;

  return (
    <Modal
      title={selectedReview ? '确认通过' : '选择要同意的评审项'}
      open={visible}
      onOk={handleConfirm}
      onCancel={onClose}
      confirmLoading={approveMutation.isPending}
      okText="通过"
      cancelText="取消"
      width={400}
      okButtonProps={{ disabled: !selectedReview }}
      footer={
        showSelection || (loading && !selectedReview)
          ? null
          : undefined
      }
    >
      {loading ? (
        <div className="qad-loading">
          <Spin tip="加载中..." />
        </div>
      ) : !presetReview && pendingReviews.length === 0 && !selectedReview ? (
        <Empty description="暂无您可审批的待办项" />
      ) : showSelection ? (
        <List
          className="qad-selection"
          dataSource={pendingReviews}
          renderItem={(review) => (
            <List.Item
              className="qad-selection-item"
              onClick={() => handleSelect(review)}
            >
              <List.Item.Meta
                title={
                  <span>
                    <Tag color="processing">{review.role}</Tag>
                    {review.step}
                  </span>
                }
                description={review.step ? `步骤：${review.step}` : null}
              />
            </List.Item>
          )}
        />
      ) : (
        <TextArea
          value={opinion}
          onChange={(e) => setOpinion(e.target.value)}
          rows={3}
          maxLength={500}
          placeholder="请输入审批意见"
          autoFocus
        />
      )}
    </Modal>
  );
};

export default QuickApprovalDialog;
