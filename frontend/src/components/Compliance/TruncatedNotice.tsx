import React from 'react';
import { Alert } from 'antd';

interface TruncatedNoticeProps {
  show: boolean;
}

const TruncatedNotice: React.FC<TruncatedNoticeProps> = ({ show }) => {
  if (!show) return null;

  return (
    <Alert
      type="warning"
      showIcon
      message="文件过长已截断，可能影响检查准确性"
      style={{ marginBottom: 16 }}
    />
  );
};

export default TruncatedNotice;
