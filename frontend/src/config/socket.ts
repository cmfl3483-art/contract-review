import { io, Socket } from 'socket.io-client';
import { message, notification } from 'antd';
import { API_BASE_URL } from './api';
import type {
  ContractUpdatedData,
  ReviewAddedData,
  CommentAddedData,
  ReplyAddedData,
  LikeUpdatedData,
  PendingChangedData,
  SocketEventCallback,
  UnsubscribeFunction,
} from '../types/socket';

/**
 * Socket.IO 客户端配置
 * Socket.IO Client Configuration
 *
 * 提供实时通信功能,支持以下事件:
 * - contract:updated - 合同信息更新
 * - review:added - 新增评审意见
 * - comment:added - 新增评论
 * - reply:added - 新增回复
 * - like:updated - 点赞更新
 * - pending:changed - 待办数量变化
 *
 * 增强的错误处理:
 * - 连接失败时显示用户友好的通知
 * - 自动重连机制
 * - 重连状态提示
 * - 连接质量监控
 */

// Socket.IO 客户端实例
let socket: Socket | null = null;

// 连接状态跟踪
let isReconnecting = false;
let reconnectNotificationKey: string | null = null;

/**
 * 获取 Socket.IO 客户端实例
 * 如果实例不存在,则创建新实例
 *
 * @param token - JWT 认证 token
 * @returns Socket.IO 客户端实例
 */
export const getSocket = (token?: string): Socket => {
  if (!socket) {
    // 生产环境 VITE_API_BASE_URL 为空字符串，直接用相对路径（当前域名）
    // 开发环境用 localhost:8000
    const socketUrl = API_BASE_URL || undefined;
    socket = io(socketUrl as string, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      autoConnect: false, // 手动控制连接
      reconnection: true, // 启用自动重连
      reconnectionAttempts: 5, // 最多重连5次
      reconnectionDelay: 1000, // 重连延迟1秒
      reconnectionDelayMax: 5000, // 最大重连延迟5秒
      timeout: 20000, // 连接超时20秒
      auth: token ? { token } : undefined,
    });

    // 连接成功事件
    socket.on('connect', () => {
      console.log('[Socket.IO] 连接成功', socket?.id);
      
      // 如果是重连成功,显示通知
      if (isReconnecting) {
        message.success('实时通信已恢复');
        isReconnecting = false;
        
        // 关闭重连通知
        if (reconnectNotificationKey) {
          notification.destroy(reconnectNotificationKey);
          reconnectNotificationKey = null;
        }
      }
    });

    // 连接错误事件
    socket.on('connect_error', (error) => {
      console.error('[Socket.IO] 连接错误:', error.message);
      
      // 首次连接失败时显示警告
      if (!isReconnecting) {
        notification.warning({
          message: '实时通信连接失败',
          description: '部分功能可能受影响,系统将自动尝试重新连接',
          duration: 4,
        });
        isReconnecting = true;
      }
    });

    // 断开连接事件
    socket.on('disconnect', (reason) => {
      console.log('[Socket.IO] 断开连接:', reason);

      // 根据断开原因显示不同的提示
      if (reason === 'io server disconnect') {
        // 服务器主动断开
        notification.warning({
          message: '实时通信已断开',
          description: '服务器主动断开了连接,正在尝试重新连接...',
          duration: 0,
          key: 'socket-disconnect',
        });
        reconnectNotificationKey = 'socket-disconnect';
        isReconnecting = true;
        
        // 尝试重连
        socket?.connect();
      } else if (reason === 'io client disconnect') {
        // 客户端主动断开,不显示通知
        console.log('[Socket.IO] 客户端主动断开连接');
      } else {
        // 其他原因断开
        if (!isReconnecting) {
          message.warning('实时通信连接中断,正在重连...');
          isReconnecting = true;
        }
      }
    });

    // 重连尝试事件
    socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`[Socket.IO] 尝试重连 (${attemptNumber}/5)`);
      
      // 显示持续的重连通知
      if (!reconnectNotificationKey) {
        reconnectNotificationKey = `reconnect-${Date.now()}`;
        notification.info({
          message: '正在重新连接',
          description: `正在尝试重新连接实时通信服务 (${attemptNumber}/5)...`,
          duration: 0,
          key: reconnectNotificationKey,
        });
      } else {
        // 更新现有通知
        notification.info({
          message: '正在重新连接',
          description: `正在尝试重新连接实时通信服务 (${attemptNumber}/5)...`,
          duration: 0,
          key: reconnectNotificationKey,
        });
      }
    });

    // 重连成功事件
    socket.on('reconnect', (attemptNumber) => {
      console.log(`[Socket.IO] 重连成功 (尝试次数: ${attemptNumber})`);
      
      notification.success({
        message: '重新连接成功',
        description: '实时通信已恢复,您可以继续正常使用',
        duration: 3,
      });
      
      isReconnecting = false;
      
      // 关闭重连通知
      if (reconnectNotificationKey) {
        notification.destroy(reconnectNotificationKey);
        reconnectNotificationKey = null;
      }
    });

    // 重连失败事件
    socket.on('reconnect_failed', () => {
      console.error('[Socket.IO] 重连失败,已达到最大重连次数');
      
      notification.error({
        message: '连接失败',
        description: '无法连接到实时通信服务,请刷新页面重试。部分功能可能无法正常使用。',
        duration: 0,
      });
      
      isReconnecting = false;
      
      // 关闭重连通知
      if (reconnectNotificationKey) {
        notification.destroy(reconnectNotificationKey);
        reconnectNotificationKey = null;
      }
    });

    // 服务器确认连接事件
    socket.on('connected', (data) => {
      console.log('[Socket.IO] 服务器确认连接:', data);
    });
  }

  return socket;
};

