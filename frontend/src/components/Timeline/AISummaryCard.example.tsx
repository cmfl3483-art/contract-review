import React from 'react';
import AISummaryCard from './AISummaryCard';
import type { AISummary } from '../../types';

/**
 * Example usage of AISummaryCard component
 * This file demonstrates different states and scenarios
 */

// Example 1: Approval in progress with key issues
const summaryInProgress: AISummary = {
  id: 'summary-1',
  contractId: 'contract-1',
  approvalStatus: 'in_progress',
  completedCount: 3,
  totalCount: 5,
  reviewCount: 8,
  keyIssues: [
    {
      issue: '合同中缺少违约责任条款，建议补充明确的违约责任和赔偿标准',
      solution: '已在第5条补充违约责任条款',
    },
    {
      issue: '付款方式需要明确具体的付款时间节点',
    },
    {
      issue: '知识产权归属问题需要进一步明确',
      solution: '双方已达成一致，知识产权归甲方所有',
    },
  ],
  createdAt: '2025-01-15T10:00:00Z',
  updatedAt: '2025-01-15T10:00:00Z',
};

// Example 2: Approval completed with no issues
const summaryCompleted: AISummary = {
  id: 'summary-2',
  contractId: 'contract-2',
  approvalStatus: 'completed',
  completedCount: 5,
  totalCount: 5,
  reviewCount: 12,
  keyIssues: [],
  createdAt: '2025-01-15T10:00:00Z',
  updatedAt: '2025-01-15T10:00:00Z',
};

// Example 3: Early stage with one issue
const summaryEarlyStage: AISummary = {
  id: 'summary-3',
  contractId: 'contract-3',
  approvalStatus: 'in_progress',
  completedCount: 1,
  totalCount: 5,
  reviewCount: 2,
  keyIssues: [
    {
      issue: '合同金额需要财务部门确认',
    },
  ],
  createdAt: '2025-01-15T10:00:00Z',
  updatedAt: '2025-01-15T10:00:00Z',
};

// Example 4: Multiple issues with solutions
const summaryWithSolutions: AISummary = {
  id: 'summary-4',
  contractId: 'contract-4',
  approvalStatus: 'in_progress',
  completedCount: 4,
  totalCount: 6,
  reviewCount: 15,
  keyIssues: [
    {
      issue: '合同期限建议延长至2年',
      solution: '已与对方协商，同意延长至2年',
    },
    {
      issue: '保密条款需要加强',
      solution: '已补充保密期限和违约责任',
    },
    {
      issue: '争议解决方式建议采用仲裁',
      solution: '双方同意采用北京仲裁委员会仲裁',
    },
  ],
  createdAt: '2025-01-15T10:00:00Z',
  updatedAt: '2025-01-15T10:00:00Z',
};

const AISummaryCardExample: React.FC = () => {
  return (
    <div style={{ padding: '24px', background: '#f5f5f5' }}>
      <h2>AISummaryCard Examples</h2>

      <div style={{ marginBottom: '24px' }}>
        <h3>Example 1: Approval In Progress with Key Issues</h3>
        <AISummaryCard summary={summaryInProgress} />
      </div>

      <div style={{ marginBottom: '24px' }}>
        <h3>Example 2: Approval Completed (No Issues)</h3>
        <AISummaryCard summary={summaryCompleted} />
      </div>

      <div style={{ marginBottom: '24px' }}>
        <h3>Example 3: Early Stage (One Issue)</h3>
        <AISummaryCard summary={summaryEarlyStage} />
      </div>

      <div style={{ marginBottom: '24px' }}>
        <h3>Example 4: Multiple Issues with Solutions</h3>
        <AISummaryCard summary={summaryWithSolutions} />
      </div>
    </div>
  );
};

export default AISummaryCardExample;
