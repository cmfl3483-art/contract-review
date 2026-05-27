import React, { memo } from 'react';
import { Tag, Tooltip, Avatar } from 'antd';
import { UserOutlined, CheckOutlined } from '@ant-design/icons';
import type { Contract } from '../../types';
import { formatRelativeTime } from '../../utils/time';
import './ContractCard.css';

interface ContractCardProps {
  contract: Contract;
  selected?: boolean;
  onSelect: (contractId: string) => void;
  onApprove?: (contractId: string) => void;
}

const ContractCard: React.FC<ContractCardProps> = memo(({
  contract,
  selected = false,
  onSelect,
  onApprove,
}) => {
  const handleCardClick = () => {
    onSelect(contract.id);
  };

  const handleApproveClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card selection when clicking approve button
    if (onApprove) {
      onApprove(contract.id);
    }
  };

  // Get status display text and color
  const getStatusConfig = () => {
    if (contract.status === 'completed') {
      return { text: '已完成', color: 'success' };
    }
    return { text: '进行中', color: 'processing' };
  };

  const statusConfig = getStatusConfig();

  // Generate avatar color based on initiator name
  const getAvatarColor = (name: string) => {
    const colors = ['#f56a00', '#7265e6', '#ffbf00', '#00a2ae', '#87d068'];
    const charCode = name.charCodeAt(0);
    return colors[charCode % colors.length];
  };

  const initiatorName = contract.initiator?.name || '未知用户';
  const avatarColor = getAvatarColor(initiatorName);

  return (
    <div
      className={`contract-card ${selected ? 'contract-card-selected' : ''}`}
      onClick={handleCardClick}
      data-testid="contract-card"
    >
      <div className="contract-card-header">
        <div className="contract-card-title">{(contract.contractNumber ? contract.contractNumber + ' ' : '') + contract.name}</div>
        <Tag color={statusConfig.color}>{statusConfig.text}</Tag>
      </div>

      <div className="contract-card-meta">
        <div className="contract-card-initiator">
          <Tooltip title={initiatorName}>
            <Avatar
              size="small"
              style={{ backgroundColor: avatarColor }}
              src={contract.initiator?.avatar}
              icon={!contract.initiator?.avatar && <UserOutlined />}
            >
              {!contract.initiator?.avatar && initiatorName.charAt(0)}
            </Avatar>
          </Tooltip>
          <span className="contract-card-initiator-name">{initiatorName}</span>
        </div>
        <span className="contract-card-date">
          {formatRelativeTime(contract.createdAt)}
        </span>
        {contract.hasPendingReview && onApprove && (
          <button className="contract-card-approve-btn" onClick={handleApproveClick}>
            <CheckOutlined /> 同意
          </button>
        )}
      </div>
    </div>
  );
});

ContractCard.displayName = 'ContractCard';

export default ContractCard;
