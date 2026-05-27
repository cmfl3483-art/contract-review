import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from '../utils/axios';
import { API_BASE_URL } from '../config/api';
import { useNotificationStore } from '../stores/useNotificationStore';
import type { ApiResponse, Notification, NotificationListResponse } from '../types';

// 后端 snake_case → 前端 camelCase 映射
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapNotificationFromApi(n: any): Notification {
  return {
    id: n.id,
    type: n.type,
    actorId: n.actor_id ?? n.actorId,
    actorName: n.actor_name ?? n.actorName,
    actor: n.actor,
    contractId: n.contract_id ?? n.contractId,
    contractName: n.contract_name ?? n.contractName,
    anchorId: n.anchor_id ?? n.anchorId,
    preview: n.preview,
    isRead: n.is_read ?? n.isRead ?? false,
    createdAt: n.created_at ?? n.createdAt,
  };
}

/**
 * 获取通知列表（分页）
 *
 * @param page - 页码，默认第 1 页
 */
export function useNotificationList(page: number = 1) {
  const setUnreadCount = useNotificationStore((s) => s.setUnreadCount);

  return useQuery({
    queryKey: ['notifications', 'list', page],
    queryFn: async () => {
      const response = await axios.get<ApiResponse<NotificationListResponse>>(
        `${API_BASE_URL}/api/notifications`,
        { params: { page, page_size: 20 } }
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '获取通知列表失败');
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const raw = response.data.data as any;
      const notifications: Notification[] = (raw?.notifications ?? []).map(mapNotificationFromApi);

      // 同步未读数（从响应中统计）
      const unreadCount = notifications.filter((n) => !n.isRead).length;
      setUnreadCount(unreadCount);

      return {
        notifications,
        total: raw?.total ?? 0,
        page: raw?.page ?? page,
        pageSize: raw?.page_size ?? raw?.pageSize ?? 20,
      } as NotificationListResponse;
    },
  });
}

/**
 * 获取未读通知数量
 * 每 30 秒轮询一次
 */
export function useUnreadCount() {
  const setUnreadCount = useNotificationStore((s) => s.setUnreadCount);

  return useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: async () => {
      const response = await axios.get<ApiResponse<{ count: number }>>(
        `${API_BASE_URL}/api/notifications/unread-count`
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '获取未读数失败');
      }

      const count = response.data.data?.count ?? 0;
      setUnreadCount(count);
      return count;
    },
    staleTime: 30 * 1000,
    refetchInterval: 30 * 1000,
  });
}

/**
 * 标记单条通知为已读
 */
export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  const markAsRead = useNotificationStore((s) => s.markAsRead);

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await axios.patch<ApiResponse<{ id: string; is_read: boolean }>>(
        `${API_BASE_URL}/api/notifications/${id}/read`
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '标记已读失败');
      }

      return id;
    },
    onSuccess: (id) => {
      markAsRead(id);
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'list'] });
    },
  });
}

/**
 * 全部标为已读
 */
export function useMarkAllRead() {
  const queryClient = useQueryClient();
  const markAllAsRead = useNotificationStore((s) => s.markAllAsRead);

  return useMutation({
    mutationFn: async () => {
      const response = await axios.post<ApiResponse<{ updated_count: number }>>(
        `${API_BASE_URL}/api/notifications/read-all`
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '全部标为已读失败');
      }

      return response.data.data;
    },
    onSuccess: () => {
      markAllAsRead();
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'list'] });
    },
  });
}
