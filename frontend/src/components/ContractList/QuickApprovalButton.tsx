import { useState } from 'react';
import { Button, Modal, Input, List, message } from 'antd';
import { CheckOutlined } from '@ant-design/icons';
import type { Review } from '../../types';
import { useApproveReview } from '../../hooks/useReviews';
import './QuickApprovalButton.css';

const { TextArea } = Input;

interface QuickApprovalButtonProps {
  contractId: string;
  contractName: string;
  pendingReviews: Review[];
  onApprovalSuccess?: () => void;
}

/**
 * QuickApprovalButton Component
 *
 * Displays a quick approval button for contracts with pending reviews.
 * - Shows "同意" button only when there are pending reviews for current user
 * - Single pending item: directly shows confirmation dialog
 * - Multiple pending items: shows selection list first
 * - Pre-fills "同意并通过" text in confirmation dialog
 *
 * Requirements: 9.1-9.9
 */
const QuickApprovalButton: React.FC<QuickApprovalButtonProps> = ({
  contractId,
  contractName,
  pendingReviews,
  onApprovalSuccess,
}) => {
  const approveMutation = useApproveReview();
  const [isSelectionModalVisible, setIsSelectionModalVisible] = useState(false);
  const [isConfirmModalVisible, setIsConfirmModalVisible] = useState(false);
  const [selectedReview, setSelectedReview] = useState<Review | null>(null);
  const [opinion, setOpinion] = useState('同意并确认');

  // Don't render button if no pending reviews
  if (!pendingReviews || pendingReviews.length === 0) {
    return null;
  }

  /**
   * Handle button click
   * - Single pending item: show confirmation dialog directly
   * - Multiple pending items: show selection list
   */
  const handleButtonClick = () => {
    if (pendingReviews.length === 1) {
      // Single pending item - show confirmation dialog directly
      setSelectedReview(pendingReviews[0]);
      setOpinion('同意并确认');
      setIsConfirmModalVisible(true);
    } else {
      // Multiple pending items - show selection list
      setIsSelectionModalVisible(true);
    }
  };

  /**
   * Handle review selection from list
   */
  const handleReviewSelect = (review: Review) => {
    setSelectedReview(review);
    setOpinion('同意并确认');
    setIsSelectionModalVisible(false);
    setIsConfirmModalVisible(true);
  };

  /**
   * Handle approval confirmation
   */
  const handleConfirm = async () => {
    if (!selectedReview) return;
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
      setIsConfirmModalVisible(false);
      setSelectedReview(null);
      setOpinion('同意并确认');

      // Trigger success callback to refresh data
      onApprovalSuccess?.();
    } catch (error) {
      console.error('Approval failed:', error);
      const msg = error instanceof Error ? error.message : '审批失败,请重试';
      message.error(msg);
    }
  };

  /**
   * Handle modal cancel
   */
  const handleCancel = () => {
    setIsSelectionModalVisible(false);
    setIsConfirmModalVisible(false);
    setSelectedReview(null);
    setOpinion('同意并确认');
  };

  return (
    <>
      {/* Quick Approval Button */}
      <Button
        type="primary"
        size="small"
        icon={<CheckOutlined />}
        onClick={handleButtonClick}
        className="quick-approval-button"
      >
        同意
      </Button>

      {/* Selection Modal - for multiple pending items */}
      <Modal
        title="选择待处理项"
        open={isSelectionModalVisible}
        onCancel={handleCancel}
        footer={null}
        width={500}
      >
        <List
          dataSource={pendingReviews}
          renderItem={(review) => (
            <List.Item
              className="pending-review-item"
              onClick={() => handleReviewSelect(review)}
              style={{ cursor: 'pointer' }}
            >
              <List.Item.Meta
                title={
                  <div>
                    <span className="review-role">{review.role}</span>
                    {review.step && <span className="review-step"> - {review.step}</span>}
                  </div>
                }
                description={
                  <div className="review-status">
                    状态: {review.status === 'pending' ? '待处理' : '评审中'}
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Modal>

      {/* Confirmation Modal - for approval */}
      <Modal
        title="确认同意"
        open={isConfirmModalVisible}
        onOk={handleConfirm}
        onCancel={handleCancel}
        confirmLoading={approveMutation.isPending}
        okText="确定"
        cancelText="取消"
        width={500}
      >
        <div className="approval-confirmation">
          <div className="contract-info">
            <div className="info-label">合同名称:</div>
            <div className="info-value">{contractName}</div>
          </div>

          {selectedReview && (
            <div className="review-info">
              <div className="info-label">评审项:</div>
              <div className="info-value">
                {selectedReview.role}
                {selectedReview.step && ` - ${selectedReview.step}`}
              </div>
            </div>
          )}

          <div className="opinion-input">
            <div className="info-label">审批意见:</div>
            <TextArea
              value={opinion}
              onChange={(e) => setOpinion(e.target.value)}
              placeholder="请输入审批意见"
              rows={4}
              maxLength={500}
              showCount
            />
          </div>
        </div>
      </Modal>
    </>
  );
};

export default QuickApprovalButton;
