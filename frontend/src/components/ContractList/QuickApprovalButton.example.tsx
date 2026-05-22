/**
 * QuickApprovalButton Usage Example
 *
 * This file demonstrates how to use the QuickApprovalButton component
 * in different scenarios.
 */

import QuickApprovalButton from './QuickApprovalButton';
import type { Review } from '../../types';

// Example 1: Single Pending Review
export const SinglePendingReviewExample = () => {
  const singlePendingReview: Review[] = [
    {
      id: 'review-1',
      contractId: 'contract-123',
      reviewerId: 'user-1',
      role: '法务',
      step: '法务初审',
      status: 'pending',
      likes: 0,
      likedBy: [],
      createdAt: '2025-03-01T10:00:00Z',
      updatedAt: '2025-03-01T10:00:00Z',
    },
  ];

  const handleSuccess = () => {
    console.log('Approval successful! Refreshing data...');
    // In real app: refetch contract list, update UI, etc.
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #e8e8e8', borderRadius: '4px' }}>
      <h3>示例 1: 单个待处理项</h3>
      <p>点击"同意"按钮将直接显示确认对话框</p>
      <QuickApprovalButton
        contractId="contract-123"
        contractName="采购合同 - 2025年度办公用品采购"
        pendingReviews={singlePendingReview}
        onApprovalSuccess={handleSuccess}
      />
    </div>
  );
};

// Example 2: Multiple Pending Reviews
export const MultiplePendingReviewsExample = () => {
  const multiplePendingReviews: Review[] = [
    {
      id: 'review-1',
      contractId: 'contract-456',
      reviewerId: 'user-1',
      role: '法务',
      step: '法务初审',
      status: 'pending',
      likes: 0,
      likedBy: [],
      createdAt: '2025-03-01T10:00:00Z',
      updatedAt: '2025-03-01T10:00:00Z',
    },
    {
      id: 'review-2',
      contractId: 'contract-456',
      reviewerId: 'user-1',
      role: '财务',
      step: '财务审核',
      status: 'pending',
      likes: 0,
      likedBy: [],
      createdAt: '2025-03-01T11:00:00Z',
      updatedAt: '2025-03-01T11:00:00Z',
    },
    {
      id: 'review-3',
      contractId: 'contract-456',
      reviewerId: 'user-1',
      role: '业务',
      step: '业务确认',
      status: 'pending',
      likes: 0,
      likedBy: [],
      createdAt: '2025-03-01T12:00:00Z',
      updatedAt: '2025-03-01T12:00:00Z',
    },
  ];

  const handleSuccess = () => {
    console.log('Approval successful! Refreshing data...');
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #e8e8e8', borderRadius: '4px' }}>
      <h3>示例 2: 多个待处理项</h3>
      <p>点击"同意"按钮将显示待处理项选择列表</p>
      <QuickApprovalButton
        contractId="contract-456"
        contractName="服务合同 - IT系统维护服务协议"
        pendingReviews={multiplePendingReviews}
        onApprovalSuccess={handleSuccess}
      />
    </div>
  );
};

// Example 3: No Pending Reviews (Button Hidden)
export const NoPendingReviewsExample = () => {
  const noPendingReviews: Review[] = [];

  return (
    <div style={{ padding: '20px', border: '1px solid #e8e8e8', borderRadius: '4px' }}>
      <h3>示例 3: 无待处理项</h3>
      <p>当没有待处理项时,按钮不会显示</p>
      <QuickApprovalButton
        contractId="contract-789"
        contractName="租赁合同 - 办公场地租赁协议"
        pendingReviews={noPendingReviews}
      />
      <p style={{ color: '#999', marginTop: '10px' }}>(按钮已隐藏,因为没有待处理项)</p>
    </div>
  );
};

// Example 4: Integration with Contract Card
export const ContractCardIntegrationExample = () => {
  const contract = {
    id: 'contract-999',
    name: '销售合同 - 产品销售协议',
    description: '与客户签订的产品销售协议',
    status: 'progress' as const,
    initiatorId: 'user-100',
    ccUsers: ['user-101', 'user-102'],
    createdAt: '2025-03-01T09:00:00Z',
    updatedAt: '2025-03-01T09:00:00Z',
  };

  const pendingReviews: Review[] = [
    {
      id: 'review-10',
      contractId: contract.id,
      reviewerId: 'user-1',
      role: '法务',
      step: '合同审核',
      status: 'pending',
      likes: 0,
      likedBy: [],
      createdAt: '2025-03-01T10:00:00Z',
      updatedAt: '2025-03-01T10:00:00Z',
    },
  ];

  const handleSuccess = () => {
    console.log('Approval successful! Refreshing contract list...');
    // In real app:
    // - Refetch contract list
    // - Update pending count badge
    // - Show success notification
    // - Update timeline
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #e8e8e8', borderRadius: '4px' }}>
      <h3>示例 4: 集成到合同卡片</h3>
      <div
        style={{
          padding: '16px',
          border: '1px solid #d9d9d9',
          borderRadius: '4px',
          backgroundColor: '#fff',
        }}
      >
        <div style={{ marginBottom: '8px' }}>
          <strong>{contract.name}</strong>
        </div>
        <div style={{ fontSize: '12px', color: '#999', marginBottom: '8px' }}>
          发起人: 张三 | 2025-03-01
        </div>
        <div style={{ marginBottom: '12px' }}>
          <span
            style={{
              padding: '2px 8px',
              backgroundColor: '#e6f7ff',
              color: '#1890ff',
              borderRadius: '2px',
              fontSize: '12px',
            }}
          >
            进行中
          </span>
        </div>
        <QuickApprovalButton
          contractId={contract.id}
          contractName={contract.name}
          pendingReviews={pendingReviews}
          onApprovalSuccess={handleSuccess}
        />
      </div>
    </div>
  );
};

// Demo Page Component
export const QuickApprovalButtonDemo = () => {
  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>QuickApprovalButton 组件示例</h1>
      <p style={{ color: '#666', marginBottom: '40px' }}>
        以下示例展示了 QuickApprovalButton 组件在不同场景下的使用方法
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <SinglePendingReviewExample />
        <MultiplePendingReviewsExample />
        <NoPendingReviewsExample />
        <ContractCardIntegrationExample />
      </div>

      <div
        style={{
          marginTop: '40px',
          padding: '20px',
          backgroundColor: '#f5f5f5',
          borderRadius: '4px',
        }}
      >
        <h3>使用说明</h3>
        <ul style={{ lineHeight: '1.8' }}>
          <li>当合同有待处理评审项时,显示"同意"按钮</li>
          <li>单个待处理项:点击按钮直接显示确认对话框</li>
          <li>多个待处理项:点击按钮显示选择列表,选择后显示确认对话框</li>
          <li>确认对话框中预填"同意并通过"文本,用户可以修改</li>
          <li>确认后调用 API 提交审批,并触发 onApprovalSuccess 回调</li>
        </ul>
      </div>
    </div>
  );
};

export default QuickApprovalButtonDemo;
