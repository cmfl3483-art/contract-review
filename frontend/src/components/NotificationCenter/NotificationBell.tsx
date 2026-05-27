import React from 'react';
import { Badge } from 'antd';
import { BellOutlined } from '@ant-design/icons';
import { useNotificationStore } from '../../stores/useNotificationStore';

interface NotificationBellProps {
  onClick: () => void;
}

const NotificationBell: React.FC<NotificationBellProps> = ({ onClick }) => {
  const unreadCount = useNotificationStore((s) => s.unreadCount);

  return (
    <Badge count={unreadCount} showZero={false}>
      <BellOutlined
        style={{ fontSize: 20, cursor: 'pointer' }}
        onClick={onClick}
      />
    </Badge>
  );
};

export default NotificationBell;
