import React, { useState } from 'react';
import NotificationBell from './NotificationBell';
import NotificationList from './NotificationList';
import { useUnreadCount } from '../../hooks/useNotifications';
import './NotificationCenter.css';

const NotificationCenter: React.FC = () => {
  const [open, setOpen] = useState(false);
  useUnreadCount(); // 初始化未读数

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <NotificationBell onClick={() => setOpen(!open)} />
      <NotificationList open={open} onClose={() => setOpen(false)} />
    </div>
  );
};

export default NotificationCenter;
