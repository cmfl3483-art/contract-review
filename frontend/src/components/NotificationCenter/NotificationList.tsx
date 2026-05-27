import React, { useState } from 'react';
import { Drawer, Button, Pagination, Empty, Spin } from 'antd';
import { useNotificationList, useMarkAllRead } from '../../hooks/useNotifications';
import NotificationItem from './NotificationItem';

interface NotificationListProps {
  open: boolean;
  onClose: () => void;
}

const NotificationList: React.FC<NotificationListProps> = ({ open, onClose }) => {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useNotificationList(page);
  const { mutate: markAllRead, isPending: isMarkingAll } = useMarkAllRead();

  const notifications = data?.notifications ?? [];
  const total = data?.total ?? 0;

  return (
    <Drawer
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>消息通知</span>
          <Button
            type="link"
            size="small"
            loading={isMarkingAll}
            onClick={() => markAllRead()}
            style={{ padding: 0 }}
          >
            全部已读
          </Button>
        </div>
      }
      placement="right"
      width={360}
      open={open}
      onClose={onClose}
      styles={{ body: { padding: 0 } }}
    >
      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <Spin />
        </div>
      ) : notifications.length === 0 ? (
        <div style={{ padding: 40 }}>
          <Empty description="暂无通知" />
        </div>
      ) : (
        <>
          <div>
            {notifications.map((n) => (
              <NotificationItem key={n.id} notification={n} />
            ))}
          </div>
          {total > 20 && (
            <div style={{ padding: '12px 16px', textAlign: 'center' }}>
              <Pagination
                current={page}
                total={total}
                pageSize={20}
                size="small"
                onChange={(p) => setPage(p)}
                showSizeChanger={false}
              />
            </div>
          )}
        </>
      )}
    </Drawer>
  );
};

export default NotificationList;
