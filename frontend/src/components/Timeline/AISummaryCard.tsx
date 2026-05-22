import React from 'react';
import { RobotOutlined } from '@ant-design/icons';
import type { AISummary } from '../../types/index';
import './AISummaryCard.css';

interface AISummaryCardProps {
  summary: AISummary;
}

const AISummaryCard: React.FC<AISummaryCardProps> = ({ summary }) => {
  const statusText = summary.approvalStatus === 'completed' ? '已完成' : '进行中';
  const statusClass = summary.approvalStatus === 'completed' ? 'completed' : 'pending';

  return (
    <div className="ai-summary">
      <div className="ai-summary-header">
        <RobotOutlined />
        <span>AI 智能总结</span>
      </div>
      <div className="ai-summary-content">
        <div className="ai-summary-section">
          <div className="ai-summary-label">
            审批进度：
            <span className={`ai-summary-status ${statusClass}`}>{statusText}</span>
          </div>
        </div>
        <div className="ai-summary-section">
          <div className="ai-summary-label">
            已完成：{summary.completedCount}/{summary.totalCount} 人
          </div>
        </div>
        <div className="ai-summary-section">
          <div className="ai-summary-label">评审意见总数：{summary.reviewCount} 条</div>
        </div>
        {summary.keyIssues && summary.keyIssues.length > 0 && (
          <div className="ai-summary-section">
            <div className="ai-summary-label">关键问题：</div>
            <div className="ai-summary-text">
              {summary.keyIssues.slice(0, 3).map((issue, index) => (
                <div key={index} className="key-issue-item">
                  <div className="issue-text">• {issue.issue}</div>
                  {issue.solution && (
                    <div className="solution-text">→ 解决方案：{issue.solution}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AISummaryCard;
