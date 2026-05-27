import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import {
  connectSocket,
  disconnectSocket,
  joinContractRoom,
  leaveContractRoom,
  onContractUpdated,
  onContractRevised,
  onReviewAdded,
  onCommentAdded,
  onReplyAdded,
  onLikeUpdated,
  onPendingChanged,
  onNotificationNew,
  isConnected,
} from '../config/socket';
import { queryKeys } from '../config/queryClient';
import { useUserStore } from '../stores/useUserStore';
import { useNotificationStore } from '../stores/useNotificationStore';
import type { Notification } from '../types';

/**
 * Socket.IO 连接管理 Hook
 * 自动管理 Socket.IO 连接的生命周期
 * 当用户登录时自动连接,登出时自动断开
 */
export const useSocket = () => {
  const token = useUserStore((state) => state.token);
  const queryClient = useQueryClient();

  useEffect(() => {
    // 如果有 token,则连接 Socket.IO
    if (token) {
      connectSocket(token);

      return () => {
        // 组件卸载时断开连接
        disconnectSocket();
      };
    }
  }, [token]);

  return {
    isConnected: isConnected(),
  };
};

/**
 * 合同房间管理 Hook
 * 自动加入和离开合同房间
 *
 * @param contractId - 合同 ID (可选)
 */
export const useContractRoom = (contractId?: string) => {
  useEffect(() => {
    if (contractId) {
      // 加入合同房间
      joinContractRoom(contractId);

      return () => {
        // 离开合同房间
        leaveContractRoom(contractId);
      };
    }
  }, [contractId]);
};

/**
 * Socket.IO 事件监听 Hook
 * 监听所有 Socket.IO 事件并自动刷新 React Query 缓存
 */
export const useSocketEvents = () => {
  const queryClient = useQueryClient();

  useEffect(() => {
    // 监听合同更新事件
    const unsubscribeContractUpdated = onContractUpdated((data) => {
      console.log('[Socket.IO Event] contract:updated', data);

      // 刷新合同列表缓存
      queryClient.invalidateQueries({ queryKey: queryKeys.contracts.lists() });

      // 刷新特定合同详情缓存
      if (data.contract_id) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.contracts.detail(data.contract_id),
        });
      }
    });

    // 监听评审添加事件
    const unsubscribeReviewAdded = onReviewAdded((data) => {
      console.log('[Socket.IO Event] review:added', data);

      // 刷新评审记录缓存
      if (data.contract_id) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.reviews.list(data.contract_id),
        });

        // 刷新合同详情缓存 (评审人状态可能变化)
        queryClient.invalidateQueries({
          queryKey: queryKeys.contracts.detail(data.contract_id),
        });

        // 刷新合同列表缓存 (状态可能变化)
        queryClient.invalidateQueries({ queryKey: queryKeys.contracts.lists() });
      }
    });

    // 监听评论添加事件
    const unsubscribeCommentAdded = onCommentAdded((data) => {
      console.log('[Socket.IO Event] comment:added', data);

      // 刷新评审记录缓存
      if (data.contract_id) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.reviews.list(data.contract_id),
        });
      }
    });

    // 监听回复添加事件
    const unsubscribeReplyAdded = onReplyAdded((data) => {
      console.log('[Socket.IO Event] reply:added', data);

      // 刷新评审记录缓存
      if (data.contract_id) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.reviews.list(data.contract_id),
        });
      }
    });

    // 监听点赞更新事件
    const unsubscribeLikeUpdated = onLikeUpdated((data) => {
      console.log('[Socket.IO Event] like:updated', data);

      // 刷新评审记录缓存
      if (data.contract_id) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.reviews.list(data.contract_id),
        });
      }
    });

    // 监听待办数量变化事件
    const unsubscribePendingChanged = onPendingChanged((data) => {
      console.log('[Socket.IO Event] pending:changed', data);

      // 刷新待办数量缓存
      queryClient.invalidateQueries({ queryKey: queryKeys.pending.count() });

      // 刷新合同列表缓存 (待办徽章需要更新)
      queryClient.invalidateQueries({ queryKey: queryKeys.contracts.lists() });
    });

    // 监听新通知事件
    const notificationStore = useNotificationStore.getState();
    const unsubscribeNotificationNew = onNotificationNew((data: Notification) => {
      console.log('[Socket.IO Event] notification:new', data);
      notificationStore.addNotification(data);
    });

    // 监听合同被发起人修改重审事件
    const unsubscribeContractRevised = onContractRevised((data) => {
      console.log('[Socket.IO Event] contract:revised', data);

      // 刷新合同详情、评审记录、合同列表、待办数量缓存
      queryClient.invalidateQueries({
        queryKey: queryKeys.contracts.detail(data.contractId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.reviews.list(data.contractId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.contracts.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.pending.count() });

      // 提示用户
      message.warning(
        `合同「${data.contractName}」已被发起人修改（${data.changedFields.join('、')}），请重新审批`
      );
    });

    // 清理函数:取消所有事件监听
    return () => {
      unsubscribeContractUpdated();
      unsubscribeReviewAdded();
      unsubscribeCommentAdded();
      unsubscribeReplyAdded();
      unsubscribeLikeUpdated();
      unsubscribePendingChanged();
      unsubscribeNotificationNew();
      unsubscribeContractRevised();
    };
  }, [queryClient]);
};

/**
 * 完整的 Socket.IO 集成 Hook
 * 结合连接管理、房间管理和事件监听
 *
 * @param contractId - 当前选中的合同 ID (可选)
 */
export const useSocketIntegration = (contractId?: string) => {
  // 管理 Socket.IO 连接
  const { isConnected: connected } = useSocket();

  // 管理合同房间
  useContractRoom(contractId);

  // 监听所有事件
  useSocketEvents();

  return {
    isConnected: connected,
  };
};

/**
 * 自定义事件监听 Hook
 * 用于监听特定的 Socket.IO 事件
 *
 * @param event - 事件名称
 * @param callback - 回调函数
 */
export const useSocketEvent = (event: string, callback: (data: any) => void) => {
  useEffect(() => {
    // 这里可以扩展支持自定义事件
    // 目前主要事件已通过 useSocketEvents 处理
    console.log(`[Socket.IO] 监听自定义事件: ${event}`);
  }, [event, callback]);
};
