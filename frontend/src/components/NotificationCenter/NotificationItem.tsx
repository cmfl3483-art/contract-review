import React from 'react';
import { message } from 'antd';
import type { Notification, NotificationType } from '../../types';
import { useMarkNotificationRead } from '../../hooks/useNotifications';
import { useSelectedContractStore } from '../../stores/useSelectedContractStore';
import { useFocusedAnchorStore } from '../../stores/useFocusedAnchorStore';

interface NotificationItemProps {
  notification: Notification;
}

const TYPE_ICONS: Record<NotificationType, string> = {
  review_approved: '✅',
  comment_added: '💬',
  comment_replied: '↩️',
  user_mentioned: '@',
  contract_revised: '📝',
};

function formatRelativeTime(createdAt: string): string {
  const now = Date.now();
  const created = new Date(createdAt).getTime();
  const diffMs = now - created;
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);

  if (diffSeconds < 60) {
    return '刚刚';
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`;
  } else if (diffHours < 24) {
    return `${diffHours}小时前`;
  } else {
    const date = new Date(createdAt);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    return `${month}月${day}日`;
  }
}

/**
 * 在 DOM 中重试查找锚点元素，最多重试 N 次。
 * 因为锚点所在的折叠区域可能需要在 store 更新后才展开。
 */
function findAnchorWithRetry(
  anchorId: string,
  maxAttempts: number = 10,
  intervalMs: number = 100
): Promise<HTMLElement | null> {
  return new Promise((resolve) => {
    let attempts = 0;
    const tick = () => {
      const el = document.getElementById(`anchor-${anchorId}`);
      if (el) {
        resolve(el);
        return;
      }
      attempts++;
      if (attempts >= maxAttempts) {
        resolve(null);
        return;
      }
      setTimeout(tick, intervalMs);
    };
    tick();
  });
}

const NotificationItem: React.FC<NotificationItemProps> = ({ notification }) => {
  const { mutate: markRead } = useMarkNotificationRead();
  const setSelectedContractId = useSelectedContractStore((s) => s.setSelectedContractId);
  const setAnchorId = useFocusedAnchorStore((s) => s.setAnchorId);

  const handleClick = async () => {
    // 1. 标记已读
    markRead(notification.id);

    // 2. 切换合同
    setSelectedContractId(notification.contractId);

    // 3. 如果没有 anchorId（如 contract_revised 通知），仅切换合同后即可
    if (!notification.anchorId) {
      return;
    }

    // 4. 设置聚焦锚点（让 ReplyList 等组件自动展开折叠区域）
    setAnchorId(notification.anchorId);

    // 5. 等待初始渲染（200ms）
    await new Promise((r) => setTimeout(r, 200));

    // 6. 重试查找锚点（最多 10 次 × 100ms = 1秒），处理折叠展开延迟
    const el = await findAnchorWithRetry(notification.anchorId);

    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('highlight-flash');
      setTimeout(() => el.classList.remove('highlight-flash'), 3000);
    } else {
      message.info('该内容已被删除');
    }

    // 7. 清除聚焦锚点（避免影响后续操作）
    setTimeout(() => setAnchorId(null), 4000);
  };

  const icon = TYPE_ICONS[notification.type] ?? '🔔';
  const actorName = notification.actorName ?? notification.actor?.name ?? '未知用户';
  const contractName = notification.contractName ?? '';
  const relativeTime = formatRelativeTime(notification.createdAt);

  return (
    <div
      onClick={handleClick}
      style={{
        padding: '12px 16px',
        cursor: 'pointer',
        backgroundColor: notification.isRead ? '#ffffff' : '#f0f7ff',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        gap: 10,
        alignItems: 'flex-start',
      }}
    >
      <span style={{ fontSize: 18, flexShrink: 0, lineHeight: '22px' }}>{icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, color: '#333', marginBottom: 2 }}>
          <span style={{ fontWeight: 500 }}>{actorName}</span>
          {contractName && (
            <span style={{ color: '#666', marginLeft: 4 }}>· {contractName}</span>
          )}
        </div>
        {notification.preview && (
          <div
            style={{
              fontSize: 12,
              color: '#666',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {notification.preview}
          </div>
        )}
        <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>{relativeTime}</div>
      </div>
    </div>
  );
};

export default NotificationItem;