/**
 * 连接 Socket.IO 服务器
 *
 * @param token - JWT 认证 token
 */
export const connectSocket = (token: string): void => {
  const socketInstance = getSocket(token);

  // 更新认证信息
  if (socketInstance.auth) {
    (socketInstance.auth as { token: string }).token = token;
  }

  // 如果未连接,则连接
  if (!socketInstance.connected) {
    socketInstance.connect();
  }
};

/**
 * 断开 Socket.IO 连接
 */
export const disconnectSocket = (): void => {
  if (socket?.connected) {
    socket.disconnect();
  }
};

/**
 * 加入合同房间 (用于接收特定合同的实时更新)
 *
 * @param contractId - 合同 ID
 */
export const joinContractRoom = (contractId: string): void => {
  if (socket?.connected) {
    socket.emit('join_contract', { contract_id: contractId });
    console.log(`[Socket.IO] 加入合同房间: ${contractId}`);
  }
};

/**
 * 离开合同房间
 *
 * @param contractId - 合同 ID
 */
export const leaveContractRoom = (contractId: string): void => {
  if (socket?.connected) {
    socket.emit('leave_contract', { contract_id: contractId });
    console.log(`[Socket.IO] 离开合同房间: ${contractId}`);
  }
};

/**
 * 监听合同更新事件
 *
 * @param callback - 回调函数
 * @returns 取消监听的函数
 */
export const onContractUpdated = (
  callback: SocketEventCallback<ContractUpdatedData>
): UnsubscribeFunction => {
  const socketInstance = getSocket();
  socketInstance.on('contract:updated', callback);

  // 返回取消监听的函数
  return () => {
    socketInstance.off('contract:updated', callback);
  };
};

/**
 * 监听评审添加事件
 *
 * @param callback - 回调函数
 * @returns 取消监听的函数
 */
export const onReviewAdded = (
  callback: SocketEventCallback<ReviewAddedData>
): UnsubscribeFunction => {
  const socketInstance = getSocket();
  socketInstance.on('review:added', callback);

  return () => {
    socketInstance.off('review:added', callback);
  };
};

/**
 * 监听评论添加事件
 *
 * @param callback - 回调函数
 * @returns 取消监听的函数
 */
export const onCommentAdded = (
  callback: SocketEventCallback<CommentAddedData>
): UnsubscribeFunction => {
  const socketInstance = getSocket();
  socketInstance.on('comment:added', callback);

  return () => {
    socketInstance.off('comment:added', callback);
  };
};

/**
 * 监听回复添加事件
 *
 * @param callback - 回调函数
 * @returns 取消监听的函数
 */
export const onReplyAdded = (
  callback: SocketEventCallback<ReplyAddedData>
): UnsubscribeFunction => {
  const socketInstance = getSocket();
  socketInstance.on('reply:added', callback);

  return () => {
    socketInstance.off('reply:added', callback);
  };
};

/**
 * 监听点赞更新事件
 *
 * @param callback - 回调函数
 * @returns 取消监听的函数
 */
export const onLikeUpdated = (
  callback: SocketEventCallback<LikeUpdatedData>
): UnsubscribeFunction => {
  const socketInstance = getSocket();
  socketInstance.on('like:updated', callback);

  return () => {
    socketInstance.off('like:updated', callback);
  };
};

/**
 * 监听待办数量变化事件
 *
 * @param callback - 回调函数
 * @returns 取消监听的函数
 */
export const onPendingChanged = (
  callback: SocketEventCallback<PendingChangedData>
): UnsubscribeFunction => {
  const socketInstance = getSocket();
  socketInstance.on('pending:changed', callback);

  return () => {
    socketInstance.off('pending:changed', callback);
  };
};

/**
 * 监听新通知事件
 *
 * @param callback - 回调函数
 * @returns 取消监听的函数
 */
export const onNotificationNew = (
  callback: SocketEventCallback<any>
): UnsubscribeFunction => {
  const socketInstance = getSocket();
  socketInstance.on('notification:new', callback);
  return () => {
    socketInstance.off('notification:new', callback);
  };
};

/**
 * 监听合同被发起人修改重审事件
 *
 * @param callback - 回调函数，接收 { contractId, contractName, changedFields }
 * @returns 取消监听的函数
 */
export const onContractRevised = (
  callback: SocketEventCallback<{
    contractId: string;
    contractName: string;
    changedFields: string[];
  }>
): UnsubscribeFunction => {
  const socketInstance = getSocket();
  socketInstance.on('contract:revised', callback);
  return () => {
    socketInstance.off('contract:revised', callback);
  };
};

/**
 * 移除所有事件监听器
 */
export const removeAllListeners = (): void => {
  if (socket) {
    socket.removeAllListeners();
  }
};

/**
 * 获取当前连接状态
 *
 * @returns 是否已连接
 */
export const isConnected = (): boolean => {
  return socket?.connected ?? false;
};
